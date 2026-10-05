# Folio · React + Vite

A responsive stock dashboard for the existing Flask backend. The frontend uses
React, native Fetch, custom SVG charts and plain CSS. There are no charting,
component-library, Firebase or Axios dependencies.

## Run locally

Use Node.js 22.12+ (the included ESLint tooling needs 22.13+) or a compatible newer
LTS version. From the repository root:

```powershell
cd frontend_nw
npm install
npm run dev
```

Open http://localhost:5173. `npm start` is also supported. Once the lockfile is
present, use `npm ci` for repeatable installs. No `--force` or legacy peer flags
are needed.

In a second terminal, start the backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-data.txt
.\.venv\Scripts\python.exe server.py
```

The minimal requirements enable history, quotes and statistical forecasts. News
sentiment models are not required for forecasting. LSTM is optional; see the
root README for enabling TensorFlow.

## Features

- Search NSE and US companies by name or symbol, including keyboard navigation
  and Ctrl/Cmd + K.
- Hover over closing prices and switch between 1M, 3M, 6M, 1Y and full history.
- Generate next-session statistical forecasts, with optional LSTM when enabled.
- Save or remove companies from a watchlist persisted in local storage.
- View recent trading sessions and export the full stock history as CSV.
- Display connection, loading, partial-data and retry states without fabricated
  stock prices or forecasts.
- Use the dashboard on mobile with a collapsible navigation drawer.

## Backend configuration

Vite proxies `/api` to `http://127.0.0.1:5000` and strips the prefix. This works in
both development and local preview, so browser requests stay on the same origin.
To change the backend port, copy `.env.example` to `.env.local`, set `BACKEND_URL`,
and restart Vite.

For a production deployment, configure your web server to proxy `/api` to Flask.
Alternatively, set `VITE_API_BASE_URL` to the backend address at build time and
configure Flask CORS for the frontend's origin. Never put market-provider API
keys in variables prefixed with `VITE_`; those are sent to the browser.

Google Fonts are optional: system fonts are used when they cannot be loaded.

## Verify

```powershell
npm run lint
npm test
npm run build
npm run preview
```

The API and data tests use Node's built-in test runner. Production output is
written to `dist/`.
# Expanded stock coverage

Folio searches 2,614 NSE companies from the official NSE equity listing, plus its featured US stocks. Search by company name or symbol, including IRFC, TATASTEEL, CANBK (also CANABANK), BAJAJHFL and IOB. Select a company and click its star to save it. The watchlist has no application-imposed stock limit and persists in this browser.

For symbols outside the catalogue, enter a Yahoo-compatible ticker: `NVDA`, `500325.BO` for BSE or an Indian ticker ending in `.NS`. Quotes and history depend on provider availability. Custom stocks also persist in the watchlist.

Both frontend and backend use `shared/nse-stocks.json`. Refresh the catalogue from NSE with `python scripts/refresh_stock_catalogue.py` at the repository root, then restart/rebuild the app. The refresh script validates the download before replacing the catalogue.
