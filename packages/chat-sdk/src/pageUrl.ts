const listeners = new Set<() => void>()
let stopListening: (() => void) | undefined

export function getPageUrl(): string {
  return typeof window === 'undefined' ? '' : window.location.href
}

/** Share route notifications across mounts without polling or additional config requests. */
export function subscribeToPageUrl(listener: () => void): () => void {
  listeners.add(listener)
  if (listeners.size === 1) {
    const notify = () => listeners.forEach(callback => callback())
    const history = window.history
    const pushState = history.pushState
    const replaceState = history.replaceState
    const wrappedPush: History['pushState'] = function (this: History, ...args) {
      pushState.apply(this, args)
      notify()
    }
    const wrappedReplace: History['replaceState'] = function (this: History, ...args) {
      replaceState.apply(this, args)
      notify()
    }
    history.pushState = wrappedPush
    history.replaceState = wrappedReplace
    window.addEventListener('popstate', notify)
    window.addEventListener('hashchange', notify)
    stopListening = () => {
      if (history.pushState === wrappedPush) history.pushState = pushState
      if (history.replaceState === wrappedReplace) history.replaceState = replaceState
      window.removeEventListener('popstate', notify)
      window.removeEventListener('hashchange', notify)
    }
  }
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0) {
      stopListening?.()
      stopListening = undefined
    }
  }
}
