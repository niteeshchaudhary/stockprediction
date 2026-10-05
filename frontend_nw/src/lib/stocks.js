import catalogue from '../../../shared/nse-stocks.json' with { type: 'json' }

const FEATURED_STOCKS = [
  { id: 'reliance', name: 'Reliance Industries', symbol: 'RELIANCE', sector: 'Energy', color: '#5264c9', initials: 'RI' },
  { id: 'tcs', name: 'Tata Consultancy Services', symbol: 'TCS', sector: 'Technology', color: '#9659b4', initials: 'TC' },
  { id: 'hdfc', name: 'HDFC Bank', symbol: 'HDFCBANK', sector: 'Banking', color: '#3467a5', initials: 'HD' },
  { id: 'infosys', name: 'Infosys', symbol: 'INFY', sector: 'Technology', color: '#328bba', initials: 'IN' },
  { id: 'icici', name: 'ICICI Bank', symbol: 'ICICIBANK', sector: 'Banking', color: '#b77044', initials: 'IC' },
  { id: 'itc', name: 'ITC Limited', symbol: 'ITC', sector: 'Consumer goods', color: '#4266a2', initials: 'IT' },
  { id: 'sbi', name: 'State Bank of India', symbol: 'SBIN', sector: 'Banking', color: '#288aac', initials: 'SB' },
  { id: 'airtel', name: 'Bharti Airtel', symbol: 'BHARTIARTL', sector: 'Telecom', color: '#c35c60', initials: 'BA' },
  { id: 'hcl', name: 'HCL Technologies', symbol: 'HCLTECH', sector: 'Technology', color: '#4383b7', initials: 'HC' },
  { id: 'sunpharma', name: 'Sun Pharmaceutical', symbol: 'SUNPHARMA', sector: 'Healthcare', color: '#b4783f', initials: 'SP' },
  { id: 'cipla', name: 'Cipla', symbol: 'CIPLA', sector: 'Healthcare', color: '#5776b3', initials: 'CI' },
  { id: 'bajaj finance', name: 'Bajaj Finance', symbol: 'BAJFINANCE', sector: 'Finance', color: '#576eaa', initials: 'BF' },
  { id: 'ntpc', name: 'NTPC Limited', symbol: 'NTPC', sector: 'Utilities', color: '#7c73b3', initials: 'NT' },
  { id: 'axis', name: 'Axis Bank', symbol: 'AXISBANK', sector: 'Banking', color: '#a65a80', initials: 'AX' },
  { id: 'tata steel', name: 'Tata Steel', symbol: 'TATASTEEL', sector: 'Materials', color: '#5b789d', initials: 'TS' },
  { id: 'maruti', name: 'Maruti Suzuki', symbol: 'MARUTI', sector: 'Automotive', color: '#5170b6', initials: 'MS' },
  { id: 'coal india', name: 'Coal India', symbol: 'COALINDIA', sector: 'Energy', color: '#9b7850', initials: 'CO' },
  { id: 'hero', name: 'Hero MotoCorp', symbol: 'HEROMOTOCO', sector: 'Automotive', color: '#b96369', initials: 'HM' },
  { id: 'apple', name: 'Apple', symbol: 'AAPL', sector: 'Technology', color: '#6b747e', initials: 'AP', market: 'NASDAQ', currency: 'USD' },
  { id: 'microsoft', name: 'Microsoft', symbol: 'MSFT', sector: 'Technology', color: '#68875e', initials: 'MS', market: 'NASDAQ', currency: 'USD' },
].map(stock => ({ market: 'NSE', currency: 'INR', ...stock }))

const COLORS = ['#5264c9', '#328bba', '#b77044', '#9659b4', '#68875e', '#a65a80']
const ALIASES = {
  CANBK: ['canabank', 'canara bank'],
  BAJAJHFL: ['bajaj housing finance', 'bajaj housing finace'],
  IRFC: ['irfc', 'indian railway finance'],
  IOB: ['iob', 'indian overseas bank'],
}
const featuredSymbols = new Set(FEATURED_STOCKS.filter(stock => stock.market === 'NSE').map(stock => stock.symbol))

function decorateStock(stock) {
  const hash = [...stock.symbol].reduce((value, char) => value + char.charCodeAt(0), 0)
  return {
    color: COLORS[hash % COLORS.length],
    initials: stock.name.split(/\s+/).slice(0, 2).map(word => word[0]).join('').toUpperCase(),
    sector: 'Equity', ...stock,
  }
}

export const STOCKS = [
  ...FEATURED_STOCKS,
  ...catalogue.stocks.filter(stock => !featuredSymbols.has(stock.symbol)).map(stock => decorateStock({
    ...stock, id: `${stock.symbol}.NS`, market: 'NSE', currency: 'INR', aliases: ALIASES[stock.symbol] || [],
  })),
]
const STOCK_BY_ID = new Map(STOCKS.map(stock => [stock.id, stock]))
const STOCK_BY_TICKER = new Map(STOCKS.map(stock => [stock.market === 'NSE' ? `${stock.symbol}.NS` : stock.symbol, stock]))
export const CATALOGUE_UPDATED = catalogue.updated
export const TICKER_PATTERN = /^[A-Z0-9][A-Z0-9&-]{0,29}(?:\.(?:NS|BO))?$/

export function stockFromTicker(value) {
  const ticker = value.trim().toUpperCase()
  if (!TICKER_PATTERN.test(ticker)) return null
  if (STOCK_BY_TICKER.has(ticker)) return STOCK_BY_TICKER.get(ticker)
  const market = ticker.endsWith('.NS') ? 'NSE' : ticker.endsWith('.BO') ? 'BSE' : 'US'
  const stock = decorateStock({ id: `ticker:${ticker}`, symbol: ticker.replace(/\.(NS|BO)$/, ''), name: ticker,
    market, currency: market === 'US' ? 'USD' : 'INR', sector: 'Custom ticker' })
  STOCK_BY_ID.set(stock.id, stock)
  STOCK_BY_TICKER.set(ticker, stock)
  return stock
}

export function getStock(id) {
  if (typeof id !== 'string') return null
  return STOCK_BY_ID.get(id) || (id.startsWith('ticker:') ? stockFromTicker(id.slice(7)) : null)
}

function normalizeSearch(value) {
  return value.toLowerCase().replace(/finace/g, 'finance').replace(/[^a-z0-9]/g, '')
}
const SEARCH_INDEX = STOCKS.map(stock => ({ stock,
  name: normalizeSearch(stock.name), symbol: normalizeSearch(stock.symbol),
  aliases: (stock.aliases || []).map(normalizeSearch),
}))

export function searchStocks(query, limit = 7) {
  const term = normalizeSearch(query)
  if (!term) return STOCKS.slice(0, limit)
  return SEARCH_INDEX.filter(entry => entry.name.includes(term) || entry.symbol.includes(term) || entry.aliases.some(alias => alias.includes(term)))
    .sort((a, b) => {
      const rank = entry => entry.symbol === term || entry.aliases.includes(term) ? 0 : entry.name === term ? 1 : entry.symbol.startsWith(term) ? 2 : entry.name.startsWith(term) ? 3 : 4
      return rank(a) - rank(b)
    }).slice(0, limit).map(entry => entry.stock)
}

export const DEFAULT_WATCHLIST = ['reliance', 'tcs', 'hdfc', 'infosys', 'icici']

export function money(value, currency = 'INR', decimals = 2) {
  if (value == null || !Number.isFinite(Number(value))) return '—'
  return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', {
    style: 'currency', currency, minimumFractionDigits: decimals, maximumFractionDigits: decimals,
  }).format(Number(value))
}

export function number(value, decimals = 2) {
  if (value == null || !Number.isFinite(Number(value))) return '—'
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: decimals }).format(Number(value))
}

export function formatDate(value, options = {}) {
  const date = new Date(`${value}T12:00:00`)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', ...options })
}

export function filterHistory(history, range) {
  if (range === 'ALL' || !history.length) return history
  const days = { '1M': 30, '3M': 90, '6M': 180, '1Y': 365 }[range]
  const cutoff = new Date(`${history.at(-1).Date}T12:00:00`)
  cutoff.setDate(cutoff.getDate() - days)
  return history.filter(row => new Date(`${row.Date}T12:00:00`) >= cutoff)
}

export function exportHistory(history, symbol) {
  const columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
  const csv = [columns.join(','), ...history.map(row => columns.map(key => row[key] ?? '').join(','))].join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `${symbol}-history.csv`
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
