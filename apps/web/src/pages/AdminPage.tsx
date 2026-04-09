import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import logoDark from '@/assets/icons/logo-dark.svg'
import {
  deleteRecommendation,
  fetchRecommendations,
  saveRecommendation,
  type RecommendationPayload,
  type RecommendationRecord,
} from '@/api/recommendations'
import {
  fetchLeadCaptureTriageConfig,
  saveLeadCaptureTriageConfig,
} from '@/api/leadCaptureConfig'
import { fetchLeads, submitLead, type LeadPayload, type LeadRecord } from '@/api/leads'
import {
  deleteHomepagePrompt,
  fetchHomepagePrompts,
  saveHomepagePrompt,
  saveHomepageSettings,
  type HomepagePrompt,
  type HomepagePromptPayload,
  type HomepageSettings,
} from '@/api/homepagePrompts'

type Tab = 'recommendations' | 'leads' | 'homepage-prompts'

const RECO_PRODUCT_OPTIONS = [
  { value: 'futurist', label: 'FF Futurist' },
  { value: 'futurist-ultra', label: 'FF Futurist Ultra' },
  { value: 'master', label: 'FF Master' },
  { value: 'aegis', label: 'FF Aegis' },
  { value: 'aegis-ultra', label: 'FF Aegis Ultra' },
  { value: 'ff91', label: 'FF 91 2.0' },
]

const LEAD_PRODUCT_OPTIONS = [
  { value: 'futurist', label: 'FF Futurist' },
  { value: 'futurist-ultra', label: 'FF Futurist Ultra' },
  { value: 'master', label: 'FF Master' },
  { value: 'aegis', label: 'FF Aegis' },
  { value: 'aegis-ultra', label: 'FF Aegis Ultra' },
  { value: 'ff91', label: 'FF 91 2.0' },
]

const EMPTY_RECO_FORM: RecommendationPayload = {
  enabled: true,
  product_name: 'master',
  trigger_scene: '',
  recommendation_content_cn: '',
  recommendation_content_en: '',
}

const EMPTY_LEAD_FORM: LeadPayload = {
  product: 'master',
  contact_name: '',
  email: '',
  phone: '',
  thread_id: '',
}

function keywordLinesToArray(text: string): string[] {
  return text
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
}

function isBlank(text: string): boolean {
  return text.trim().length === 0
}

/* ───── Recommendations Tab ───── */

function RecommendationsTab() {
  const [form, setForm] = useState<RecommendationPayload>(EMPTY_RECO_FORM)
  const [rows, setRows] = useState<RecommendationRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const loadRecommendations = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchRecommendations()
      setRows(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载推荐数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRecommendations()
  }, [loadRecommendations])

  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => a.product_name.localeCompare(b.product_name)),
    [rows]
  )

  const updateField = <K extends keyof RecommendationPayload>(
    key: K,
    value: RecommendationPayload[K]
  ) => {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  const resetForm = () => {
    setForm(EMPTY_RECO_FORM)
    setEditingId(null)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    if (isBlank(form.trigger_scene)) {
      setError('触发场景不能为空。')
      return
    }
    if (isBlank(form.recommendation_content_cn)) {
      setError('中文推荐文案不能为空。')
      return
    }
    if (isBlank(form.recommendation_content_en)) {
      setError('英文推荐文案不能为空。')
      return
    }

    setSubmitting(true)
    try {
      const payload = editingId ? { ...form, id: editingId } : form
      const { created } = await saveRecommendation(payload)
      setSuccess(created ? '新增成功。' : '更新成功。')
      resetForm()
      await loadRecommendations()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (row: RecommendationRecord) => {
    const { id: _, ...rest } = row
    setForm(rest)
    setEditingId(row.id)
    setError(null)
    setSuccess(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDelete = async (row: RecommendationRecord) => {
    const label = row.product_name || row.id
    if (!window.confirm(`确认删除推荐「${label}」吗？`)) return

    setDeletingId(row.id)
    setError(null)
    setSuccess(null)
    try {
      await deleteRecommendation(row.id)
      setSuccess(`已删除「${label}」`)
      if (editingId === row.id) resetForm()
      await loadRecommendations()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <section className="reco-card">
        <div className="recommendation-page-head">
          <div>
            <h1>{editingId ? `编辑：${form.product_name || editingId}` : '新增推荐'}</h1>
            <p>填写推荐图鉴信息后点击保存，数据直接写入后端配置。</p>
          </div>
          <div className="recommendation-page-links">
            <button type="button" className="admin-link-btn" onClick={resetForm}>
              清空表单
            </button>
          </div>
        </div>

        <form className="recommendation-form" onSubmit={handleSubmit}>
          <label>
            产品名称
            <select
              value={form.product_name}
              onChange={(e) => updateField('product_name', e.target.value)}
              required
            >
              {RECO_PRODUCT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>

          <label className="recommendation-toggle">
            <span>启用状态</span>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => updateField('enabled', e.target.checked)}
            />
          </label>

          <label className="recommendation-form-full">
            触发场景
            <textarea
              value={form.trigger_scene}
              onChange={(e) => updateField('trigger_scene', e.target.value)}
              placeholder="用户咨询工业巡检、安防巡逻、复杂环境作业……"
              rows={3}
              required
            />
          </label>

          <label className="recommendation-form-full">
            中文推荐文案
            <textarea
              value={form.recommendation_content_cn}
              onChange={(e) => updateField('recommendation_content_cn', e.target.value)}
              placeholder="请输入中文推荐文案"
              rows={4}
              required
            />
          </label>

          <label className="recommendation-form-full">
            英文推荐文案
            <textarea
              value={form.recommendation_content_en}
              onChange={(e) => updateField('recommendation_content_en', e.target.value)}
              placeholder="Please enter recommendation copy in English"
              rows={4}
              required
            />
          </label>

          <div className="recommendation-form-actions">
            <button type="submit" disabled={submitting}>
              {submitting ? '保存中…' : editingId ? '保存修改' : '新增推荐'}
            </button>
            {editingId && (
              <button
                type="button"
                className="recommendation-secondary-btn"
                onClick={resetForm}
              >
                取消编辑
              </button>
            )}
          </div>
        </form>

        {success && <p className="lead-msg success">{success}</p>}
        {error && <p className="lead-msg error">{error}</p>}
      </section>

      <section className="reco-card">
        <div className="lead-table-header">
          <div>
            <h2>推荐列表</h2>
            <p>共 {rows.length} 条，可直接编辑或删除。</p>
          </div>
          <button type="button" onClick={loadRecommendations} disabled={loading}>
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>

        <div className="lead-table-wrap">
          <table className="lead-table">
            <thead>
              <tr>
                <th>启用</th>
                <th>产品</th>
                <th>触发场景</th>
                <th>中文推荐</th>
                <th>英文推荐</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map(row => (
                <tr key={row.id} className={editingId === row.id ? 'reco-row-active' : ''}>
                  <td>
                    <span className={row.enabled ? 'reco-badge-on' : 'reco-badge-off'}>
                      {row.enabled ? '启用' : '停用'}
                    </span>
                  </td>
                  <td>{RECO_PRODUCT_OPTIONS.find(o => o.value === row.product_name)?.label || row.product_name || '-'}</td>
                  <td className="recommendation-cell-multiline">{row.trigger_scene || '-'}</td>
                  <td className="recommendation-cell-multiline">{row.recommendation_content_cn || '-'}</td>
                  <td className="recommendation-cell-multiline">{row.recommendation_content_en || '-'}</td>
                  <td>
                    <div className="recommendation-row-actions">
                      <button type="button" onClick={() => handleEdit(row)}>编辑</button>
                      <button
                        type="button"
                        className="recommendation-danger-btn"
                        onClick={() => handleDelete(row)}
                        disabled={deletingId === row.id}
                      >
                        {deletingId === row.id ? '删除中…' : '删除'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {sortedRows.length === 0 && !loading && (
                <tr><td colSpan={6}>暂无推荐数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

/* ───── Leads Tab ───── */

function LeadsTab() {
  const [form, setForm] = useState<LeadPayload>(EMPTY_LEAD_FORM)
  const [rows, setRows] = useState<LeadRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [triageLoading, setTriageLoading] = useState(true)
  const [triageSaving, setTriageSaving] = useState(false)
  const [triageError, setTriageError] = useState<string | null>(null)
  const [triageSuccess, setTriageSuccess] = useState<string | null>(null)
  const [triggerCn, setTriggerCn] = useState('')
  const [triggerEn, setTriggerEn] = useState('')
  const [kwCnText, setKwCnText] = useState('')
  const [kwEnText, setKwEnText] = useState('')
  const [leadCaptureBase, setLeadCaptureBase] = useState<Record<string, string>>({})

  const loadTriageConfig = useCallback(async () => {
    setTriageLoading(true)
    setTriageError(null)
    try {
      const cfg = await fetchLeadCaptureTriageConfig()
      const lc = cfg.lead_capture || {}
      setLeadCaptureBase(
        Object.fromEntries(
          Object.entries(lc).map(([k, v]) => [k, typeof v === 'string' ? v : String(v ?? '')])
        )
      )
      setTriggerCn(lc.trigger_conditions_cn ?? '')
      setTriggerEn(lc.trigger_conditions_en ?? '')
      setKwCnText((cfg.purchase_intent_keywords?.cn || []).join('\n'))
      setKwEnText((cfg.purchase_intent_keywords?.en || []).join('\n'))
    } catch (err) {
      setTriageError(err instanceof Error ? err.message : '加载留资触发配置失败')
    } finally {
      setTriageLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTriageConfig()
  }, [loadTriageConfig])

  const handleSaveTriageConfig = async (e: FormEvent) => {
    e.preventDefault()
    setTriageError(null)
    setTriageSuccess(null)
    const trimmedKwCn = keywordLinesToArray(kwCnText)
    const trimmedKwEn = keywordLinesToArray(kwEnText)

    if (isBlank(triggerCn)) {
      setTriageError('触发条件说明（中文）不能为空。')
      return
    }
    if (isBlank(triggerEn)) {
      setTriageError('Trigger notes (English) 不能为空。')
      return
    }
    if (trimmedKwCn.length === 0) {
      setTriageError('购买意图关键词（中文）至少填写一条。')
      return
    }
    if (trimmedKwEn.length === 0) {
      setTriageError('Purchase-intent keywords (English) 至少填写一条。')
      return
    }

    setTriageSaving(true)
    try {
      await saveLeadCaptureTriageConfig({
        lead_capture: {
          ...leadCaptureBase,
          trigger_conditions_cn: triggerCn,
          trigger_conditions_en: triggerEn,
        },
        purchase_intent_keywords: {
          cn: trimmedKwCn,
          en: trimmedKwEn,
        },
      })
      setTriageSuccess('已保存。下次对话的 Triage 将使用新配置动态生成购买意图判定说明。')
      await loadTriageConfig()
    } catch (err) {
      setTriageError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setTriageSaving(false)
    }
  }

  const loadLeads = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchLeads()
      setRows(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载留资数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadLeads()
  }, [loadLeads])

  const updateField = (key: keyof LeadPayload, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setSuccess(null)
    try {
      await submitLead(form)
      setSuccess('提交成功，已保存到服务端本地文件。')
      setForm(EMPTY_LEAD_FORM)
      await loadLeads()
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <section className="reco-card">
        <h1>留资触发（Triage）</h1>
        <p>
          配置会写入 <code className="text-xs">recommendations.json</code>，并在每次请求时通过{' '}
          <code className="text-xs">build_purchase_intent_prompt()</code> 注入 Triage 提示词中的{' '}
          <code className="text-xs">{'{{purchase_intent_rules}}'}</code> 占位符。
        </p>
        {triageLoading && <p className="text-sm text-gray-500">加载配置中…</p>}
        {!triageLoading && (
          <form className="lead-form" onSubmit={handleSaveTriageConfig}>
            <label className="lead-form-full">
              触发条件说明（中文）
              <textarea
                value={triggerCn}
                onChange={e => setTriggerCn(e.target.value)}
                placeholder="补充哪些情况应判为购买/商务意图（支持多行）"
                required
              />
            </label>
            <label className="lead-form-full">
              Trigger notes (English)
              <textarea
                value={triggerEn}
                onChange={e => setTriggerEn(e.target.value)}
                placeholder="English notes for purchase / business intent"
                required
              />
            </label>
            <label className="lead-form-full">
              购买意图关键词（中文，每行一条）
              <textarea
                value={kwCnText}
                onChange={e => setKwCnText(e.target.value)}
                placeholder="例如：&#10;询价&#10;多少钱&#10;采购"
                required
              />
            </label>
            <label className="lead-form-full">
              Purchase-intent keywords (English, one per line)
              <textarea
                value={kwEnText}
                onChange={e => setKwEnText(e.target.value)}
                placeholder={'e.g.\nprice\nquote\nprocurement'}
                required
              />
            </label>
            <button type="submit" disabled={triageSaving}>
              {triageSaving ? '保存中…' : '保存 Triage 留资配置'}
            </button>
          </form>
        )}
        {triageSuccess && <p className="lead-msg success">{triageSuccess}</p>}
        {triageError && <p className="lead-msg error">{triageError}</p>}
      </section>

      <section className="reco-card">
        <h2>测试留资提交</h2>
        <p>提交后会调用服务端留资接口，并写入本地存储。</p>
        <form className="lead-form" onSubmit={handleSubmit}>
          <label>
            产品
            <select
              value={form.product}
              onChange={(e) => updateField('product', e.target.value)}
            >
              {LEAD_PRODUCT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            姓名
            <input
              value={form.contact_name}
              onChange={(e) => updateField('contact_name', e.target.value)}
              placeholder="请输入姓名"
            />
          </label>
          <label>
            邮箱
            <input
              type="email"
              value={form.email}
              onChange={(e) => updateField('email', e.target.value)}
              placeholder="请输入邮箱"
            />
          </label>
          <label>
            电话
            <input
              value={form.phone}
              onChange={(e) => updateField('phone', e.target.value)}
              placeholder="请输入电话"
            />
          </label>
          <label>
            线程 ID（可选）
            <input
              value={form.thread_id || ''}
              onChange={(e) => updateField('thread_id', e.target.value)}
              placeholder="thread_xxx"
            />
          </label>
          <button type="submit" disabled={submitting}>
            {submitting ? '提交中…' : '提交'}
          </button>
        </form>
        {success && <p className="lead-msg success">{success}</p>}
        {error && <p className="lead-msg error">{error}</p>}
      </section>

      <section className="reco-card">
        <div className="lead-table-header">
          <h2>已保存用户数据</h2>
          <button type="button" onClick={loadLeads} disabled={loading}>
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
        <div className="lead-table-wrap">
          <table className="lead-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>产品</th>
                <th>姓名</th>
                <th>邮箱</th>
                <th>电话</th>
                <th>线程 ID</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`${row.timestamp}-${idx}`}>
                  <td>{row.timestamp}</td>
                  <td>{row.product}</td>
                  <td>{row.contact_name}</td>
                  <td>{row.email}</td>
                  <td>{row.phone}</td>
                  <td>{row.thread_id}</td>
                </tr>
              ))}
              {rows.length === 0 && !loading && (
                <tr><td colSpan={6}>暂无数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

/* ───── Homepage Prompts Tab ───── */

const EMPTY_PROMPT_FORM: HomepagePromptPayload = {
  enabled: true,
  label: '',
  prompt: '',
  sort_order: 0,
}

function HomepagePromptsTab() {
  const [form, setForm] = useState<HomepagePromptPayload>(EMPTY_PROMPT_FORM)
  const [rows, setRows] = useState<HomepagePrompt[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [settings, setSettings] = useState<HomepageSettings>({ greeting: '', placeholder: '', info_text: '' })
  const [settingsLoading, setSettingsLoading] = useState(true)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsError, setSettingsError] = useState<string | null>(null)
  const [settingsSuccess, setSettingsSuccess] = useState<string | null>(null)

  const loadPrompts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const cfg = await fetchHomepagePrompts(true)
      setRows(cfg.prompts)
      setSettings({ greeting: cfg.greeting, placeholder: cfg.placeholder, info_text: cfg.info_text })
      setSettingsLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载首页推荐数据失败')
      setSettingsLoading(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPrompts()
  }, [loadPrompts])

  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => a.sort_order - b.sort_order || a.id.localeCompare(b.id)),
    [rows],
  )

  const updateField = <K extends keyof HomepagePromptPayload>(
    key: K,
    value: HomepagePromptPayload[K],
  ) => {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  const resetForm = () => {
    setForm(EMPTY_PROMPT_FORM)
    setEditingId(null)
  }

  const handleSaveSettings = async (e: FormEvent) => {
    e.preventDefault()
    setSettingsError(null)
    setSettingsSuccess(null)
    if (isBlank(settings.greeting)) {
      setSettingsError('欢迎标题不能为空。')
      return
    }
    if (isBlank(settings.placeholder)) {
      setSettingsError('输入框提示词不能为空。')
      return
    }
    setSettingsSaving(true)
    try {
      const saved = await saveHomepageSettings(settings)
      setSettings(saved)
      setSettingsSuccess('页面设置已保存。')
    } catch (err) {
      setSettingsError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSettingsSaving(false)
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    if (isBlank(form.label)) {
      setError('按钮文本不能为空。')
      return
    }
    if (isBlank(form.prompt)) {
      setError('Prompt 内容不能为空。')
      return
    }

    setSubmitting(true)
    try {
      const payload = editingId ? { ...form, id: editingId } : form
      const { created } = await saveHomepagePrompt(payload)
      setSuccess(created ? '新增成功。' : '更新成功。')
      resetForm()
      await loadPrompts()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (row: HomepagePrompt) => {
    setForm({
      enabled: row.enabled,
      label: row.label,
      prompt: row.prompt,
      sort_order: row.sort_order,
    })
    setEditingId(row.id)
    setError(null)
    setSuccess(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDelete = async (row: HomepagePrompt) => {
    const label = row.label || row.id
    if (!window.confirm(`确认删除「${label}」吗？`)) return

    setDeletingId(row.id)
    setError(null)
    setSuccess(null)
    try {
      await deleteHomepagePrompt(row.id)
      setSuccess(`已删除「${label}」`)
      if (editingId === row.id) resetForm()
      await loadPrompts()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <section className="reco-card">
        <h1>页面设置</h1>
        <p>配置首页聊天面板中显示的欢迎标题和输入框提示词。</p>
        {settingsLoading ? (
          <p className="text-sm text-gray-500">加载中…</p>
        ) : (
          <form className="lead-form" onSubmit={handleSaveSettings}>
            <label className="lead-form-full">
              欢迎标题
              <input
                type="text"
                value={settings.greeting}
                onChange={(e) => setSettings(prev => ({ ...prev, greeting: e.target.value }))}
                placeholder="Hi! I can help you with any of our products."
                required
              />
            </label>
            <label className="lead-form-full">
              输入框提示词
              <input
                type="text"
                value={settings.placeholder}
                onChange={(e) => setSettings(prev => ({ ...prev, placeholder: e.target.value }))}
                placeholder="Ask a question…"
                required
              />
            </label>
            <label className="lead-form-full">
              推荐信息
              <textarea
                value={settings.info_text}
                onChange={(e) => setSettings(prev => ({ ...prev, info_text: e.target.value }))}
                placeholder="显示在推荐问题下方的纯文本提示信息（可留空）"
                rows={3}
              />
            </label>
            <button type="submit" disabled={settingsSaving}>
              {settingsSaving ? '保存中…' : '保存页面设置'}
            </button>
          </form>
        )}
        {settingsSuccess && <p className="lead-msg success">{settingsSuccess}</p>}
        {settingsError && <p className="lead-msg error">{settingsError}</p>}
      </section>

      <section className="reco-card">
        <div className="recommendation-page-head">
          <div>
            <h1>{editingId ? `编辑：${form.label || editingId}` : '新增首页推荐问题'}</h1>
            <p>配置首页聊天面板中显示的推荐问题按钮，用户点击后进入对话。</p>
          </div>
          <div className="recommendation-page-links">
            <button type="button" className="admin-link-btn" onClick={resetForm}>
              清空表单
            </button>
          </div>
        </div>

        <form className="recommendation-form" onSubmit={handleSubmit}>
          <label>
            按钮文本
            <input
              type="text"
              value={form.label}
              onChange={(e) => updateField('label', e.target.value)}
              placeholder="例如：FF Master"
              required
            />
          </label>

          <label>
            排序权重
            <input
              type="number"
              value={form.sort_order}
              onChange={(e) => updateField('sort_order', Number(e.target.value))}
              placeholder="0"
            />
          </label>

          <label className="recommendation-toggle">
            <span>启用状态</span>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => updateField('enabled', e.target.checked)}
            />
          </label>

          <label className="recommendation-form-full">
            Prompt 内容
            <textarea
              value={form.prompt}
              onChange={(e) => updateField('prompt', e.target.value)}
              placeholder="Tell me about FF Master. What are its key features, specs, and how do I get started?"
              rows={4}
              required
            />
          </label>

          <div className="recommendation-form-actions">
            <button type="submit" disabled={submitting}>
              {submitting ? '保存中…' : editingId ? '保存修改' : '新增推荐'}
            </button>
            {editingId && (
              <button
                type="button"
                className="recommendation-secondary-btn"
                onClick={resetForm}
              >
                取消编辑
              </button>
            )}
          </div>
        </form>

        {success && <p className="lead-msg success">{success}</p>}
        {error && <p className="lead-msg error">{error}</p>}
      </section>

      <section className="reco-card">
        <div className="lead-table-header">
          <div>
            <h2>首页推荐列表</h2>
            <p>共 {rows.length} 条，按排序权重升序显示。</p>
          </div>
          <button type="button" onClick={loadPrompts} disabled={loading}>
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>

        <div className="lead-table-wrap">
          <table className="lead-table">
            <thead>
              <tr>
                <th>启用</th>
                <th>排序</th>
                <th>按钮文本</th>
                <th>Prompt 内容</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map(row => (
                <tr key={row.id} className={editingId === row.id ? 'reco-row-active' : ''}>
                  <td>
                    <span className={row.enabled ? 'reco-badge-on' : 'reco-badge-off'}>
                      {row.enabled ? '启用' : '停用'}
                    </span>
                  </td>
                  <td>{row.sort_order}</td>
                  <td>{row.label || '-'}</td>
                  <td className="recommendation-cell-multiline">{row.prompt || '-'}</td>
                  <td>
                    <div className="recommendation-row-actions">
                      <button type="button" onClick={() => handleEdit(row)}>编辑</button>
                      <button
                        type="button"
                        className="recommendation-danger-btn"
                        onClick={() => handleDelete(row)}
                        disabled={deletingId === row.id}
                      >
                        {deletingId === row.id ? '删除中…' : '删除'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {sortedRows.length === 0 && !loading && (
                <tr><td colSpan={5}>暂无首页推荐数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

/* ───── Admin Page (Shell) ───── */

const TABS: { key: Tab; label: string }[] = [
  { key: 'recommendations', label: '推荐管理' },
  { key: 'leads', label: '留资管理' },
  { key: 'homepage-prompts', label: '首页推荐' },
]

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('recommendations')

  useEffect(() => {
    document.title = '管理后台 - EAI Robot'
  }, [])

  return (
    <div className="reco-standalone">
      <header className="reco-header">
        <div className="reco-header-left">
          <Link to="/">
            <img src={logoDark} alt="EAI Robot" className="reco-header-logo" />
          </Link>
          <span className="reco-header-title">管理后台</span>
        </div>
        <nav className="reco-header-nav">
          <Link to="/" className="reco-nav-btn">返回手册</Link>
        </nav>
      </header>

      <div className="admin-tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`admin-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <main className="reco-body">
        {activeTab === 'recommendations' && <RecommendationsTab />}
        {activeTab === 'leads' && <LeadsTab />}
        {activeTab === 'homepage-prompts' && <HomepagePromptsTab />}
      </main>
    </div>
  )
}
