# StockPrediction

- Predict the closing price of stocks with the help of previous data and todays news sentiments.
- The model uses moving average, different stock strategies and news sentiments as factors and predict the closing price.
- Stock history and quotes use Yahoo's structured chart endpoint, without HTML scraping.
- Set `TWELVE_DATA_API_KEY` to prefer Twelve Data, with Yahoo as a fallback.


# How to run ? 
download model and tokenizer folder from
https://drive.google.com/drive/folders/1PPKOWUygpNf9HfECWR1wLgiKwNWMGFPx?usp=sharing
and place them in backend folder.

goto frontend_nw folder and execute following commands:
npm install
to run:
npm run dev

Open http://localhost:5173. The new React + Vite dashboard replaces the old
Create React App frontend. See [frontend_nw/README.md](frontend_nw/README.md) for
requirements, backend proxy configuration and available features.

goto backend folder and execute following commands:
python –m venv env
In linux:
    source env/bin/activate

In Windows:
    env/Scripts/activate

pip install -r requirements.txt
to run:
python server.py

## Stock data setup and troubleshooting

History, quotes and statistical predictions run without downloaded sentiment
models or TensorFlow. For a minimal setup in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-data.txt
.\.venv\Scripts\python.exe server.py
```

Statistical forecasts use ridge autoregression on recent daily log returns and
forecast the next trading session. At least 65 valid daily candles are required.

Forecasts also compare weighted momentum, damped Holt trend (fixed smoothing
parameters), and ridge regression on return lags, RSI, moving-average deviation
and volatility against a last-close baseline. These models use NumPy and require
no additional installs. Up to 40 recent rolling one-session predictions use only
earlier observations. The earlier half fits inverse-error ensemble weights;
the later half evaluates those fixed weights and all component models. The UI
reports average percentage error, direction accuracy and whether the ensemble
beats the baseline. The displayed range uses the 90th percentile of recent
absolute percentage errors; it is not a calibrated confidence interval. RSI uses
simple average gains/losses over 14 sessions. Analysis covers daily close prices,
not news, fundamentals, volume or the broader market. Optional LSTM remains
separate and is not included in the ensemble or its backtest.
The response identifies the model and last history date. The old news sentiment
pipeline remains optional and separate; its `/newsanalysis` endpoint still needs
the legacy dependencies and local model/tokenizer folders.

Data uses flat numeric OHLC columns and `YYYY-MM-DD` dates. The backend creates
`backend/csvfiles` automatically and caches history for 15 minutes. Empty or
invalid responses are rejected and never cached. Unknown companies return 404;
provider failures return a JSON error with status 503, shown in the frontend.

Yahoo works without an API key, but its chart endpoint is unofficial and can be
rate limited or changed. For an independent provider, get a key from
[Twelve Data](https://twelvedata.com/docs), then set it before starting Flask:

```powershell
$env:TWELVE_DATA_API_KEY = "your-key"
.\.venv\Scripts\python.exe server.py
```

The key stays on the backend. Twelve Data must support the requested market on
your account/plan; Indian `.NS` symbols are requested on the NSE exchange.
If Twelve Data fails, Yahoo is attempted automatically. Quotes are provider
quotes and may be delayed; outside market hours they show the latest available
price and its change from the previous trading close.

The Vite frontend runs at `http://localhost:5173` and proxies `/api` to Flask at
`http://127.0.0.1:5000`. Set `BACKEND_URL` in `frontend_nw/.env.local` if the backend
uses another address; see the frontend README for production configuration.

Run the backend regression checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Prediction logs and optional LSTM

### Combined news and fundamentals trend analysis

`GET /data/trend/<company>` returns one **Evidence-weighted trend score** and an
indicative 5–20-session directional bias. No account or new library is required.
Google News RSS supplies company-matched headlines (7 days) and distinct budget/
policy headlines (30 days); Screener supplies public Indian-company valuation,
results and quarterly ownership. Yahoo supplies daily prices and the Nifty 50,
Sensex or S&P 500 benchmark. Public source coverage and HTML formats can change;
unavailable inputs are reported instead of blocking other sources.

Fixed maximum factor weights: price trend 30, market/relative strength 15,
company news 20, fundamentals 20, ownership changes 10, budget/policy news 5.
The score ranges from -100 to +100; missing components contribute zero and
weights are never redistributed. The app requires at least 60% weighted input
coverage and price history within seven days before assigning a direction.
Scores >=15 indicate upward bias, <=-15 downward bias, otherwise mixed/flat.
At least 50 sessions are required. News signals use conservative phrase rules,
negation checks and publisher diversity, not full articles or a language model.
Ambiguous headlines remain unclassified. This heuristic has no claimed forecast
accuracy: point-in-time news and filings are needed for a meaningful backtest.

P/E is compared with at least three positive-P/E peers (excluding the target),
and has 35% of the fundamentals factor. Same-quarter net-profit and sales YoY
growth have 40% and 25%; reported net profit may include one-off items. Holdings
use quarter-on-quarter promoter/FII/DII changes (50%/25%/25% of ownership),
not a rule that high promoter holding is bullish. Results/ownership periods older
than 180 days are excluded. ROE/ROCE, RSI and volume are shown as context.
Promoter pledging, full Union Budget documents and verified company-specific
policy impact are not assessed. Displayed peers can differ materially in business
mix, so valuation comparisons need review.

Headlines are cached 15 minutes and fundamentals six hours; failure responses
are cached only one minute. Source timestamps and reported periods are visible.
No source needs the legacy news-analysis TensorFlow/Transformers model folders.


Logs appear in the terminal and `backend/logs/server.log` even when Flask is
imported by another launcher. Logs rotate at 2 MB and keep three backups. Each
request has an `X-Request-ID`; errors include that ID, and prediction logs show
history loading, model fitting, completion and full tracebacks on failure.
Set `LOG_LEVEL=DEBUG` for more verbose logs.

The statistical forecast is available by default. To also train a small LSTM
for the next session, from the backend directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lstm.txt
$env:ENABLE_LSTM = "true"
.\.venv\Scripts\python.exe server.py
```

If LSTM is disabled or fails, the statistical forecast still returns successfully;
`pvaluelstm` is null and the frontend explains its availability. LSTM requests
train on at most 512 closing prices and predict from the final 60 actual closes.
Forecasts are experimental estimates; neither model includes news sentiment.
