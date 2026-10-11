import { getStock } from './stocks.js'

export function addToWatchlist(items, id) {
  const stock = getStock(id)
  if (!stock || items.includes(stock.id)) return items
  return [...items, stock.id]
}
