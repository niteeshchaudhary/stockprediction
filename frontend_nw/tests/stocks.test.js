import { test } from 'node:test'
import assert from 'node:assert/strict'
import { STOCKS, EXCHANGE_COUNTS, searchStocks, getStock, stockFromTicker } from '../src/lib/stocks.js'

test('catalogue contains thousands of unique stocks and preserves saved IDs', () => {
  assert.ok(STOCKS.length >= 2600)
  assert.equal(new Set(STOCKS.map(stock => stock.id)).size, STOCKS.length)
  assert.equal(stockFromTicker('TATASTEEL.NS').id, 'tata steel')
})

test('both exchange directories can be browsed without a seven-result cap', () => {
  assert.ok(EXCHANGE_COUNTS.BSE > 5000)
  assert.ok(EXCHANGE_COUNTS.NSE > 3000)
  const bse = searchStocks('', Infinity, 'BSE')
  assert.equal(bse.length, EXCHANGE_COUNTS.BSE)
  assert.ok(bse.every(stock => stock.market === 'BSE'))
  assert.equal(searchStocks('500325', 20, 'BSE')[0].symbol, 'RELIANCE')
  assert.equal(stockFromTicker('500325').id, '500325.BO')
  assert.equal(stockFromTicker('500325.BO').ticker, 'RELIANCE.BO')
  assert.equal(stockFromTicker('RELIANCE.BO'), getStock('500325.BO'))
  assert.ok(searchStocks('reliance', 100, 'BSE').every(stock => stock.market === 'BSE'))
  assert.equal(stockFromTicker('NEWLISTING.NS').market, 'NSE')
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
