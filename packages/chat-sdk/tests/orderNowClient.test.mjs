import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('../src/orderNowClient.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const { DEFAULT_ORDER_NOW_CONFIG, fetchOrderNowConfig, resolveOrderNowUrl, resolveOrderNowAction } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`
)
const catalog = {
  default_url: 'https://shop.ff.com/',
  rules: Object.values(JSON.parse(readFileSync(new URL('../../../apps/rag-api/app/services/order_now_defaults.json', import.meta.url), 'utf8'))),
}
const rule = (pattern, target_url, enabled = true) => ({ id: pattern, label: pattern, pattern, target_url, enabled })
const config = {
  default_url: 'https://shop.ff.com/',
  rules: [
    rule('https://www.ff.com/*', 'https://shop.ff.com/all'),
    rule('https://www.ff.com/us/*', 'https://shop.ff.com/us'),
    rule('https://www.ff.com/us/navi', 'https://shop.ff.com/products/fx-navi'),
    rule('https://futurist.ff.com/us', 'https://shop.ff.com/products/ff-all-new-futurist'),
    rule('https://www.ff.com/disabled', 'https://shop.ff.com/disabled', false),
  ],
}

test('provided product pages, normalization, exact and longest-prefix precedence', () => {
  assert.equal(resolveOrderNowUrl(config, 'https://futurist.ff.com/us/'), 'https://shop.ff.com/products/ff-all-new-futurist')
  assert.equal(resolveOrderNowUrl(config, 'https://WWW.FF.COM/us/navi/?utm_source=test#details'), 'https://shop.ff.com/products/fx-navi')
  assert.equal(resolveOrderNowUrl(config, 'https://www.ff.com/us/navi/details'), 'https://shop.ff.com/us')
  assert.equal(resolveOrderNowUrl(config, 'https://www.ff.com/'), 'https://shop.ff.com/all')
  assert.equal(resolveOrderNowUrl(config, 'https://www.ff.com/usa'), 'https://shop.ff.com/all')
  assert.equal(resolveOrderNowUrl(config, 'https://www.ff.com/disabled'), 'https://shop.ff.com/all')
})

test('unmatched pages, disabled/invalid rules and missing config use the shop fallback', () => {
  for (const url of ['https://other.ff.com/us/navi', 'https://www.ff.com.evil.test/us/navi', 'invalid', 'javascript:alert(1)']) {
    assert.equal(resolveOrderNowUrl(config, url), 'https://shop.ff.com/')
  }
  assert.equal(resolveOrderNowUrl(DEFAULT_ORDER_NOW_CONFIG, 'https://www.ff.com/us/navi'), 'https://shop.ff.com/')
  assert.equal(resolveOrderNowUrl({ default_url: 'javascript:alert(1)', rules: [rule('https://www.ff.com/', 'javascript:alert(1)')] }, 'https://www.ff.com/'), 'https://shop.ff.com/')
})

test('all ten products and thirteen source URLs have the requested targets and button text', () => {
  const expected = [
    [['https://futurist.ff.com/us/', 'https://www.ff.com/us/futurist/'], 'https://shop.ff.com/products/ff-all-new-futurist', 'Order Now'],
    [['https://robotics.ff.com/us/ff-master/'], 'https://shop.ff.com/products/master', 'Order Now'],
    [['https://robotics.ff.com/us/ff-master-mini/'], 'https://shop.ff.com/products/ff-master-mini', 'Order Now'],
    [['https://robotics.ff.com/us/fx-aegis/'], 'https://shop.ff.com/products/aegis', 'Order Now'],
    [['https://robotics.ff.com/us/fx-aegis-mega/'], 'https://shop.ff.com/products/fx-aegis-mega', 'Order Now'],
    [['https://robotics.ff.com/us/fx-aegis-hyper/'], 'https://shop.ff.com/products/fx-aegis-hyper', 'Order Now'],
    [['https://www.ff.com/us/navi/', 'https://navi.ff.com/'], 'https://shop.ff.com/products/fx-navi', 'Order Now'],
    [['https://robotics.ff.com/us/nova/'], 'https://developer.ff.com/onboarding/en/nova', 'Apply Now'],
    [['https://robotics.ff.com/us/nova-mini/'], 'https://shop.ff.com/products/ff-nova-mini', 'Order Now'],
    [['https://faber.ff.com/us/', 'https://www.ff.com/us/faber/'], 'https://www.ff.com/#eai-robotics-contact-us', 'Contact Sales'],
  ]
  assert.equal(catalog.rules.length, 13)
  for (const [sources, url, label] of expected) {
    for (const source of sources) {
      assert.deepEqual(resolveOrderNowAction(catalog, source), { url, label })
      assert.deepEqual(resolveOrderNowAction(catalog, `${source}?campaign=test#details`), { url, label })
    }
  }
  assert.deepEqual(resolveOrderNowAction(catalog, 'https://unconfigured.example/'), { url: 'https://shop.ff.com/', label: 'Order Now' })
  const disabled = { ...catalog, rules: catalog.rules.map(rule => ({ ...rule, enabled: false })) }
  assert.deepEqual(resolveOrderNowAction(disabled, 'https://robotics.ff.com/us/nova/'), { url: 'https://shop.ff.com/', label: 'Order Now' })
})

test('concurrent and later loads share one request; navigation resolves from cached rules', async () => {
  const originalFetch = globalThis.fetch
  let calls = 0
  let finish
  globalThis.fetch = async (_url, options) => {
    calls++
    assert.equal(options.cache, 'no-store')
    return new Promise(resolve => { finish = () => resolve(Response.json(config)) })
  }
  try {
    const first = fetchOrderNowConfig('https://api.test/config')
    const second = fetchOrderNowConfig('https://api.test/config')
    assert.equal(first, second)
    finish()
    const cached = await first
    assert.equal(resolveOrderNowUrl(cached, 'https://www.ff.com/us/navi'), 'https://shop.ff.com/products/fx-navi')
    assert.equal(resolveOrderNowUrl(cached, 'https://futurist.ff.com/us'), 'https://shop.ff.com/products/ff-all-new-futurist')
    assert.equal(await fetchOrderNowConfig('https://api.test/config'), cached)
    assert.equal(calls, 1)
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('network, HTTP and malformed responses fall back and remain cached', async () => {
  const originalFetch = globalThis.fetch
  try {
    for (const [index, response] of [
      () => { throw new Error('offline') },
      () => new Response('', { status: 500 }),
      () => Response.json({ rules: null }),
    ].entries()) {
      let calls = 0
      globalThis.fetch = async () => { calls++; return response() }
      const url = `https://api.test/failure-${index}`
      assert.deepEqual(await fetchOrderNowConfig(url), DEFAULT_ORDER_NOW_CONFIG)
      assert.deepEqual(await fetchOrderNowConfig(url), DEFAULT_ORDER_NOW_CONFIG)
      assert.equal(calls, 1)
    }
    globalThis.fetch = async () => Response.json({ default_url: 'javascript:alert(1)', rules: [null, {}, rule('https://www.ff.com/', 'javascript:alert(1)'), {...rule('https://www.ff.com/', 'https://shop.ff.com/'), button_label: 123}] })
    assert.deepEqual(await fetchOrderNowConfig('https://api.test/unsafe'), DEFAULT_ORDER_NOW_CONFIG)
  } finally {
    globalThis.fetch = originalFetch
  }
})
