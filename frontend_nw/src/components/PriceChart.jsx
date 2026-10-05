import { useId, useState } from 'react'
import { formatDate, money, number } from '../lib/stocks'
import useMobile from '../hooks/useMobile'

export default function PriceChart({ history, currency, loading }) {
  const gradientId = useId()
  const [hover, setHover] = useState(null)
  const mobile = useMobile()
  const width = mobile ? 640 : 1000, height = 310
  const fontSize = mobile ? 18 : 16
  const padding = { left: 8, right: mobile ? 90 : 100, top: 24, bottom: 38 }
  const values = history.map(row => row.Close)
  const minimum = Math.min(...values), maximum = Math.max(...values)
  const buffer = Math.max((maximum - minimum) * .2, maximum * .008, 1)
  const low = minimum - buffer, high = maximum + buffer
  const plotWidth = width - padding.left - padding.right
  const plotHeight = height - padding.top - padding.bottom
  const x = index => padding.left + index / Math.max(1, history.length - 1) * plotWidth
  const y = value => padding.top + (high - value) / (high - low) * plotHeight
  const line = history.map((row, index) => `${index ? 'L' : 'M'}${x(index).toFixed(2)},${y(row.Close).toFixed(2)}`).join(' ')
  const area = `${line} L${x(history.length - 1)},${height - padding.bottom} L${padding.left},${height - padding.bottom} Z`
  const activeIndex = hover == null ? null : Math.min(hover, history.length - 1)
  const active = activeIndex == null ? null : history[activeIndex]
  if (!history.length) return <div className={`chart-empty ${loading ? 'loading' : ''}`}>
    <div className="chart-grid-placeholder"/>
    <div><span className="empty-chart-icon">↗</span><strong>{loading ? 'Connecting the dots…' : 'A clearer view of the market'}</strong><p>{loading ? 'Fetching the latest available price history.' : 'Price history will appear here once the data service is connected.'}</p></div>
  </div>
  return <div className="chart-container">
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Closing prices from ${formatDate(history[0].Date, { year: 'numeric' })} to ${formatDate(history.at(-1).Date, { year: 'numeric' })}. Last closing price ${money(history.at(-1).Close, currency)}.`}
      onPointerMove={event => {
        const rect = event.currentTarget.getBoundingClientRect()
        const position = (event.clientX - rect.left) / rect.width * width
        setHover(Math.round(Math.max(0, Math.min(1, (position - padding.left) / plotWidth)) * (history.length - 1)))
      }} onPointerLeave={() => setHover(null)}>
      <defs><linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#25a27c" stopOpacity=".2"/><stop offset="100%" stopColor="#25a27c" stopOpacity=".005"/></linearGradient></defs>
      {[0, 1, 2, 3, 4].map(index => {
        const value = high - index / 4 * (high - low), position = y(value)
        return <g key={index}><line x1={padding.left} x2={width - padding.right} y1={position} y2={position} stroke="#e8edec" strokeDasharray="4 5"/><text x={width - padding.right + 16} y={position + 4} fill="#8a9499" fontSize={fontSize}>{number(value, 0)}</text></g>
      })}
      <path d={area} fill={`url(#${gradientId})`}/><path d={line} fill="none" stroke="#239c77" strokeWidth="2.5" strokeLinejoin="round"/>
      {[0, 1, 2, 3, 4].map(index => { const i = Math.round(index / 4 * (history.length - 1)); return <text key={index} x={x(i)} y={height - 8} textAnchor={index === 0 ? 'start' : index === 4 ? 'end' : 'middle'} fill="#8a9499" fontSize={fontSize}>{formatDate(history[i].Date, { year: history.length > 260 ? '2-digit' : undefined })}</text> })}
      <circle cx={x(history.length - 1)} cy={y(history.at(-1).Close)} r="4" fill="#239c77" stroke="white" strokeWidth="2"/>
      {active && <g><line x1={x(activeIndex)} x2={x(activeIndex)} y1={padding.top} y2={height - padding.bottom} stroke="#8ebbae" strokeDasharray="4 4"/><circle cx={x(activeIndex)} cy={y(active.Close)} r="5" fill="#239c77" stroke="white" strokeWidth="2"/></g>}
    </svg>
    {active && <div className="chart-tooltip" style={{ left: `${Math.max(14, Math.min(80, x(activeIndex) / width * 100))}%` }}><small>{formatDate(active.Date, { year: 'numeric' })}</small><strong>{money(active.Close, currency)}</strong><span>Closing price</span></div>}
  </div>
}
