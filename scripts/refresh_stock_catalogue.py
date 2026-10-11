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
INSTRUMENT_SOURCE = 'https://images.dhan.co/api-data/api-scrip-master.csv'
EXCHANGE_OUTPUT = OUTPUT.with_name('indian-stocks.json')


def catalogue_from_instruments(content):
    stocks = {}
    for row in csv.DictReader(io.StringIO(content.lstrip('\ufeff'))):
        exchange = row.get('SEM_EXM_EXCH_ID', '')
        if exchange not in {'NSE', 'BSE'} or row.get('SEM_SEGMENT') != 'E' or row.get('SEM_EXCH_INSTRUMENT_TYPE') != 'ES':
            continue
        symbol = row.get('SEM_TRADING_SYMBOL', '').strip().upper()
        code = row.get('SEM_SMST_SECURITY_ID', '').strip()
        name = (row.get('SEM_CUSTOM_SYMBOL') or row.get('SM_SYMBOL_NAME') or symbol).strip()
        if not name or not re.fullmatch(r'[A-Z0-9][A-Z0-9&.-]{0,29}', symbol):
            continue
        if exchange == 'BSE' and not re.fullmatch(r'\d{6}', code):
            continue
        ticker = f'{symbol}.NS' if exchange == 'NSE' else f'{symbol}.BO'
        stocks[ticker] = {'symbol': symbol, 'name': name, 'market': exchange, 'ticker': ticker,
                          'id': f'{symbol}.NS' if exchange == 'NSE' else f'{code}.BO',
                          'scripCode': code if exchange == 'BSE' else None}
    counts = {exchange: sum(stock['market'] == exchange for stock in stocks.values()) for exchange in ['NSE', 'BSE']}
    if counts['NSE'] < 2000 or counts['BSE'] < 4000:
        raise ValueError('Incomplete exchange instrument response; existing catalogue unchanged')
    return {'source': INSTRUMENT_SOURCE, 'updated': date.today().isoformat(), 'counts': counts,
            'stocks': sorted(stocks.values(), key=lambda stock: (stock['market'], stock['symbol']))}


def download(source):
    with urlopen(Request(source, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45) as response:
        return response.read().decode('utf-8-sig')


def save_catalogue(path, catalogue):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)
    print(f'Saved {len(catalogue["stocks"])} listings to {path}')


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
    parser.add_argument('--instruments-csv', type=Path, help='Use a previously downloaded Dhan instrument CSV')
    args = parser.parse_args()
    if args.csv:
        content = args.csv.read_text(encoding="utf-8-sig")
    else:
        content = download(SOURCE)
    catalogue = catalogue_from_csv(content)
    instruments = args.instruments_csv.read_text(encoding='utf-8-sig') if args.instruments_csv else download(INSTRUMENT_SOURCE)
    exchanges = catalogue_from_instruments(instruments)
    # Validate both responses before replacing either directory.
    save_catalogue(OUTPUT, catalogue)
    save_catalogue(EXCHANGE_OUTPUT, exchanges)


if __name__ == "__main__":
    main()
