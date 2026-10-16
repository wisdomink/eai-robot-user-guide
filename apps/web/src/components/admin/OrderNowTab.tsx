import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  deleteOrderNowRule,
  fetchOrderNowRules,
  saveOrderNowRule,
  type OrderNowRule,
  type OrderNowRulePayload,
} from '@/api/orderNow'

const EMPTY_FORM: OrderNowRulePayload = { label: '', pattern: '', target_url: '', button_label: 'Order Now', enabled: true }

export default function OrderNowTab() {
  const [rows, setRows] = useState<OrderNowRule[]>([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const config = await fetchOrderNowRules()
      setRows(config.rules)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载 Order Now 配置失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const persistRule = async (payload: OrderNowRulePayload, resetForm = false) => {
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      const { rule, created } = await saveOrderNowRule(payload)
      setRows(prev => [...prev.filter(row => row.id !== rule.id), rule]
        .sort((a, b) => a.pattern.localeCompare(b.pattern)))
      if (resetForm) setForm(EMPTY_FORM)
      else if (form.id === rule.id) setForm(rule)
      setSuccess(created ? '规则已新增，刷新宿主页面后生效。' : '规则已更新，刷新宿主页面后生效。')
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setBusy(false)
    }
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    void persistRule(form, true)
  }

  const handleDelete = async (rule: OrderNowRule) => {
    if (!window.confirm(`确认删除 Order Now 规则「${rule.label}」吗？`)) return
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      await deleteOrderNowRule(rule.id)
      setRows(prev => prev.filter(row => row.id !== rule.id))
      if (form.id === rule.id) setForm(EMPTY_FORM)
      setSuccess('规则已删除，刷新宿主页面后生效。')
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="reco-card">
        <div className="recommendation-page-head">
          <div>
            <h1>Order Now 配置</h1>
            <p>按宿主页面 URL 显示入口文字并跳转目标页，使用新标签页打开。未匹配时显示 Order Now，前往 https://shop.ff.com/。</p>
            <p>精确匹配优先，其次最长路径前缀（/*）；忽略查询参数、# 和末尾 /。保存后刷新宿主页面生效。</p>
          </div>
        </div>
        <h2>{form.id ? '编辑规则' : '新增规则'}</h2>
        <form className="recommendation-form" onSubmit={handleSubmit}>
          <label>
            配置名称
            <input
              value={form.label}
              onChange={event => setForm(prev => ({ ...prev, label: event.target.value }))}
              placeholder="例如：FX Navi"
              maxLength={200}
              required
            />
          </label>
          <label>
            按钮文字
            <input
              value={form.button_label}
              onChange={event => setForm(prev => ({ ...prev, button_label: event.target.value }))}
              placeholder="Order Now / Apply Now / Contact Sales"
              maxLength={40}
              required
            />
          </label>
          <label className="recommendation-toggle">
            <span>启用状态</span>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={event => setForm(prev => ({ ...prev, enabled: event.target.checked }))}
            />
          </label>
          <label className="recommendation-form-full">
            来源 URL 匹配规则
            <input
              type="url"
              value={form.pattern}
              onChange={event => setForm(prev => ({ ...prev, pattern: event.target.value }))}
              placeholder="https://www.ff.com/us/navi/ 或 https://www.ff.com/us/navi/*"
              maxLength={2048}
              required
            />
          </label>
          <label className="recommendation-form-full">
            目标 URL
            <input
              type="url"
              value={form.target_url}
              onChange={event => setForm(prev => ({ ...prev, target_url: event.target.value }))}
              placeholder="https://shop.ff.com/products/fx-navi"
              maxLength={2048}
              required
            />
          </label>
          <div className="recommendation-form-actions">
            <button type="submit" disabled={busy || loading}>{busy ? '处理中…' : '保存规则'}</button>
            {form.id && (
              <button type="button" className="recommendation-secondary-btn" disabled={busy} onClick={() => setForm(EMPTY_FORM)}>
                取消编辑
              </button>
            )}
          </div>
        </form>
        {success && <p className="lead-msg success" role="status">{success}</p>}
        {error && <p className="lead-msg error" role="alert">{error}</p>}
      </section>

      <section className="reco-card">
        <div className="lead-table-header">
          <h2>已保存规则</h2>
          <button type="button" onClick={load} disabled={busy || loading}>{loading ? '刷新中…' : '刷新'}</button>
        </div>
        <div className="lead-table-wrap">
          <table className="lead-table">
            <thead><tr><th>名称</th><th>来源 URL</th><th>按钮文字</th><th>目标 URL</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {rows.map(rule => (
                <tr key={rule.id}>
                  <td>{rule.label}</td><td>{rule.pattern}</td><td>{rule.button_label}</td><td>{rule.target_url}</td>
                  <td>{rule.enabled ? '启用' : '停用'}</td>
                  <td>
                    <div className="recommendation-row-actions">
                      <button type="button" disabled={busy || loading} onClick={() => { setForm(rule); setError(null); setSuccess(null) }}>编辑</button>
                      <button type="button" disabled={busy || loading} onClick={() => persistRule({ ...rule, enabled: !rule.enabled })}>
                        {rule.enabled ? '停用' : '启用'}
                      </button>
                      <button type="button" className="recommendation-danger-btn" disabled={busy || loading} onClick={() => handleDelete(rule)}>删除</button>
                    </div>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={6}>{loading ? '加载中…' : '暂无规则，所有页面默认跳转商城首页。'}</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
