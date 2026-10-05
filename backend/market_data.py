"""Stock data adapters, with one stable schema for charts and prediction models."""

import json
import logging
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import pandas as pd

logger = logging.getLogger(__name__)
CACHE_DIR = Path(__file__).resolve().parent / "csvfiles"
CACHE_TTL = 900
_cache_lock = threading.Lock()
PRICE_COLUMNS = ["Open", "High", "Low", "Close"]


class MarketDataError(Exception):
    pass


def _request_json(url, params):
    request = Request(url + "?" + urlencode(params), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise MarketDataError("Provider returned an invalid response")
        return payload
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        # Do not expose request URLs, which may contain an API key.
        raise MarketDataError("Market data request failed") from exc


def normalize_history(frame):
    frame = frame.copy()
    if frame.empty or not set(["Date"] + PRICE_COLUMNS).issubset(frame.columns):
        raise MarketDataError("Provider returned no usable stock history")
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    for column in PRICE_COLUMNS + ["Adj Close", "Volume"]:
        if column not in frame:
            frame[column] = frame["Close"] if column == "Adj Close" else 0
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.replace([float("inf"), float("-inf")], float("nan"))
    frame = frame.dropna(subset=["Date"] + PRICE_COLUMNS)
    frame = frame[frame["Close"] > 0].sort_values("Date").drop_duplicates("Date", keep="last")
    if frame.empty:
        raise MarketDataError("Provider returned no usable stock history")
    frame["Adj Close"] = frame["Adj Close"].fillna(frame["Close"])
    frame["Volume"] = frame["Volume"].fillna(0)
    frame["Date"] = frame["Date"].dt.strftime("%Y-%m-%d")
    return frame[["Date"] + PRICE_COLUMNS + ["Adj Close", "Volume"]].reset_index(drop=True)


def _yahoo_chart(ticker, params):
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            payload = _request_json(
                f"https://{host}/v8/finance/chart/{quote(ticker, safe='')}", params
            )
            chart = payload.get("chart", {})
            if not isinstance(chart, dict) or chart.get("error") or not chart.get("result"):
                raise MarketDataError("Yahoo returned no data for this ticker")
            result = chart["result"][0]
            if not isinstance(result, dict):
                raise MarketDataError("Yahoo returned an invalid chart")
            return result
        except MarketDataError:
            continue
    raise MarketDataError("Yahoo stock data is temporarily unavailable")


def _yahoo_history(ticker, start, end):
    def timestamp(value):
        return int(datetime.combine(date.fromisoformat(value), datetime.min.time(), timezone.utc).timestamp())

    result = _yahoo_chart(ticker, {
        "period1": timestamp(start), "period2": timestamp(end), "interval": "1d",
    })
    prices = result.get("indicators", {}).get("quote", [{}])[0]
    # Daily candles are labelled by the exchange's local trading date.
    dates = pd.to_datetime(result.get("timestamp", []), unit="s", utc=True)
    dates = dates.tz_convert(result["meta"].get("exchangeTimezoneName", "UTC")).tz_localize(None)
    frame = pd.DataFrame({"Date": dates, **{key.title(): value for key, value in prices.items()}})
    adjusted = result.get("indicators", {}).get("adjclose")
    if adjusted:
        frame["Adj Close"] = adjusted[0]["adjclose"]
    return normalize_history(frame)


def _twelve_request(ticker, endpoint, **params):
    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        raise MarketDataError("TWELVE_DATA_API_KEY is required for Twelve Data")
    symbol = ticker.removesuffix(".NS")
    if ticker.endswith(".NS"):
        params["exchange"] = "NSE"
    # Twelve Data uses a dot for US share classes, rather than Yahoo's dash.
    if symbol in ("BRK-A", "BRK-B"):
        symbol = symbol.replace("-", ".")
    payload = _request_json(f"https://api.twelvedata.com/{endpoint}", {
        "symbol": symbol, "apikey": api_key, **params,
    })
    if payload.get("status") == "error":
        raise MarketDataError("Twelve Data rejected the request; check API key, plan and ticker coverage")
    return payload


def _twelve_history(ticker, start, end):
    payload = _twelve_request(
        ticker, "time_series", interval="1day", start_date=start,
        end_date=end,
        outputsize=5000, order="ASC", adjust="splits",
    )
    frame = pd.DataFrame(payload.get("values", []))
    frame = frame.rename(columns={"datetime": "Date", **{
        column.lower(): column for column in PRICE_COLUMNS + ["Volume"]
    }})
    return normalize_history(frame)


def _providers():
    # A configured independent provider gets first choice; Yahoo remains key-free.
    return ["twelve", "yahoo"] if os.environ.get("TWELVE_DATA_API_KEY") else ["yahoo"]


def get_history(ticker, start="2023-01-01", end=None):
    end = end or (date.today() + timedelta(days=1)).isoformat()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    provider_key = "-".join(_providers())
    cache = CACHE_DIR / f"v2-{ticker}-{start}-{end}-{provider_key}.csv"
    # Serialize cache population so simultaneous chart/prediction requests share data.
    with _cache_lock:
        if cache.exists() and time.time() - cache.stat().st_mtime < CACHE_TTL:
            try:
                return normalize_history(pd.read_csv(cache))
            except (MarketDataError, ValueError, OSError):
                logger.warning("Ignoring invalid stock cache for %s", ticker)
        for provider in _providers():
            try:
                frame = (_twelve_history if provider == "twelve" else _yahoo_history)(ticker, start, end)
                frame = frame[(frame.Date >= start) & (frame.Date < end)].reset_index(drop=True)
                if frame.empty:
                    raise MarketDataError("No trading data in the requested date range")
            except (MarketDataError, ValueError, KeyError, TypeError, IndexError):
                logger.warning("%s history unavailable for %s", provider, ticker)
                continue
            temporary_path = None
            try:
                with NamedTemporaryFile(mode="w", dir=CACHE_DIR, suffix=".csv", delete=False) as temporary:
                    temporary_path = temporary.name
                    frame.to_csv(temporary, index=False)
                os.replace(temporary_path, cache)
            except OSError:
                logger.warning("Could not cache stock history for %s", ticker)
            finally:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)
            return frame
    raise MarketDataError(f"Unable to fetch stock history for {ticker}. Please try again later.")


def get_quote(ticker):
    for provider in _providers():
        try:
            if provider == "twelve":
                result = _twelve_request(ticker, "quote")
                price, previous = float(result["close"]), float(result["previous_close"])
            else:
                chart = _yahoo_chart(ticker, {"range": "5d", "interval": "1d"})
                result = chart["meta"]
                price = float(result["regularMarketPrice"])
                previous = result.get("previousClose")
                if previous is None:
                    # chartPreviousClose is the close BEFORE the entire 5-day range.
                    # Instead, select the candle preceding the quote's trading date.
                    zone = result.get("exchangeTimezoneName", "UTC")
                    market_date = pd.Timestamp(result["regularMarketTime"], unit="s", tz="UTC").tz_convert(zone).date()
                    closes = chart["indicators"]["quote"][0]["close"]
                    previous_closes = [close for timestamp, close in zip(chart["timestamp"], closes)
                                       if close is not None and pd.Timestamp(timestamp, unit="s", tz="UTC").tz_convert(zone).date() < market_date]
                    previous = previous_closes[-1]
                previous = float(previous)
            if not all(0 < value < float("inf") for value in (price, previous)):
                raise ValueError("Invalid quote")
            change = price - previous
            return [f"{price:.2f}", f"{change:+.2f}", f"({change / previous * 100:+.2f}%)"]
        except (MarketDataError, KeyError, TypeError, ValueError, IndexError):
            logger.warning("%s quote unavailable for %s", provider, ticker)
    raise MarketDataError(f"Unable to fetch the current price for {ticker}. Please try again later.")
