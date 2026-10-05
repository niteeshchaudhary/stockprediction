"""Next-session forecasts using installed data dependencies; optional TensorFlow LSTM."""

import logging
import os

import numpy as np

from market_data import normalize_history

logger = logging.getLogger(__name__)


def statistical_forecast(closes):
    # Ridge autoregression on recent daily log returns. Fit each observation once.
    returns = np.diff(np.log(closes[-253:]))
    lag = 5
    x = np.array([returns[i - lag:i] for i in range(lag, len(returns))])
    y = returns[lag:]
    design = np.column_stack([np.ones(len(x)), x])
    penalty = np.eye(lag + 1) * 0.01
    penalty[0, 0] = 0
    weights = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    next_return = float(np.r_[1, returns[-lag:]] @ weights)
    return float(closes[-1] * np.exp(next_return))


def generate_forecast(frame):
    frame = normalize_history(frame)
    if len(frame) < 65:
        raise ValueError('At least 65 trading days are required for prediction.')
    closes = frame.Close.to_numpy(dtype=float)
    statistical = statistical_forecast(closes)
    if not np.isfinite(statistical) or statistical <= 0:
        raise ValueError('Statistical model returned an invalid price.')
    lstm = None
    warnings = []
    if os.getenv('ENABLE_LSTM', '').lower() in {'1', 'true', 'yes'}:
        try:
            from lstmprediction import getPrediction
            lstm = float(np.asarray(getPrediction(frame)).reshape(-1)[0])
            if not np.isfinite(lstm) or lstm <= 0:
                raise ValueError('LSTM returned an invalid price.')
        except Exception:
            logger.exception('Optional LSTM failed; retaining statistical forecast')
            lstm = None
            warnings.append('LSTM unavailable; the statistical forecast is still available.')
    else:
        warnings.append('LSTM is disabled. Enable it on the backend with TensorFlow installed.')
    return {'pvalue': statistical, 'pvaluelstm': lstm,
            'models': {'statistical': 'Ridge autoregression', 'lstm': 'LSTM' if lstm is not None else None},
            'horizon': 'Next trading session', 'as_of': frame.Date.iloc[-1], 'warnings': warnings}
