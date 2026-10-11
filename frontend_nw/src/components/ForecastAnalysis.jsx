import { money } from '../lib/stocks'

export default function ForecastAnalysis({ analysis, currency }) {
  if (!analysis) return null
  const indicators = analysis.indicators
  return <div className="forecast-analysis">
    <h3>Backtested ensemble</h3>
    <strong className="ensemble-price">{money(analysis.price, currency)}</strong>
    <p>{money(analysis.error_range.low, currency)} – {money(analysis.error_range.high, currency)}<br/><small>Historical error range · not a confidence guarantee</small></p>
    <p>Tested on {analysis.evaluation_sessions} later sessions after fitting weights on {analysis.weight_fit_sessions} earlier sessions.</p>
    <div className="model-comparison"><table><thead><tr><th>Model</th><th>Next close</th><th>Avg. error</th></tr></thead><tbody>{analysis.models.map(model => <tr key={model.id}><td>{model.name}<small>{(model.weight * 100).toFixed(0)}% ensemble weight</small></td><td>{money(model.price, currency)}</td><td>{model.mape.toFixed(2)}%</td></tr>)}</tbody></table></div>
    <p>Ensemble avg. error: {analysis.mape.toFixed(2)}% · Direction accuracy: {analysis.direction_accuracy.toFixed(0)}%</p>
    <p className="benchmark-result">{analysis.beats_baseline ? 'Lower recent error than the last-close baseline.' : 'No improvement over the last-close baseline in this evaluation.'}</p>
    <h3>Price signals</h3>
    <p>RSI (14): {indicators.rsi14.toFixed(1)} · {indicators.rsi14 >= 70 ? 'Elevated momentum' : indicators.rsi14 <= 30 ? 'Weak momentum' : 'Mid-range momentum'}<br/>20-session average: {money(indicators.sma20, currency)}<br/>50-session average: {money(indicators.sma50, currency)}<br/>Annualized volatility: {indicators.annualized_volatility.toFixed(1)}%</p>
    <p>{analysis.scope}</p>
  </div>
}
