import { useEffect, useReducer } from 'react'
import { fetchHistory, fetchQuote } from '../lib/api'

const initial = { id: null, history: [], quote: null, loading: true, errors: [], updated: null }
function reducer(state, action) {
  if (action.type === 'start') return { ...initial, id: action.id }
  if (action.type === 'finish') return { ...action.data, id: action.id, loading: false, updated: action.data.history.length || action.data.quote ? new Date() : null }
  return state
}

export default function useMarketData(stock, refresh) {
  const [state, dispatch] = useReducer(reducer, initial)
  useEffect(() => {
    const controller = new AbortController()
    dispatch({ type: 'start', id: stock.id })
    Promise.allSettled([
      fetchHistory(stock, { signal: controller.signal }),
      fetchQuote(stock, { signal: controller.signal }),
    ]).then(([history, quote]) => {
      if (controller.signal.aborted) return
      const errors = []
      if (history.status === 'rejected') errors.push(history.reason.message)
      if (quote.status === 'rejected') errors.push(quote.reason.message)
      dispatch({ type: 'finish', id: stock.id, data: {
        history: history.status === 'fulfilled' ? history.value : [],
        quote: quote.status === 'fulfilled' ? quote.value : null,
        errors: [...new Set(errors)],
      } })
    })
    return () => controller.abort()
  }, [stock, refresh])
  return state.id === stock.id ? state : initial
}
