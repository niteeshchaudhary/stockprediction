import logging
import os
import time
import uuid
from functools import lru_cache

from flask import Flask, Response, jsonify, g, request
from flask_cors import CORS

from market_data import MarketDataError, get_history, get_quote
from stock_directory import resolve_directory_ticker
from forecast_service import generate_forecast
from server_logging import configure_logging

configure_logging()


company_tickers = {
    "microsoft": "MSFT",
    "cisco": "CSCO",
    "intel": "INTC",
    "apple": "AAPL",
    "tcs": "TCS.NS",
    "hcl": "HCLTECH.NS",
    "nike": "NKE",
    "mcdonald's": "MCD",
    "disney": "DIS",
    "walmart": "WMT",
    "american express": "AXP",
    "goldman": "GS",
    "visa": "V",
    "berkshire": "BRK-B",
    "jpmorgan": "JPM",
    "mastercard": "MA",
    "wells fargo": "WFC",
    "citigroup": "C",
    "hsbc": "HSBC",
    "morgan stanley": "MS",
    "amgen": "AMGN",
    "boeing": "BA",
    "coca-cola": "KO",
    "verizon": "VZ",
    "dlf ltd": "DLF.NS",
    "tata power": "TATAPOWER.NS",
    "indian_oil": "IOC.NS",
    "adani": "ADANIGREEN.NS",
    "tata motors": "TATAMOTORS.NS",
    "sunpharma": "SUNPHARMA.NS",
    "cipla": "CIPLA.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "ntpc": "NTPC.NS",
    "axis": "AXISBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "reliance": "RELIANCE.NS",
    "tata steel": "TATASTEEL.NS",
    "power grid": "POWERGRID.NS",
    "sbi": "SBIN.NS",
    "oil and natural gas": "ONGC.NS",
    "sbi life": "SBILIFE.NS",
    "hdfc life": "HDFCLIFE.NS",
    "tata consumer": "TATACONSUM.NS",
    "airtel": "BHARTIARTL.NS",
    "maruti": "MARUTI.NS",
    "coal india": "COALINDIA.NS",
    "hero": "HEROMOTOCO.NS",
    "eicher motors": "EICHERMOT.NS",
    "hindalco": "HINDALCO.NS",
    "infosys": "INFY.NS",
    "itc": "ITC.NS",
}

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])


@app.before_request
def begin_request():
    g.started = time.perf_counter()
    g.request_id = uuid.uuid4().hex[:12]
    app.logger.info('Request %s started %s %s', g.request_id, request.method, request.path)


@app.after_request
def log_response(response):
    response.headers['X-Request-ID'] = g.request_id
    app.logger.info('Request %s completed %s %s status=%s duration=%.3fs',
                    g.request_id, request.method, request.path, response.status_code,
                    time.perf_counter() - g.started)
    return response


def resolve_ticker(company):
    return company_tickers.get(company.strip().lower()) or resolve_directory_ticker(company)


@app.errorhandler(MarketDataError)
def market_data_error(error):
    app.logger.warning('Request %s market data failed: %s', g.request_id, error)
    return jsonify({'error': str(error)}), 503


@lru_cache(maxsize=1)
def get_news_sentiment():
    # Missing sentiment models must not prevent stock data endpoints from starting.
    import news_analysis
    return news_analysis.get_news_report()


@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/newsanalysis', methods=['GET'])
def newsAnalysis():
    try:
        return jsonify(get_news_sentiment())
    except Exception:
        app.logger.exception('News analysis unavailable')
        return jsonify({'error': 'News analysis unavailable. Install the backend dependencies and model/tokenizer folders.'}), 503


@app.route('/data/current/<company>', methods=['GET'])
def currentInfo(company):
    ticker = resolve_ticker(company)
    if ticker is None:
        return jsonify({'error': 'Unknown company'}), 404
    return jsonify({'values': get_quote(ticker)})


def getcurrentInfo(company):
    ticker = resolve_ticker(company)
    if ticker is None:
        raise ValueError('Unknown company')
    return get_quote(ticker)


@app.route('/data/<company>', methods=['GET'])
def getdata(company):
    ticker = resolve_ticker(company)
    if ticker is None:
        return jsonify({'error': 'Unknown company'}), 404
    frame = get_history(ticker)
    return Response(frame.to_json(orient='records'), mimetype='application/json')


@app.route('/data/predict/<company>', methods=['GET'])
def predict(company):
    ticker = resolve_ticker(company)
    if ticker is None:
        return jsonify({'error': 'Unknown company'}), 404
    try:
        app.logger.info('Request %s prediction fetching history ticker=%s', g.request_id, ticker)
        frame = get_history(ticker)
        if len(frame) < 65:
            app.logger.warning('Prediction rejected ticker=%s rows=%s', ticker, len(frame))
            return jsonify({'error': 'At least 65 trading days are required for prediction.'}), 422
        app.logger.info('Request %s prediction fitting ticker=%s rows=%s', g.request_id, ticker, len(frame))
        result = generate_forecast(frame)
        app.logger.info('Request %s prediction completed ticker=%s as_of=%s statistical=%s lstm=%s',
                        g.request_id, ticker, result['as_of'], result['pvalue'], result['pvaluelstm'])
        return jsonify(result)
    except MarketDataError:
        raise
    except Exception:
        app.logger.exception('Request %s prediction failed ticker=%s', g.request_id, ticker)
        return jsonify({'error': 'Prediction failed. See backend/logs/server.log for details.', 'request_id': g.request_id}), 503


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=os.getenv('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'})
