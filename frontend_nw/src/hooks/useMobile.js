import { useSyncExternalStore } from 'react'

const QUERY = '(max-width: 760px)'
function subscribe(callback) {
  const media = window.matchMedia(QUERY)
  media.addEventListener('change', callback)
  return () => media.removeEventListener('change', callback)
}
function snapshot() { return window.matchMedia(QUERY).matches }

export default function useMobile() {
  return useSyncExternalStore(subscribe, snapshot, () => false)
}
