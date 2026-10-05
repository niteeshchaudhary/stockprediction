import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import market_data as data
import server


def history():
    return pd.DataFrame({
        "Date": ["2026-01-02", "2026-01-05"],
        "Open": [100, 101], "High": [102, 103], "Low": [99, 100],
        "Close": [101, 102], "Volume": [10, 20],
    })


class MarketDataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        cache_patch = patch.object(data, "CACHE_DIR", Path(self.directory.name) / "csvfiles")
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        env_patch = patch.dict(os.environ, {"TWELVE_DATA_API_KEY": ""})
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def test_normalization_sorts_removes_invalid_rows_and_preserves_numeric_columns(self):
        frame = history().iloc[::-1].copy()
        frame.loc[2] = ["invalid", 1, 1, 1, 1, 1]
        frame.loc[3] = ["2026-01-06", 1, 1, 1, float("inf"), 1]
        normalized = data.normalize_history(frame)
        self.assertEqual(normalized.Date.tolist(), ["2026-01-02", "2026-01-05"])
        self.assertEqual(normalized.Close.tolist(), [101, 102])
        self.assertEqual(normalized["Adj Close"].tolist(), [101, 102])
        self.assertEqual(normalized.index.tolist(), [0, 1])

    def test_cache_created_and_reused(self):
        with patch.object(data, "_yahoo_history", return_value=history()) as fetch:
            first = data.get_history("AAPL", "2026-01-01", "2026-01-07")
            second = data.get_history("AAPL", "2026-01-01", "2026-01-07")
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(first.Close.tolist(), second.Close.tolist())
        self.assertEqual(len(list(data.CACHE_DIR.glob("*.csv"))), 1)

    def test_empty_result_is_not_cached(self):
        with patch.object(data, "_yahoo_history", return_value=history().iloc[:0]):
            with self.assertRaises(data.MarketDataError):
                data.get_history("AAPL", "2026-01-01", "2026-01-07")
        self.assertEqual(list(data.CACHE_DIR.glob("*.csv")), [])

    def test_corrupt_cache_refetched(self):
        data.CACHE_DIR.mkdir()
        cache = data.CACHE_DIR / "v2-AAPL-2026-01-01-2026-01-07-yahoo.csv"
        cache.write_text("bad,columns\n1,2\n")
        with patch.object(data, "_yahoo_history", return_value=history()) as fetch:
            frame = data.get_history("AAPL", "2026-01-01", "2026-01-07")
        self.assertEqual(len(frame), 2)
        fetch.assert_called_once()

    def test_expired_cache_refetched(self):
        with patch.object(data, "_yahoo_history", return_value=history()) as fetch:
            data.get_history("AAPL", "2026-01-01", "2026-01-07")
            cache = next(data.CACHE_DIR.glob("*.csv"))
            os.utime(cache, (0, 0))
            data.get_history("AAPL", "2026-01-01", "2026-01-07")
        self.assertEqual(fetch.call_count, 2)

    def test_independent_provider_falls_back_to_yahoo(self):
        with patch.dict(os.environ, {"TWELVE_DATA_API_KEY": "test-key"}), \
             patch.object(data, "_twelve_history", side_effect=data.MarketDataError("Unavailable")), \
             patch.object(data, "_yahoo_history", return_value=history()) as fetch:
            self.assertEqual(len(data.get_history("AAPL", "2026-01-01", "2026-01-07")), 2)
        fetch.assert_called_once()

    def test_yahoo_host_failover(self):
        with patch.object(data, "_request_json", side_effect=[
            data.MarketDataError("rate limited"), {"chart": {"result": [{"meta": {}}]}},
        ]) as fetch:
            self.assertEqual(data._yahoo_chart("AAPL", {}), {"meta": {}})
        self.assertIn("query2.finance.yahoo.com", fetch.call_args.args[0])

    def test_yahoo_exchange_date_and_missing_candle(self):
        timestamps = [int(pd.Timestamp(day, tz="Asia/Kolkata").timestamp())
                      for day in ["2026-01-02", "2026-01-05"]]
        result = {"meta": {"exchangeTimezoneName": "Asia/Kolkata"}, "timestamp": timestamps,
                  "indicators": {"quote": [{"open": [100, None], "high": [102, None],
                                             "low": [99, None], "close": [101, None]}]}}
        with patch.object(data, "_yahoo_chart", return_value=result):
            frame = data._yahoo_history("RELIANCE.NS", "2026-01-01", "2026-01-07")
        self.assertEqual(frame.Date.tolist(), ["2026-01-02"])

    def test_quote_change_uses_previous_day_not_start_of_range(self):
        timestamps = [int(pd.Timestamp(day, tz="UTC").timestamp())
                      for day in ["2026-01-02", "2026-01-05", "2026-01-06"]]
        chart = {"meta": {"regularMarketPrice": 110, "regularMarketTime": timestamps[-1],
                          "exchangeTimezoneName": "UTC", "chartPreviousClose": 80},
                 "timestamp": timestamps, "indicators": {"quote": [{"close": [90, 100, 110]}]}}
        with patch.object(data, "_yahoo_chart", return_value=chart):
            self.assertEqual(data.get_quote("AAPL"), ["110.00", "+10.00", "(+10.00%)"])

    def test_twelve_data_exchange_and_date_range(self):
        with patch.dict(os.environ, {"TWELVE_DATA_API_KEY": "test-key"}), \
             patch.object(data, "_request_json", return_value={"values": [
                 {"datetime": "2026-01-02", "open": "100", "high": "102", "low": "99", "close": "101"}
             ]}) as fetch:
            frame = data._twelve_history("RELIANCE.NS", "2026-01-01", "2026-01-07")
        params = fetch.call_args.args[1]
        self.assertEqual(params["exchange"], "NSE")
        self.assertEqual(params["symbol"], "RELIANCE")
        self.assertEqual(params["end_date"], "2026-01-07")
        self.assertEqual(frame.Close.tolist(), [101])


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_data_routes_work_without_loading_prediction_models(self):
        with patch.object(server, "get_history", return_value=data.normalize_history(history())):
            response = self.client.get("/data/reliance", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["Date"], "2026-01-02")
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:3000")
        self.assertNotIn("news_analysis", sys.modules)
        self.assertNotIn("lstmprediction", sys.modules)

    def test_provider_failure_returns_json_503(self):
        for endpoint, fetch in [("/data/apple", "get_history"), ("/data/current/apple", "get_quote")]:
            with self.subTest(endpoint=endpoint), patch.object(server, fetch, side_effect=data.MarketDataError("Unavailable")):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json, {"error": "Unavailable"})

    def test_unknown_companies_return_404(self):
        for endpoint in ["/data/unknown", "/data/current/unknown", "/data/predict/unknown"]:
            self.assertEqual(self.client.get(endpoint).status_code, 404)

    def test_expanded_stocks_and_custom_ticker_routes(self):
        for company, ticker in [('IRFC.NS', 'IRFC.NS'), ('CANBK.NS', 'CANBK.NS'),
                                ('BAJAJHFL.NS', 'BAJAJHFL.NS'), ('IOB.NS', 'IOB.NS'),
                                ('tata steel', 'TATASTEEL.NS'), ('ticker:NVDA', 'NVDA')]:
            with self.subTest(company=company), patch.object(server, 'get_quote', return_value=['100', '+1', '(+1%)']) as fetch:
                self.assertEqual(self.client.get('/data/current/' + company).status_code, 200)
                fetch.assert_called_once_with(ticker)

    def test_short_history_cannot_reach_prediction_models(self):
        with patch.object(server, "get_history", return_value=history()):
            response = self.client.get("/data/predict/apple")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
