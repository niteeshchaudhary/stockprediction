import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stock_directory import CATALOGUE, resolve_directory_ticker


class StockDirectoryTests(unittest.TestCase):
    def test_catalogue_and_requested_stocks(self):
        self.assertGreater(len(CATALOGUE['stocks']), 2600)
        for value, ticker in [('IRFC', 'IRFC.NS'), ('TATASTEEL', 'TATASTEEL.NS'),
                              ('CANABANK', 'CANBK.NS'), ('Canara Bank', 'CANBK.NS'),
                              ('Bajaj housing finace', 'BAJAJHFL.NS'), ('IOB', 'IOB.NS')]:
            with self.subTest(value=value):
                self.assertEqual(resolve_directory_ticker(value), ticker)

    def test_custom_tickers_require_explicit_prefix(self):
        for ticker in ['NVDA', '500325.BO', 'IRFC.NS']:
            self.assertEqual(resolve_directory_ticker('ticker:' + ticker), ticker)
        for value in ['unknown', 'ticker:../secret', 'ticker:a/b', 'ticker:BAD.L', 'ticker:']:
            self.assertIsNone(resolve_directory_ticker(value))


if __name__ == '__main__':
    unittest.main()
