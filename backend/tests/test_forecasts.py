import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import forecast_service
import server


def candles(closes):
    return pd.DataFrame({'Date': pd.date_range('2025-01-01', periods=len(closes)),
                         'Open': closes, 'High': closes, 'Low': closes, 'Close': closes})


class ForecastTests(unittest.TestCase):
    def test_constant_price_remains_constant(self):
        with patch.dict(os.environ, {'ENABLE_LSTM': 'false'}):
            result = forecast_service.generate_forecast(candles(np.full(100, 123.0)))
        self.assertAlmostEqual(result['pvalue'], 123.0)
        self.assertIsNone(result['pvaluelstm'])
        self.assertEqual(result['models']['statistical'], 'Ridge autoregression')

    def test_forecasts_next_session_for_constant_log_return(self):
        closes = 100 * np.exp(np.arange(100) * .001)
        with patch.dict(os.environ, {'ENABLE_LSTM': 'false'}):
            result = forecast_service.generate_forecast(candles(closes))
        self.assertAlmostEqual(result['pvalue'], closes[-1] * np.exp(.001), places=6)
        self.assertEqual(result['as_of'], '2025-04-10')

    def test_short_history_rejected(self):
        with self.assertRaisesRegex(ValueError, '65 trading days'):
            forecast_service.generate_forecast(candles(np.full(64, 100)))

    def test_optional_lstm_failure_does_not_block_statistical(self):
        with patch.dict(os.environ, {'ENABLE_LSTM': 'true'}), patch.dict(sys.modules, {'lstmprediction': SimpleNamespace(getPrediction=Mock(side_effect=ImportError('No TensorFlow')))}):
            with self.assertLogs('forecast_service', 'ERROR'):
                result = forecast_service.generate_forecast(candles(np.full(100, 100)))
        self.assertEqual(result['pvalue'], 100)
        self.assertIsNone(result['pvaluelstm'])
        self.assertIn('unavailable', result['warnings'][0])

    def test_prediction_endpoint_logs_and_returns_real_forecast_without_optional_dependencies(self):
        with patch.dict(os.environ, {'ENABLE_LSTM': 'false'}), patch.object(server, 'get_history', return_value=candles(np.full(100, 100))):
            with self.assertLogs(server.app.logger, 'INFO') as logs:
                response = server.app.test_client().get('/data/predict/IRFC.NS')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['pvalue'], 100)
        self.assertTrue(response.headers.get('X-Request-ID'))
        self.assertIn('prediction completed', '\n'.join(logs.output))

    def test_model_error_returns_traceable_error_and_logs_traceback(self):
        with patch.object(server, 'get_history', return_value=candles(np.full(100, 100))), patch.object(server, 'generate_forecast', side_effect=RuntimeError('broken model')):
            with self.assertLogs(server.app.logger, 'ERROR') as logs:
                response = server.app.test_client().get('/data/predict/apple')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['request_id'], response.headers['X-Request-ID'])
        self.assertIn('broken model', '\n'.join(logs.output))

    def test_provider_error_is_logged_before_prediction(self):
        with patch.object(server, 'get_history', side_effect=server.MarketDataError('Provider offline')):
            with self.assertLogs(server.app.logger, 'WARNING') as logs:
                response = server.app.test_client().get('/data/predict/apple')
        self.assertEqual(response.status_code, 503)
        self.assertIn('Provider offline', '\n'.join(logs.output))
