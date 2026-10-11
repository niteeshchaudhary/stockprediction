import { useEffect, useRef, useState } from 'react'
import StockSearch from './StockSearch'
import Icon from './Icon'
import { getStock } from '../lib/stocks'

export default function WatchlistPicker({ watchlist, onAdd, onClose }) {
  const dialog = useRef(null)
  const [message, setMessage] = useState('')
  useEffect(() => { dialog.current?.showModal() }, [])
  function add(id) {
    const stock = getStock(id)
    if (!stock) return
    onAdd(stock.id)
    setMessage(watchlist.includes(stock.id) ? `${stock.symbol} is already in your watchlist.` : `${stock.symbol} added to your watchlist.`)
  }
  return <dialog className="guide-dialog watchlist-picker" ref={dialog} onCancel={onClose} onClick={event => { if (event.target === event.currentTarget) onClose() }}>
    <div className="guide-heading"><span className="eyebrow">YOUR WATCHLIST</span><button className="icon-button" onClick={onClose} aria-label="Close add stocks"><Icon name="close"/></button></div>
    <h2>Add stocks</h2>
    <p>Search for a company, then select it to save it directly to your watchlist.</p>
    <StockSearch onSelect={add} action="add"/>
    <p role="status" className="watchlist-feedback">{message || 'You can add multiple stocks here.'}</p>
    <button className="primary-button" onClick={onClose}>Done <Icon name="check" size={17}/></button>
  </dialog>
}
