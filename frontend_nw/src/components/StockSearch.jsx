import { useRef, useState, useEffect } from 'react'
import { STOCKS, searchStocks, stockFromTicker } from '../lib/stocks'
import Icon from './Icon'

export function CompanyMark({ stock, small = false }) {
  return <span className={`company-mark ${small ? 'small' : ''}`} style={{ '--company-color': stock.color }}>{stock.initials}</span>
}

export default function StockSearch({ onSelect }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const input = useRef(null)
  const container = useRef(null)
  const matches = searchStocks(query)
  const custom = query.trim() && (!matches.length || /\.(NS|BO)$/i.test(query.trim())) ? stockFromTicker(query) : null
  if (custom && !matches.some(stock => stock.id === custom.id)) matches.push(custom)
  useEffect(() => {
    function keydown(event) {
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()
        input.current?.focus()
      }
      if (event.key === 'Escape') setOpen(false)
    }
    function outside(event) { if (!container.current?.contains(event.target)) setOpen(false) }
    document.addEventListener('keydown', keydown)
    document.addEventListener('pointerdown', outside)
    return () => {
      document.removeEventListener('keydown', keydown)
      document.removeEventListener('pointerdown', outside)
    }
  }, [])
  function select(stock) {
    onSelect(stock.id)
    setOpen(false)
    setQuery('')
    input.current?.blur()
  }
  return <div className="stock-search" ref={container}>
    <Icon name="search" size={18}/>
    <input ref={input} value={query} onFocus={() => setOpen(true)} onChange={event => { setQuery(event.target.value); setOpen(true); setActive(0) }}
      placeholder="Search companies or symbols" aria-label="Search stocks" role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls="stock-results"
      aria-activedescendant={open && matches.length ? `stock-result-${active}` : undefined}
      onKeyDown={event => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); setOpen(true); setActive(index => Math.max(0, Math.min(matches.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))) }
        if (event.key === 'Enter' && open && matches[active]) { event.preventDefault(); select(matches[active]) }
        if (event.key === 'Tab') setOpen(false)
      }}/>
    <kbd>Ctrl K</kbd>
    {open && <div className="search-results" id="stock-results" role="listbox" aria-label="Companies">
      <div className="search-caption">{STOCKS.length.toLocaleString('en-IN')} COMPANIES · SEARCH OR ENTER A TICKER</div>
      {matches.length ? matches.map((stock, index) => <button key={stock.id} id={`stock-result-${index}`} type="button" role="option" aria-selected={index === active} className={index === active ? 'highlighted' : ''} onMouseEnter={() => setActive(index)} onClick={() => select(stock)} tabIndex={-1}>
        <CompanyMark stock={stock} small/><span><strong>{stock.name}</strong><small>{stock.symbol} · {stock.market}{stock.sector === 'Custom ticker' ? ' · Use this ticker' : ''}</small></span><Icon name="arrow" size={16}/>
      </button>) : <p className="search-empty">Try a company name, or a ticker such as NVDA, IRFC.NS or 500325.BO.</p>}
    </div>}
  </div>
}
