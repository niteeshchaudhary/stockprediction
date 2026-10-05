import { useEffect, useReducer } from 'react'
import { fetchQuote } from '../lib/api'
import { getStock } from '../lib/stocks'

function reducer(state, action) {
  return { ...state, [action.id]: action.quote }
}

export default function useWatchlist(ids, refresh) {
  const [quotes, dispatch] = useReducer(reducer, {})
  useEffect(() => {
    const controller = new AbortController()
    // Two workers keep a larger watchlist from flooding the data provider.
    const pending = [...ids]
    async function worker() {
      while (pending.length && !controller.signal.aborted) {
        const id = pending.shift()
        const stock = getStock(id)
        try {
          const quote = await fetchQuote(stock, { signal: controller.signal })
          if (!controller.signal.aborted) dispatch({ id, quote })
        } catch {
          if (!controller.signal.aborted) dispatch({ id, quote: null })
        }
      }
    }
    worker()
    worker()
    return () => controller.abort()
  }, [ids, refresh])
  return quotes
}
