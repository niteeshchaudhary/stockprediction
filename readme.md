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
