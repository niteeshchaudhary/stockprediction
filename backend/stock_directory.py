"""Resolve the shared stock catalogue and explicitly entered provider tickers."""

import json
import re
from pathlib import Path

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "shared" / "nse-stocks.json"
CATALOGUE = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
EXCHANGE_CATALOGUE = json.loads(CATALOGUE_PATH.with_name('indian-stocks.json').read_text(encoding='utf-8'))
NSE_SYMBOLS = {stock["symbol"]: stock["symbol"] + ".NS" for stock in CATALOGUE["stocks"]}
NSE_SYMBOLS.update({stock['symbol']: stock['ticker'] for stock in EXCHANGE_CATALOGUE['stocks'] if stock['market'] == 'NSE'})
BSE_CODES = {stock['scripCode']: stock['ticker'] for stock in EXCHANGE_CATALOGUE['stocks'] if stock['market'] == 'BSE'}
NSE_NAMES = {stock["name"].lower(): stock["symbol"] + ".NS" for stock in CATALOGUE["stocks"]}
ALIASES = {
    "canabank": "CANBK.NS", "canara bank": "CANBK.NS",
    "irfc": "IRFC.NS", "iob": "IOB.NS", "indian overseas bank": "IOB.NS",
    "bajaj housing finance": "BAJAJHFL.NS", "bajaj housing finace": "BAJAJHFL.NS",
}
TICKER_PATTERN = re.compile(r"(?:[A-Z0-9][A-Z0-9&.-]{0,29}\.(?:NS|BO)|[A-Z0-9][A-Z0-9&-]{0,29})\Z")


def resolve_directory_ticker(value):
    value = value.strip()
    if value.lower().startswith("ticker:"):
        ticker = value[7:].upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            return None
        return BSE_CODES.get(ticker.removesuffix('.BO'), ticker) if ticker.endswith('.BO') else ticker
    upper = value.upper()
    if upper.endswith(('.NS', '.BO')):
        if not TICKER_PATTERN.fullmatch(upper):
            return None
        return BSE_CODES.get(upper[:-3], upper) if upper.endswith('.BO') else upper
    if upper in BSE_CODES:
        return BSE_CODES[upper]
    return ALIASES.get(value.lower()) or NSE_SYMBOLS.get(upper) or NSE_NAMES.get(value.lower())
