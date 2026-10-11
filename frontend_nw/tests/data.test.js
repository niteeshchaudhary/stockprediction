import { afterEach, test, mock } from 'node:test'
import assert from 'node:assert/strict'
import { fetchHistory, fetchQuote, fetchForecast, fetchTrend, request } from '../src/lib/api.js'
import { STOCKS, filterHistory, money, exportHistory } from '../src/lib/stocks.js'

afterEach(() => mock.restoreAll())
const stock = STOCKS.find(item => item.id === 'bajaj finance')
function respond(payload, status = 200) {
  mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } }))
}

test('history requests encode company names and reject invalid candles', async () => {
  respond([
    { Date: '2026-10-02', Open: '100', High: '105', Low: '95', Close: '102', Volume: '1000' },
    { Date: '2026-10-01', Open: 90, High: 100, Low: 85, Close: 98 },
    { Date: 'bad', Close: null },
  ])
  const history = await fetchHistory(stock)
  assert.equal(globalThis.fetch.mock.calls[0].arguments[0], '/api/data/bajaj%20finance')
  assert.equal(history.length, 2)
  assert.equal(history[0].Date, '2026-10-01')
  assert.equal(history[1].Close, 102)
})

test('empty history is an actionable failure', async () => {
  respond([])
  await assert.rejects(fetchHistory(stock), /No price history/)
})

test('quote change is calculated from the previous close', async () => {
  respond({ values: ['110.00', '+10.00', '(+10.00%)'] })
  assert.deepEqual(await fetchQuote(stock), { price: 110, change: 10, percent: 10, quotedAt: null, fetchedAt: null, provider: null })
})

test('provider errors preserve the backend message', async () => {
  respond({ error: 'Market provider unavailable' }, 503)
  await assert.rejects(fetchHistory(stock), /Market provider unavailable/)
})

test('quote source timestamps stay distinct from fetch timestamps', async () => {
  respond({ values: ['110', '+10'], quoted_at: '2026-10-09T10:00:00+00:00', fetched_at: '2026-10-11T10:00:00+00:00', provider: 'yahoo' })
  const quote = await fetchQuote(stock)
  assert.equal(quote.quotedAt, '2026-10-09T10:00:00+00:00')
  assert.equal(quote.fetchedAt, '2026-10-11T10:00:00+00:00')
  assert.equal(quote.provider, 'yahoo')
})

test('non-JSON proxy failures explain how to reconnect', async () => {
  mock.method(globalThis, 'fetch', async () => new Response('Proxy failure', { status: 500 }))
  await assert.rejects(request('/data/reliance'), /Check that the backend is running/)
})

test('forecast values must be finite and positive', async () => {
  respond({ pvalue: '120.5', pvaluelstm: '122.5' })
  assert.deepEqual(await fetchForecast(stock), { statistical: 120.5, lstm: 122.5, models: undefined, asOf: undefined, horizon: undefined, warnings: [] })
  respond({ pvalue: 'NaN', pvaluelstm: '-1' })
  await assert.rejects(fetchForecast(stock), /invalid forecast/)
})

test('stock switching can cancel a pending request', async () => {
  mock.method(globalThis, 'fetch', async (_url, { signal }) => new Promise((_, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
  }))
  const controller = new AbortController()
  const pending = request('/data/reliance', { signal: controller.signal })
  controller.abort()
  await assert.rejects(pending, { name: 'AbortError' })
})

test('forecast preserves ensemble comparisons and evaluation metadata', async () => {
  const analysis = { price: 123, models: [{ id: 'baseline', mape: 1 }], evaluation_sessions: 20, beats_baseline: false }
  respond({ pvalue: 120, pvaluelstm: null, analysis })
  assert.deepEqual((await fetchForecast(stock)).analysis, analysis)
})

test('trend requests preserve missing-input coverage and reject invalid analyses', async () => {
  const analysis = { score: -5, coverage: 30, factors: [], fundamentals: { available: false }, indicators: {}, news: [], policy_news: [], warnings: ['Missing inputs'] }
  respond(analysis)
  assert.deepEqual(await fetchTrend(stock), analysis)
  assert.equal(globalThis.fetch.mock.calls[0].arguments[0], '/api/data/trend/bajaj%20finance')
  respond({ score: 'NaN' })
  await assert.rejects(fetchTrend(stock), /invalid analysis/)
})

test('an unavailable optional LSTM preserves the statistical forecast and model details', async () => {
  respond({ pvalue: 120, pvaluelstm: null, models: { statistical: 'Ridge autoregression', lstm: null }, as_of: '2026-10-05', horizon: 'Next trading session', warnings: ['LSTM disabled'] })
  const result = await fetchForecast(stock)
  assert.equal(result.statistical, 120)
  assert.equal(result.lstm, null)
  assert.equal(result.models.statistical, 'Ridge autoregression')
  assert.equal(result.asOf, '2026-10-05')
  assert.deepEqual(result.warnings, ['LSTM disabled'])
})

test('ranges use the last trading date, including historical data', () => {
  const history = ['2023-01-01', '2023-02-20', '2023-03-01'].map(Date => ({ Date, Close: 100 }))
  assert.equal(filterHistory(history, '1M').length, 2)
  assert.equal(filterHistory(history, 'ALL').length, 3)
  assert.equal(money(null), '—')
  assert.match(money(100, 'USD'), /\$100\.00/)
})

test('CSV export includes OHLC data and the selected symbol filename', async () => {
  let csvBlob
  const clicked = mock.fn()
  const removed = mock.fn()
  const link = { click: clicked, remove: removed }
  const originalDocument = globalThis.document
  globalThis.document = { createElement: () => link, body: { appendChild: mock.fn() } }
  mock.method(URL, 'createObjectURL', blob => { csvBlob = blob; return 'blob:test' })
  mock.method(URL, 'revokeObjectURL', () => {})
  mock.method(globalThis, 'setTimeout', callback => { callback(); return 0 })
  try {
    exportHistory([{ Date: '2026-10-05', Open: 100, High: 105, Low: 99, Close: 103, 'Adj Close': 103, Volume: 1000 }], 'RELIANCE')
    assert.equal(link.download, 'RELIANCE-history.csv')
    assert.equal(clicked.mock.callCount(), 1)
    assert.equal(removed.mock.callCount(), 1)
    assert.equal(await csvBlob.text(), 'Date,Open,High,Low,Close,Adj Close,Volume\r\n2026-10-05,100,105,99,103,103,1000')
  } finally {
    if (originalDocument === undefined) delete globalThis.document
    else globalThis.document = originalDocument
  }
})
