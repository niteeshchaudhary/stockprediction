"""Resolve the shared stock catalogue and explicitly entered provider tickers."""

import json
import re
from pathlib import Path

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "shared" / "nse-stocks.json"
CATALOGUE = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
NSE_SYMBOLS = {stock["symbol"]: stock["symbol"] + ".NS" for stock in CATALOGUE["stocks"]}
NSE_NAMES = {stock["name"].lower(): stock["symbol"] + ".NS" for stock in CATALOGUE["stocks"]}
ALIASES = {
    "canabank": "CANBK.NS", "canara bank": "CANBK.NS",
    "irfc": "IRFC.NS", "iob": "IOB.NS", "indian overseas bank": "IOB.NS",
    "bajaj housing finance": "BAJAJHFL.NS", "bajaj housing finace": "BAJAJHFL.NS",
}
TICKER_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9&-]{0,29}(?:\.(?:NS|BO))?\Z")


def resolve_directory_ticker(value):
    value = value.strip()
    if value.lower().startswith("ticker:"):
        ticker = value[7:].upper()
        return ticker if TICKER_PATTERN.fullmatch(ticker) else None
    upper = value.upper()
    if upper.endswith(".NS"):
        return NSE_SYMBOLS.get(upper[:-3])
    return ALIASES.get(value.lower()) or NSE_SYMBOLS.get(upper) or NSE_NAMES.get(value.lower())
