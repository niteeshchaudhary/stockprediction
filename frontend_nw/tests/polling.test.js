import { test } from 'node:test'
import assert from 'node:assert/strict'
import { startPolling, POLL_INTERVAL } from '../src/lib/polling.js'

test('polling waits for completion, pauses hidden/offline, resumes and cleans up', async () => {
  const page = new EventTarget()
  const browser = new EventTarget()
  browser.navigator = { onLine: true }
  page.hidden = false
  let calls = 0
  let complete
  let scheduled
  const stop = startPolling(() => { calls++; return new Promise(resolve => { complete = resolve }) }, {
    document: page, window: browser,
    setTimer: (callback, delay) => { assert.equal(delay, POLL_INTERVAL); scheduled = callback; return 1 },
    clearTimer: () => { scheduled = null },
  })
  assert.equal(calls, 1)
  browser.dispatchEvent(new Event('online'))
  assert.equal(calls, 1)
  assert.equal(scheduled, null)
  complete()
  await Promise.resolve()
  assert.equal(typeof scheduled, 'function')
  page.hidden = true
  page.dispatchEvent(new Event('visibilitychange'))
  assert.equal(scheduled, null)
  page.hidden = false
  page.dispatchEvent(new Event('visibilitychange'))
  assert.equal(calls, 2)
  browser.navigator.onLine = false
  complete()
  await Promise.resolve()
  assert.equal(scheduled, null)
  browser.navigator.onLine = true
  browser.dispatchEvent(new Event('online'))
  assert.equal(calls, 3)
  stop()
  complete()
  await Promise.resolve()
  browser.dispatchEvent(new Event('online'))
  assert.equal(calls, 3)
  assert.equal(scheduled, null)
})
