export const POLL_INTERVAL = 120000

// Schedule after completion: slow requests cannot overlap the next refresh.
export function startPolling(task, { signal, document: page = document, window: browser = window,
  setTimer = setTimeout, clearTimer = clearTimeout } = {}) {
  let timer
  let running = false
  let stopped = false
  const available = () => !page.hidden && browser.navigator.onLine !== false
  async function run() {
    if (stopped || signal?.aborted || running) return
    clearTimer(timer)
    if (!available()) return
    running = true
    try { await task() } finally {
      running = false
      if (!stopped && !signal?.aborted && available()) timer = setTimer(run, POLL_INTERVAL)
    }
  }
  function resume() {
    if (available()) void run()
    else clearTimer(timer)
  }
  page.addEventListener('visibilitychange', resume)
  browser.addEventListener('online', resume)
  browser.addEventListener('offline', resume)
  void run()
  return () => {
    stopped = true
    clearTimer(timer)
    page.removeEventListener('visibilitychange', resume)
    browser.removeEventListener('online', resume)
    browser.removeEventListener('offline', resume)
  }
}
