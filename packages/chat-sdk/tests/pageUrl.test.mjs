import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('../src/pageUrl.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const { getPageUrl, subscribeToPageUrl } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)

test('SPA push, replace, back/forward and hash changes notify shared subscribers and clean up', () => {
  const originalWindow = globalThis.window
  const location = { href: 'https://robotics.ff.com/us/nova/' }
  const history = {
    pushState(_data, _unused, url) {
      assert.equal(this, history)
      location.href = new URL(url, location.href).href
    },
    replaceState(_data, _unused, url) {
      assert.equal(this, history)
      location.href = new URL(url, location.href).href
    },
  }
  globalThis.window = Object.assign(new EventTarget(), { location, history })
  const originalPush = history.pushState
  const originalReplace = history.replaceState
  const seen = []
  const stopFirst = subscribeToPageUrl(() => seen.push(getPageUrl()))
  const second = []
  const stopSecond = subscribeToPageUrl(() => second.push(getPageUrl()))
  try {
    history.pushState({}, '', '/us/fx-aegis/')
    history.replaceState({}, '', '/us/nova-mini/')
    window.dispatchEvent(new Event('popstate'))
    window.dispatchEvent(new Event('hashchange'))
    assert.deepEqual(seen, [
      'https://robotics.ff.com/us/fx-aegis/',
      'https://robotics.ff.com/us/nova-mini/',
      'https://robotics.ff.com/us/nova-mini/',
      'https://robotics.ff.com/us/nova-mini/',
    ])
    assert.deepEqual(second, seen)
    stopFirst()
    history.pushState({}, '', '/us/nova/')
    assert.equal(seen.length, 4)
    assert.equal(second.length, 5)
    stopSecond()
    assert.equal(history.pushState, originalPush)
    assert.equal(history.replaceState, originalReplace)
  } finally {
    stopFirst()
    stopSecond()
    if (originalWindow === undefined) delete globalThis.window
    else globalThis.window = originalWindow
  }
})
