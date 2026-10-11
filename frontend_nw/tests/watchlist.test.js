import { test } from 'node:test'
import assert from 'node:assert/strict'
import { addToWatchlist } from '../src/lib/watchlist.js'
import { getStock } from '../src/lib/stocks.js'

test('adding catalogue and custom stocks preserves existing entries', () => {
  const original = ['reliance']
  const withIRFC = addToWatchlist(original, 'IRFC.NS')
  const withCustom = addToWatchlist(withIRFC, 'ticker:NVDA')
  assert.deepEqual(original, ['reliance'])
  assert.deepEqual(withCustom, ['reliance', 'IRFC.NS', 'ticker:NVDA'])
  assert.deepEqual(JSON.parse(JSON.stringify(withCustom)).map(id => getStock(id).id), withCustom)
})

test('adding an existing stock is idempotent and canonicalizes ticker aliases', () => {
  const items = ['tata steel']
  assert.equal(addToWatchlist(items, 'ticker:TATASTEEL.NS'), items)
  assert.equal(addToWatchlist(items, 'tata steel'), items)
  assert.equal(addToWatchlist(items, 'unknown'), items)
})
