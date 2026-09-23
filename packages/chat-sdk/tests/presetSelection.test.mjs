import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('../src/presetSelection.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const { matchesPresetMessage } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)
const selection = { id: '问题1', scope: 'page:max', text: '怎么开机？' }
const body = (type, text = selection.text) => JSON.stringify({
  type, params: { input: { content: [{ type: 'input_text', text }] } },
})

test('new and existing threads carry the selection only for the selected message', () => {
  assert.equal(matchesPresetMessage(body('threads.create'), selection), true)
  assert.equal(matchesPresetMessage(body('threads.add_user_message'), selection), true)
  assert.equal(matchesPresetMessage(body('threads.add_user_message', '自由输入'), selection), false)
})

test('history, actions and malformed requests cannot consume a pending selection', () => {
  for (const type of ['threads.list', 'threads.get_by_id', 'threads.custom_action', 'threads.retry_after_failure']) {
    assert.equal(matchesPresetMessage(body(type), selection), false)
  }
  for (const value of ['', 'not json', '{}', 'null', JSON.stringify({ type: 'threads.create' })]) {
    assert.equal(matchesPresetMessage(value, selection), false)
  }
})
