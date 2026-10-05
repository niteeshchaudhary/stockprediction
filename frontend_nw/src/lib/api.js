const API_BASE = (import.meta.env?.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export async function request(path, { signal, timeout = 60000 } = {}) {
  const controller = new AbortController()
  const cancel = () => controller.abort()
  if (signal?.aborted) cancel()
  signal?.addEventListener('abort', cancel, { once: true })
  const timer = setTimeout(cancel, timeout)
  try {
    const response = await fetch(`${API_BASE}${path}`, { signal: controller.signal })
    const payload = await response.json().catch(() => null)
    if (!response.ok) throw new Error(payload?.error || 'The data service is unavailable. Check that the backend is running, then retry.')
    if (payload == null) throw new Error('The data service returned an invalid response.')
    return payload
  } catch (error) {
    if (controller.signal.aborted && !signal?.aborted) throw new Error('The request timed out. Please try again.', { cause: error })
    if (error instanceof TypeError) throw new Error('Unable to connect to the data service. Check your connection and backend.', { cause: error })
    throw error
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}

export async function fetchHistory(stock, options) {
  const rows = await request(`/data/${encodeURIComponent(stock.id)}`, options)
  if (!Array.isArray(rows) || !rows.length) throw new Error('No price history is available for this company.')
  const history = rows.filter(row => /^\d{4}-\d{2}-\d{2}$/.test(row.Date) &&
    ['Open', 'High', 'Low', 'Close'].every(key => row[key] != null && Number.isFinite(Number(row[key]))))
    .map(row => ({ ...row, Open: Number(row.Open), High: Number(row.High), Low: Number(row.Low), Close: Number(row.Close), Volume: Number(row.Volume) || 0 }))
    .sort((a, b) => a.Date.localeCompare(b.Date))
  if (!history.length) throw new Error('The provider returned no usable price history.')
  return history
}

export async function fetchQuote(stock, options) {
  const quote = await request(`/data/current/${encodeURIComponent(stock.id)}`, options)
  const price = Number(quote.values?.[0])
  const change = Number(quote.values?.[1])
  if (!Array.isArray(quote.values) || !Number.isFinite(price) || !Number.isFinite(change) || price <= 0) {
    throw new Error('A current quote is unavailable for this company.')
  }
  const previous = price - change
  return { price, change, percent: previous > 0 ? change / previous * 100 : null }
}

export async function fetchForecast(stock, options) {
  const payload = await request(`/data/predict/${encodeURIComponent(stock.id)}`, { timeout: 300000, ...options })
  const statistical = Number(payload.pvalue)
  const lstm = payload.pvaluelstm == null ? null : Number(payload.pvaluelstm)
  if (!Number.isFinite(statistical) || statistical <= 0 || (lstm !== null && (!Number.isFinite(lstm) || lstm <= 0))) throw new Error('The models returned an invalid forecast.')
  return { statistical, lstm, models: payload.models, asOf: payload.as_of, horizon: payload.horizon, warnings: payload.warnings || [] }
}
