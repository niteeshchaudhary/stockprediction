import { useEffect, useRef, useState } from 'react'
import Icon from './components/Icon'
import StockSearch, { CompanyMark } from './components/StockSearch'
import PriceChart from './components/PriceChart'
import Guide from './components/Guide'
import useMarketData from './hooks/useMarketData'
import useWatchlist from './hooks/useWatchlist'
import useMobile from './hooks/useMobile'
import { fetchForecast } from './lib/api'
import { getStock, DEFAULT_WATCHLIST, money, number, formatDate, filterHistory, exportHistory } from './lib/stocks'
import './App.css'

function readWatchlist() {
  try {
    const stored = JSON.parse(localStorage.getItem('folio-watchlist'))
    return Array.isArray(stored) ? [...new Set(stored.map(id => getStock(id)?.id).filter(Boolean))] : DEFAULT_WATCHLIST
  } catch { return DEFAULT_WATCHLIST }
}

function Change({ percent, className = '' }) {
  if (!Number.isFinite(percent)) return <span className={`muted ${className}`}>—</span>
  return <span className={`change ${percent < 0 ? 'negative' : 'positive'} ${className}`}><Icon name="trend" size={14}/>{percent >= 0 ? '+' : ''}{percent.toFixed(2)}%</span>
}

const NAVIGATION = [
  { id: 'overview', icon: 'grid', label: 'Overview' },
  { id: 'watchlist', icon: 'star', label: 'My watchlist' },
  { id: 'history', icon: 'chart', label: 'Price history' },
]

function WatchlistRows({ detailed = false, watchlist, selected, selectedQuote, watchQuotes, onSelect, onToggle }) {
  return <div className={detailed ? 'watchlist-table' : 'watchlist-items'}>
    {detailed && <div className="watchlist-table-head"><span>Company</span><span>Market</span><span>Latest price</span><span>Day change</span><span>Actions</span></div>}
    {watchlist.map(id => {
      const item = getStock(id)
      const quote = id === selected && selectedQuote ? selectedQuote : watchQuotes[id]
      return <div className={`watchlist-row ${id === selected ? 'selected' : ''}`} key={id}>
        <button className="watchlist-company" onClick={() => onSelect(id)}><CompanyMark stock={item} small/><span><strong>{detailed ? item.name : item.symbol}</strong><small>{detailed ? item.symbol : item.name}</small></span></button>
        {detailed && <span className="market-pill">{item.market}</span>}
        <span className="watchlist-price">{quote ? money(quote.price, item.currency) : '—'}{!detailed && <Change percent={quote?.percent}/>}</span>
        {detailed && <Change percent={quote?.percent}/>}
        {detailed && <button className="icon-button" aria-label={`Remove ${item.name} from watchlist`} onClick={() => onToggle(id)}><Icon name="close" size={17}/></button>}
      </div>
    })}
    {!watchlist.length && <div className="watchlist-empty"><Icon name="star" size={28}/><h3>Keep your favorites close</h3><p>Search for a company, then use “Add to watchlist”.</p></div>}
  </div>
}

function App() {
  const [selected, setSelected] = useState('reliance')
  const [view, setView] = useState('overview')
  const [range, setRange] = useState('3M')
  const [refresh, setRefresh] = useState(0)
  const [watchlist, setWatchlist] = useState(readWatchlist)
  const [guide, setGuide] = useState(false)
  const [sidebar, setSidebar] = useState(false)
  const mobile = useMobile()
  const [forecast, setForecast] = useState({ id: null, loading: false, result: null, error: null })
  const predictionController = useRef(null)
  const forecastSection = useRef(null)
  const stock = getStock(selected)
  const market = useMarketData(stock, refresh)
  const watchQuotes = useWatchlist(watchlist, refresh)
  const visibleHistory = filterHistory(market.history, range)
  const latest = market.history.at(-1)
  const previous = market.history.at(-2)
  const currentPrice = market.quote?.price ?? latest?.Close
  const dayPercent = market.quote?.percent ?? (previous ? (latest.Close / previous.Close - 1) * 100 : null)
  const periodPercent = visibleHistory.length > 1 ? (visibleHistory.at(-1).Close / visibleHistory[0].Close - 1) * 100 : null
  const saved = watchlist.includes(selected)
  const activeForecast = forecast.id === selected ? forecast : { loading: false, result: null, error: null }
  const available = Boolean(market.quote || market.history.length)
  const status = market.loading ? 'Connecting' : market.errors.length ? (available ? 'Partial data' : 'Disconnected') : 'Connected'

  useEffect(() => {
    try { localStorage.setItem('folio-watchlist', JSON.stringify(watchlist)) } catch { /* Watchlist still works when storage is unavailable. */ }
  }, [watchlist])
  useEffect(() => () => predictionController.current?.abort(), [])

  function selectStock(id) {
    const next = getStock(id)
    if (!next) return
    id = next.id
    predictionController.current?.abort()
    setForecast({ id: null, loading: false, result: null, error: null })
    setSelected(id)
    setView('overview')
    setSidebar(false)
  }
  function toggleWatchlist(id) {
    const next = getStock(id)
    if (!next) return
    id = next.id
    setWatchlist(items => items.includes(id) ? items.filter(item => item !== id) : [...items, id])
  }
  async function generateForecast() {
    if (market.loading || market.history.length < 65 || activeForecast.loading) return
    predictionController.current?.abort()
    const controller = new AbortController()
    predictionController.current = controller
    setForecast({ id: selected, loading: true, result: null, error: null })
    try {
      const result = await fetchForecast(stock, { signal: controller.signal })
      if (!controller.signal.aborted) setForecast({ id: stock.id, loading: false, result, error: null })
    } catch (error) {
      if (!controller.signal.aborted) setForecast({ id: stock.id, loading: false, result: null, error: error.message })
    }
  }
  function showForecast() {
    setView('overview')
    setSidebar(false)
    requestAnimationFrame(() => forecastSection.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
  }



  return <div className="app-shell">
    {sidebar && <button className="sidebar-scrim" onClick={() => setSidebar(false)} aria-label="Close navigation"/>}
    <aside className={`sidebar ${sidebar ? 'open' : ''}`} inert={mobile && !sidebar}>
      <a className="brand" href="#" onClick={event => { event.preventDefault(); setView('overview'); setSidebar(false) }}><span className="brand-mark"><Icon name="chart" size={22}/></span>folio<span className="brand-dot">.</span></a>
      <div className="workspace-label">YOUR WORKSPACE</div>
      <nav aria-label="Main navigation">
        {NAVIGATION.map(item => <button key={item.id} className={`nav-item ${view === item.id ? 'active' : ''}`} aria-current={view === item.id ? 'page' : undefined} onClick={() => { setView(item.id); setSidebar(false) }}><Icon name={item.icon}/><span>{item.label}</span>{item.id === 'watchlist' && <span className="nav-count">{watchlist.length}</span>}</button>)}
        <button className="nav-item" onClick={showForecast}><Icon name="sparkles"/><span>AI forecasts</span><span className="nav-new">LAB</span></button>
      </nav>
      <div className="sidebar-insight"><span className="insight-orbit"><Icon name="sparkles" size={24}/></span><h3>A little perspective.<br/>A lot of possibility.</h3><p>Understand the past.<br/>Explore what comes next.</p><button onClick={() => setGuide(true)}>Meet your models <Icon name="arrow" size={16}/></button></div>
      <div className="sidebar-bottom"><button className="nav-item" onClick={() => setGuide(true)}><Icon name="book"/><span>How it works</span><Icon name="chevron" size={15}/></button><div className="sidebar-profile"><span className="profile-avatar">ME</span><span><strong>Personal workspace</strong><small>Your market, your perspective</small></span><span className="profile-dot"/></div></div>
    </aside>

    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" onClick={() => setSidebar(true)} aria-label="Open navigation"><Icon name="menu"/></button><span>Workspace</span><Icon name="chevron" size={13}/><strong>{NAVIGATION.find(item => item.id === view)?.label}</strong></div><StockSearch onSelect={selectStock}/><button className="topbar-help icon-button" onClick={() => setGuide(true)} aria-label="Open market guide"><Icon name="book"/></button></header>
      <main>
        <section className="page-heading"><div><div className="eyebrow">YOUR MARKET. IN PERSPECTIVE.</div><h1>{view === 'watchlist' ? 'Your watchlist' : view === 'history' ? 'The story behind the price' : 'A sharper view of the market'}<span className="heading-dot">.</span></h1><p>{view === 'watchlist' ? 'The companies you care about, all in one place.' : view === 'history' ? 'Explore daily prices and take the data with you.' : 'Follow your favorites. Discover patterns. Look ahead.'}</p></div><div className="heading-actions"><span className={`connection-badge ${status === 'Connected' ? 'connected' : status === 'Connecting' ? 'pending' : 'offline'}`}><span/>{status}</span><button className="secondary-button refresh-button" aria-label="Refresh market data" disabled={market.loading} onClick={() => setRefresh(value => value + 1)}><Icon name="refresh" size={16} className={market.loading ? 'spinning' : ''}/><span>Refresh</span></button></div></section>

        {market.errors.length > 0 && view !== 'watchlist' && <div className="error-banner" role="alert"><Icon name="info" size={19}/><div><strong>{available ? 'Some market data is unavailable' : 'Let’s reconnect to the market'}</strong><p>{market.errors.join(' ')}</p></div><button onClick={() => setRefresh(value => value + 1)} disabled={market.loading}>Retry <Icon name="refresh" size={14}/></button></div>}

        {view === 'watchlist' ? <section className="panel full-watchlist"><div className="panel-header"><div><h2>On your radar <span className="count-badge">{watchlist.length}</span></h2><p>Search thousands of companies and save as many as you like.</p></div><button className="secondary-button" onClick={() => document.querySelector('[aria-label="Search stocks"]')?.focus()}><Icon name="plus" size={16}/>Add stock</button></div><WatchlistRows detailed watchlist={watchlist} selected={selected} selectedQuote={market.quote} watchQuotes={watchQuotes} onSelect={selectStock} onToggle={toggleWatchlist}/></section> : <>
          <div className="market-stats">
            <div className="stat-card"><div className="stat-label">Latest price <Icon name="trend" size={16}/></div><div className="stat-value">{money(currentPrice, stock.currency)}<Change percent={dayPercent} className="stat-change"/></div><span className="stat-footnote">{stock.symbol} · {market.quote ? 'Latest available quote' : 'Last recorded close'}</span></div>
            <div className="stat-card"><div className="stat-label">Trading range <Icon name="chart" size={16}/></div><div className="stat-value range-value">{money(latest?.Low, stock.currency)} <span>—</span> {money(latest?.High, stock.currency)}</div><span className="stat-footnote">{latest ? `${formatDate(latest.Date)} · Daily low & high` : 'Latest trading session'}</span></div>
            <div className="stat-card"><div className="stat-label">Trading volume <Icon name="grid" size={16}/></div><div className="stat-value">{latest ? new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 2 }).format(latest.Volume) : '—'}<span className="stat-unit">shares</span></div><span className="stat-footnote">{latest ? `${formatDate(latest.Date)} · Reported volume` : 'Latest trading session'}</span></div>
          </div>

          <div className="dashboard-grid"><div className="primary-column">
            <section className="panel price-panel" aria-busy={market.loading}>
              <div className="stock-heading"><div className="stock-identity"><CompanyMark stock={stock}/><div><h2>{stock.name}</h2><div className="stock-subtitle">{stock.symbol}<span>·</span><span className="market-pill">{stock.market}</span><span>·</span>{stock.sector}</div></div></div><button className={`icon-button save-stock ${saved ? 'saved' : ''}`} aria-label={`${saved ? 'Remove' : 'Add'} ${stock.name} ${saved ? 'from' : 'to'} watchlist`} aria-pressed={saved} onClick={() => toggleWatchlist(selected)}><Icon name="star" size={21}/></button></div>
              <div className="chart-heading"><div><span className="chart-price">{money(latest?.Close, stock.currency)}</span><div className="chart-change-line"><Change percent={periodPercent}/><span>over selected period</span></div></div><div className="range-selector" aria-label="Chart date range">{['1M', '3M', '6M', '1Y', 'ALL'].map(item => <button key={item} className={range === item ? 'active' : ''} aria-pressed={range === item} onClick={() => setRange(item)}>{item}</button>)}</div></div>
              <PriceChart history={visibleHistory} currency={stock.currency} loading={market.loading}/>
              <div className="chart-footer"><span><i/>Closing price <span className="currency-label">· {stock.currency}</span></span><span><Icon name="clock" size={13}/>{latest ? `Latest session ${formatDate(latest.Date, { year: 'numeric' })}` : 'Waiting for price history'}</span></div>
            </section>

            <section className="panel history-panel"><div className="panel-header"><div><h2>Price history</h2><p>{view === 'history' ? `Showing ${Math.min(100, visibleHistory.length)} recent sessions in the selected range` : 'A closer look at the latest trading sessions'}</p></div><button className="secondary-button export-button" disabled={!market.history.length} onClick={() => exportHistory(market.history, stock.symbol)}><Icon name="download" size={16}/>Export CSV</button></div><div className="table-scroll"><table><thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead><tbody>{[...visibleHistory].reverse().slice(0, view === 'history' ? 100 : 5).map(row => <tr key={row.Date}><td>{formatDate(row.Date, { year: 'numeric' })}</td><td>{number(row.Open)}</td><td>{number(row.High)}</td><td>{number(row.Low)}</td><td className="close-cell">{number(row.Close)}</td><td>{number(row.Volume, 0)}</td></tr>)}</tbody></table>{!visibleHistory.length && <div className="table-empty">{market.loading ? 'Loading trading sessions…' : 'No trading sessions available yet.'}</div>}</div><div className="table-footer"><span>Prices in {stock.currency} · Daily interval</span><span>{market.history.length ? `${number(market.history.length, 0)} sessions available` : 'History updates when connected'}</span></div></section>
          </div>

          <div className="secondary-column"><section className="forecast-panel" ref={forecastSection}><div className="forecast-header"><span className="forecast-icon"><Icon name="sparkles" size={20}/></span><span className="lab-pill">MODEL LAB</span></div><h2>A glimpse of<br/> what’s next.</h2><p>Next-session estimates for {stock.symbol}.</p><div className="forecast-model"><div><span className="model-dot statistical"/><span>Statistical model</span><button className="model-info" aria-label="Learn about the statistical model" onClick={() => setGuide(true)}><Icon name="info" size={14}/></button></div><strong>{money(activeForecast.result?.statistical, stock.currency)}</strong><small>{activeForecast.result?.models?.statistical || 'Recent daily returns'}</small></div><div className="forecast-model"><div><span className="model-dot lstm"/><span>LSTM model</span><button className="model-info" aria-label="Learn about the LSTM model" onClick={() => setGuide(true)}><Icon name="info" size={14}/></button></div><strong>{money(activeForecast.result?.lstm, stock.currency)}</strong><small>{activeForecast.result && activeForecast.result.lstm === null ? 'Unavailable on this server' : 'Price sequences'}</small></div>{activeForecast.result && <p className="forecast-note">{activeForecast.result.horizon}{activeForecast.result.asOf && ` · Based on ${activeForecast.result.asOf}`}{activeForecast.result.warnings.map((warning, index) => <span key={index}><br/>{warning}</span>)}</p>}{activeForecast.error && <p className="forecast-error" role="alert">{activeForecast.error}</p>}<button className="primary-button forecast-button" onClick={generateForecast} disabled={market.loading || market.history.length < 65 || activeForecast.loading}><Icon name={activeForecast.loading ? 'refresh' : 'sparkles'} size={17} className={activeForecast.loading ? 'spinning' : ''}/>{activeForecast.loading ? 'Models are thinking…' : activeForecast.result ? 'Regenerate forecast' : 'Generate forecast'}{!activeForecast.loading && <Icon name="arrow" size={16}/>}</button><p className="forecast-note">{activeForecast.loading ? 'This can take a few minutes. You can still explore your chart.' : market.history.length > 0 && market.history.length < 65 ? 'At least 65 trading sessions are needed.' : 'Experimental estimates. Not investment advice.'}</p></section>
            <section className="panel watchlist-panel"><div className="panel-header"><h2>Your watchlist <span className="count-badge">{watchlist.length}</span></h2><button className="icon-button" onClick={() => setView('watchlist')} aria-label="View full watchlist"><Icon name="arrow" size={18}/></button></div><WatchlistRows watchlist={watchlist} selected={selected} selectedQuote={market.quote} watchQuotes={watchQuotes} onSelect={selectStock} onToggle={toggleWatchlist}/><button className="watchlist-add" onClick={() => toggleWatchlist(selected)}><Icon name={saved ? 'check' : 'plus'} size={15}/>{saved ? `${stock.symbol} is on your radar` : `Add ${stock.symbol} to watchlist`}</button></section>
          </div></div>
        </>}
        <footer className="page-footer"><span><span className="footer-brand">folio.</span>A little clarity goes a long way.</span><span><Icon name="globe" size={13}/>Market data may be delayed{market.updated && ` · Updated ${market.updated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}`}</span></footer>
      </main>
    </div>
    {guide && <Guide onClose={() => setGuide(false)}/>}
  </div>
}

export default App
