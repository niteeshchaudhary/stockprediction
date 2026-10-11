import { useEffect, useReducer } from 'react'
import { fetchHistory, fetchQuote } from '../lib/api'
import { startPolling } from '../lib/polling'

const initial = { id: null, history: [], quote: null, loading: true, refreshing: false, errors: [], updated: null }
function reducer(state, action) {
  if (action.type === 'start') return state.id === action.id ? { ...state, refreshing: true } : { ...initial, id: action.id, refreshing: true }
  if (action.type === 'finish') return { ...state, ...action.data, id: action.id, loading: false, refreshing: false,
    history: action.data.history ?? state.history, quote: action.data.quote ?? state.quote,
    updated: action.data.quote ? new Date() : state.updated }
  return state
}

export default function useMarketData(stock, refresh) {
  const [state, dispatch] = useReducer(reducer, initial)
  useEffect(() => {
    const controller = new AbortController()
    const stop = startPolling(async () => {
      dispatch({ type: 'start', id: stock.id })
      const [history, quote] = await Promise.allSettled([
      fetchHistory(stock, { signal: controller.signal }),
      fetchQuote(stock, { signal: controller.signal }),
      ])
      if (controller.signal.aborted) return
      const errors = []
      if (history.status === 'rejected') errors.push(history.reason.message)
      if (quote.status === 'rejected') errors.push(quote.reason.message)
      dispatch({ type: 'finish', id: stock.id, data: {
        history: history.status === 'fulfilled' ? history.value : null,
        quote: quote.status === 'fulfilled' ? quote.value : null,
        errors: [...new Set(errors)],
      } })
    }, { signal: controller.signal })
    return () => { stop(); controller.abort() }
  }, [stock, refresh])
  return state.id === stock.id ? state : initial
}
