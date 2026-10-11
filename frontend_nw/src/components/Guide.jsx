import { useEffect, useRef } from 'react'
import Icon from './Icon'

export default function Guide({ onClose }) {
  const dialog = useRef(null)
  useEffect(() => { dialog.current?.showModal() }, [])
  return <dialog className="guide-dialog" ref={dialog} onCancel={onClose} onClick={event => { if (event.target === event.currentTarget) onClose() }}>
    <div className="guide-heading"><span className="eyebrow">A LITTLE CONTEXT</span><button className="icon-button" onClick={onClose} aria-label="Close guide"><Icon name="close"/></button></div>
    <h2>Better insights.<br/>More informed decisions.</h2><p>Explore what happened, then see what your models expect.</p>
    <div className="guide-step"><span>01</span><div><h3>Find a company</h3><p>Search NSE and BSE companies by name, symbol or BSE scrip code, then save them to your watchlist. Filter by exchange and use Show more to browse. You can also enter a ticker such as IRFC.NS or RELIANCE.BO. Indian prices use rupees; US prices use dollars.</p></div></div>
    <div className="guide-step"><span>02</span><div><h3>Read the price history</h3><p>Choose a date range and hover over the chart for individual closing prices. Export the full history as a CSV.</p></div></div>
    <div className="guide-step"><span>03</span><div><h3>Generate a next-session estimate</h3><p>Compare ridge autoregression, weighted momentum, damped Holt trend and technical indicator ridge against a last-close baseline. An ensemble weights their earlier backtest errors and reports accuracy on later sessions. Price signals include RSI, moving averages and volatility. The historical error range is not a guaranteed probability interval. LSTM is optional and uses closing-price sequences when enabled on the server. Available models and the history date are shown with each result.</p></div></div>
    <div className="guide-step"><span>04</span><div><h3>Analyse the stock trend</h3><p>Use Analyse stock trend to combine recent company headlines, P/E versus displayed peers, quarterly earnings, promoter/FII/DII changes and relative market strength. This is a fixed heuristic with explained contributions and source dates. Budget and policy coverage uses company-matched headlines, not full budget documents. Missing, stale or ambiguous evidence reduces coverage; low coverage produces Insufficient evidence.</p></div></div>
    <div className="guide-note"><Icon name="info"/><p>Quotes may be delayed. Forecasts are experimental model estimates, not guaranteed prices. Statistical forecasts need price history. LSTM needs TensorFlow enabled on the backend.</p></div>
    <button className="primary-button guide-done" onClick={onClose}>Got it, let’s explore <Icon name="arrow" size={17}/></button>
  </dialog>
}
