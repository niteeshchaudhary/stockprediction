import { useEffect, useReducer, useRef } from 'react'
import Icon from './Icon'
import { fetchTrend } from '../lib/api'

const initial = { id: null, loading: false, result: null, error: null }
function reducer(_state, action) { return action }
function value(number, suffix = '') { return Number.isFinite(number) ? `${number.toFixed(2)}${suffix}` : 'Unavailable' }
function date(stamp) { return stamp ? new Date(stamp).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Unavailable' }

function Headlines({ title, articles }) {
  return <div className="trend-headlines"><h3>{title}</h3>{articles.length ? <ul>{articles.slice(0, 6).map(item => <li key={item.url}><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a><small>{item.publisher} · {date(item.published_at)} · {item.signal > 0 ? 'Positive phrase' : item.signal < 0 ? 'Negative phrase' : 'Unclassified'}</small></li>)}</ul> : <p>No recent company-matched headlines available.</p>}</div>
}

export default function TrendAnalysis({ stock }) {
  const [state, dispatch] = useReducer(reducer, initial)
  const controller = useRef(null)
  useEffect(() => () => controller.current?.abort(), [stock.id])
  const active = state.id === stock.id ? state : initial
  async function analyse() {
    controller.current?.abort()
    const next = new AbortController()
    controller.current = next
    dispatch({ id: stock.id, loading: true, result: null, error: null })
    try {
      const result = await fetchTrend(stock, { signal: next.signal })
      if (!next.signal.aborted) dispatch({ id: stock.id, loading: false, result, error: null })
    } catch (error) {
      if (!next.signal.aborted) dispatch({ id: stock.id, loading: false, result: null, error: error.message })
    }
  }
  const result = active.result
  const financial = result?.fundamentals
  return <section className="panel trend-panel" aria-busy={active.loading}>
    <div className="panel-header"><div><h2>Stock trend intelligence</h2><p>One explained score combining company news, market signals, valuation and ownership.</p></div><button className="primary-button" onClick={analyse} disabled={active.loading}><Icon name={active.loading ? 'refresh' : 'sparkles'} size={17} className={active.loading ? 'spinning' : ''}/>{active.loading ? 'Checking sources…' : result ? 'Update trend analysis' : 'Analyse stock trend'}</button></div>
    <div className="trend-body">
      {!result && !active.loading && !active.error && <p>Analyse {stock.symbol} with free public sources. Available inputs and dates appear with the result.</p>}
      {active.loading && <p role="status">Fetching recent headlines, financial results, shareholding and market data. This may take up to a minute.</p>}
      {active.error && <p className="trend-error" role="alert">{active.error}</p>}
      {result && <>
        <div className="trend-summary"><div><span className="eyebrow">{result.algorithm}</span><h3>{result.trend}</h3><p>{result.horizon}</p></div><div><strong>{value(result.score)}<small> / 100</small></strong><p>Evidence score · can be negative</p><span>{result.coverage}% weighted input coverage</span></div></div>
        <p className="trend-date">Analysis fetched {date(result.generated_at)} · Prices through {result.price_as_of}. Refresh analysis to check newer news.</p>
        <div className="trend-factors">{result.factors.map(factor => <div className={`trend-factor ${factor.available ? '' : 'missing'}`} key={factor.id}><div><h3>{factor.name}</h3><strong>{factor.available ? `${factor.contribution > 0 ? '+' : ''}${factor.contribution.toFixed(1)}` : factor.status || 'Unavailable'}</strong></div><p>{factor.reason}</p><small>Maximum weight: {factor.weight} points</small></div>)}</div>
        <div className="trend-evidence">
          <div><h3>Fundamentals & ownership</h3><dl><div><dt>P/E</dt><dd>{value(financial.pe)}</dd></div><div><dt>Peer median P/E</dt><dd>{value(financial.peer_pe)}{financial.peer_count > 0 && ` (${financial.peer_count} peers)`}</dd></div><div><dt>Profit growth YoY</dt><dd>{value(financial.profit_growth_yoy, '%')}</dd></div><div><dt>Sales growth YoY</dt><dd>{value(financial.sales_growth_yoy, '%')}</dd></div><div><dt>ROE / ROCE</dt><dd>{value(financial.roe, '%')} / {value(financial.roce, '%')}</dd></div><div><dt>Promoter holding</dt><dd>{value(financial.promoter_holding, '%')}</dd></div><div><dt>Promoter change</dt><dd>{value(financial.promoter_change_pp, ' pp')}</dd></div><div><dt>FII / DII holding</dt><dd>{value(financial.fii_holding, '%')} / {value(financial.dii_holding, '%')}</dd></div><div><dt>FII / DII change</dt><dd>{value(financial.fii_change_pp, ' pp')} / {value(financial.dii_change_pp, ' pp')}</dd></div><div><dt>Promoter pledging</dt><dd>Unavailable</dd></div></dl><p>Results period: {financial.results_period || 'Unavailable'} · Ownership period: {financial.ownership_period || 'Unavailable'}</p>{financial.source && <p><a href={financial.source} target="_blank" rel="noreferrer">Source: Screener · {financial.basis}</a> · Retrieved {date(financial.fetched_at)}</p>}</div>
          <div><h3>Market signals</h3><dl><div><dt>Stock 20-session return</dt><dd>{value(result.indicators.return20_pct, '%')}</dd></div><div><dt>{result.indicators.benchmark} return</dt><dd>{value(result.indicators.benchmark_return20_pct, '%')}</dd></div><div><dt>Relative strength</dt><dd>{value(result.indicators.relative_return20_pp, ' pp')}</dd></div><div><dt>RSI (14)</dt><dd>{value(result.indicators.rsi14)}</dd></div><div><dt>Latest / average volume</dt><dd>{value(result.indicators.volume_ratio, '×')}</dd></div><div><dt>Annualized volatility</dt><dd>{value(result.indicators.annualized_volatility, '%')}</dd></div></dl><p>Price and benchmark source: Yahoo Finance. Volume and RSI are context signals; they do not directly change the score.</p><p><a href="https://www.indiabudget.gov.in/" target="_blank" rel="noreferrer">Review official Union Budget documents</a></p></div>
        </div>
        <div className="trend-evidence"><div><Headlines title="Recent company news · 7 days" articles={result.news}/><p>Google News RSS · Retrieved {date(result.source_status.news.fetched_at)}</p></div><div><Headlines title="Distinct budget & policy news · 30 days" articles={result.policy_news}/><p>Google News RSS · Retrieved {date(result.source_status.policy.fetched_at)}</p></div></div>
        <ul className="trend-warnings">{result.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>
      </>}
    </div>
  </section>
}
