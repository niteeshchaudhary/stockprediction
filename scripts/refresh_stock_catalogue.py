"""Refresh Folio's shared NSE stock directory using the official equity CSV."""

import argparse
import csv
import io
import json
import re
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
OUTPUT = Path(__file__).resolve().parents[1] / "shared" / "nse-stocks.json"


def catalogue_from_csv(content):
    stocks = {}
    for row in csv.DictReader(io.StringIO(content.lstrip("\ufeff"))):
        row = {key.strip(): value.strip() for key, value in row.items() if key and value}
        symbol = row.get("SYMBOL", "").upper()
        name = row.get("NAME OF COMPANY", "")
        if name and re.fullmatch(r"[A-Z0-9][A-Z0-9&.-]{0,29}", symbol):
            stocks[symbol] = {"symbol": symbol, "name": name}
    if len(stocks) < 1000:
        raise ValueError("Incomplete NSE response; the existing catalogue has not been changed")
    return {"source": SOURCE, "updated": date.today().isoformat(),
            "stocks": sorted(stocks.values(), key=lambda stock: stock["symbol"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Use a previously downloaded official NSE equity CSV")
    args = parser.parse_args()
    if args.csv:
        content = args.csv.read_text(encoding="utf-8-sig")
    else:
        with urlopen(Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
            content = response.read().decode("utf-8-sig")
    catalogue = catalogue_from_csv(content)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    print(f"Saved {len(catalogue['stocks'])} NSE companies to {OUTPUT}")


if __name__ == "__main__":
    main()
