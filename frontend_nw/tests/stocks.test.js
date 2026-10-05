import { test } from 'node:test'
import assert from 'node:assert/strict'
import { STOCKS, searchStocks, getStock, stockFromTicker } from '../src/lib/stocks.js'

test('catalogue contains thousands of unique stocks and preserves saved IDs', () => {
  assert.ok(STOCKS.length >= 2600)
  assert.equal(new Set(STOCKS.map(stock => stock.id)).size, STOCKS.length)
  assert.equal(stockFromTicker('TATASTEEL.NS').id, 'tata steel')
})

test('requested companies and common aliases resolve first in search', () => {
  for (const [query, symbol] of [['IRFC', 'IRFC'], ['TATA steel', 'TATASTEEL'], ['CANABANK', 'CANBK'], ['canara bank', 'CANBK'], ['Bajaj housing finace', 'BAJAJHFL'], ['IOB', 'IOB']]) {
    assert.equal(searchStocks(query)[0].symbol, symbol, query)
  }
})

test('custom tickers are stable objects and survive watchlist ID restoration', () => {
  for (const ticker of ['NVDA', '500325.BO', 'UNLISTED.NS']) {
    const stock = stockFromTicker(ticker)
    assert.equal(getStock(stock.id), stock)
    assert.equal(stockFromTicker(ticker.toLowerCase()), stock)
  }
  assert.equal(stockFromTicker('500325.BO').currency, 'INR')
  for (const ticker of ['../secret', 'a/b', 'https://example.com', 'BAD.L', 'canara bank', '']) {
    assert.equal(stockFromTicker(ticker), null)
  }
  assert.equal(getStock(null), null)
})
