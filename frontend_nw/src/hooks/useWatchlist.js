import { useEffect, useReducer } from 'react'
import { fetchQuote } from '../lib/api'
import { getStock } from '../lib/stocks'
import { startPolling } from '../lib/polling'

function reducer(state, action) {
  return { ...state, [action.id]: { ...state[action.id], ...action.quote } }
}

export default function useWatchlist(ids, refresh, selected) {
  const [quotes, dispatch] = useReducer(reducer, {})
  useEffect(() => {
    const controller = new AbortController()
    // Two workers keep a larger watchlist from flooding the data provider.
    const stop = startPolling(async () => {
      const pending = ids.filter(id => id !== selected)
      async function worker() {
        while (pending.length && !controller.signal.aborted) {
          const id = pending.shift()
          const stock = getStock(id)
          try {
            const quote = await fetchQuote(stock, { signal: controller.signal })
            if (!controller.signal.aborted) dispatch({ id, quote: { ...quote, unavailable: false } })
          } catch {
            if (!controller.signal.aborted) dispatch({ id, quote: { unavailable: true } })
          }
        }
      }
      await Promise.all([worker(), worker()])
    }, { signal: controller.signal })
    return () => { stop(); controller.abort() }
  }, [ids, refresh, selected])
  return quotes
}
