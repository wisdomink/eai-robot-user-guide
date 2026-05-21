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
  deleteHomepagePage,
  fetchAllHomepagePages,
  saveHomepageGlobalPrompts,
  type HomepagePrompt,
  type HomepagePromptPayload,
  type HomepagePage,
  type HomepagePagePayload,
  type HomepagePromptType,
  saveHomepagePage,
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
  firstName: '',
  lastName: '',
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
      setSuccess('提交成功，已保存到服务端。')
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
        <p>提交后会调用服务端留资接口，并按当前配置保存与同步数据。</p>
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
            名
            <input
              value={form.firstName}
              onChange={(e) => updateField('firstName', e.target.value)}
              placeholder="请输入名"
            />
          </label>
          <label>
            姓
            <input
              value={form.lastName}
              onChange={(e) => updateField('lastName', e.target.value)}
              placeholder="请输入姓"
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
                <th>名</th>
                <th>姓</th>
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
                  <td>{row.firstName}</td>
                  <td>{row.lastName}</td>
                  <td>{row.email}</td>
                  <td>{row.phone}</td>
                  <td>{row.thread_id}</td>
                </tr>
              ))}
              {rows.length === 0 && !loading && (
                <tr><td colSpan={7}>暂无数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

/* ───── Homepage Prompts Tab ───── */

function createDraftPrompt(index: number, type: HomepagePromptType = 'message'): HomepagePrompt {
  return {
    id: `draft_prompt_${Date.now()}_${index}`,
    enabled: true,
    type,
    label: '',
    prompt: '',
    reply_text: '',
    sort_order: index,
  }
}

function createDraftPage(): HomepagePage {
  return {
    id: `draft_page_${Date.now()}`,
    pattern: '',
    label: '新页面',
    greeting: '',
    placeholder: '',
    info_text: '',
    prompts: [],
  }
}

function HomepagePromptsTab() {
  const [pages, setPages] = useState<HomepagePage[]>([])
  const [globalPrompts, setGlobalPrompts] = useState<HomepagePrompt[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savingGlobal, setSavingGlobal] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const loadPages = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAllHomepagePages()
      setPages(data.pages)
      setGlobalPrompts(data.global_prompts)
      setActiveId(current => current && data.pages.some(page => page.id === current) ? current : data.pages[0]?.id ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载首页推荐数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPages()
  }, [loadPages])

  const activePage = useMemo(
    () => pages.find(page => page.id === activeId) ?? null,
    [activeId, pages],
  )

  const updateActivePage = useCallback((updater: (page: HomepagePage) => HomepagePage) => {
    setPages(prev => prev.map(page => page.id === activeId ? updater(page) : page))
  }, [activeId])

  const handleCreatePage = () => {
    const nextPage = createDraftPage()
    setPages(prev => [...prev, nextPage])
    setActiveId(nextPage.id)
    setError(null)
    setSuccess('已新增一个待保存的页面标签，请填写路径与配置后保存。')
  }

  const handlePromptChange = <K extends keyof HomepagePrompt>(
    promptIndex: number,
    key: K,
    value: HomepagePrompt[K],
  ) => {
    updateActivePage(page => ({
      ...page,
      prompts: page.prompts.map((prompt, index) =>
        index === promptIndex ? { ...prompt, [key]: value } : prompt
      ),
    }))
  }

  const handleAddPrompt = () => {
    updateActivePage(page => ({
      ...page,
      prompts: [...page.prompts, createDraftPrompt(page.prompts.length)],
    }))
  }

  const handleDeletePrompt = (promptIndex: number) => {
    updateActivePage(page => ({
      ...page,
      prompts: page.prompts
        .filter((_, index) => index !== promptIndex)
        .map((prompt, index) => ({ ...prompt, sort_order: index })),
    }))
  }

  const movePrompt = (promptIndex: number, direction: -1 | 1) => {
    updateActivePage(page => {
      const nextIndex = promptIndex + direction
      if (nextIndex < 0 || nextIndex >= page.prompts.length) return page
      const prompts = [...page.prompts]
      const [target] = prompts.splice(promptIndex, 1)
      prompts.splice(nextIndex, 0, target)
      return {
        ...page,
        prompts: prompts.map((prompt, index) => ({ ...prompt, sort_order: index })),
      }
    })
  }

  const handlePageFieldChange = <K extends keyof HomepagePage>(
    key: K,
    value: HomepagePage[K],
  ) => {
    updateActivePage(page => ({ ...page, [key]: value }))
  }

  const toSavePayload = (page: HomepagePage): HomepagePagePayload => {
    const isDraftPage = page.id.startsWith('draft_page_')
    return {
      ...(isDraftPage ? {} : { id: page.id }),
      pattern: page.pattern,
      label: page.label,
      greeting: page.greeting,
      placeholder: page.placeholder,
      info_text: page.info_text,
      prompts: page.prompts.map((prompt, index) => ({
        ...(prompt.id.startsWith('draft_prompt_') ? {} : { id: prompt.id }),
        enabled: prompt.enabled,
        type: prompt.type ?? 'message',
        label: prompt.label,
        prompt: prompt.prompt,
        reply_text: prompt.reply_text ?? '',
        sort_order: index,
      })),
    }
  }

  const handleGlobalPromptChange = <K extends keyof HomepagePrompt>(
    index: number,
    key: K,
    value: HomepagePrompt[K],
  ) => {
    setGlobalPrompts(prev => prev.map((p, i) => i === index ? { ...p, [key]: value } : p))
  }

  const handleAddGlobalPrompt = () => {
    setGlobalPrompts(prev => [...prev, createDraftPrompt(prev.length)])
  }

  const handleDeleteGlobalPrompt = (index: number) => {
    setGlobalPrompts(prev => prev.filter((_, i) => i !== index).map((p, i) => ({ ...p, sort_order: i })))
  }

  const moveGlobalPrompt = (index: number, direction: -1 | 1) => {
    setGlobalPrompts(prev => {
      const nextIndex = index + direction
      if (nextIndex < 0 || nextIndex >= prev.length) return prev
      const arr = [...prev]
      const [target] = arr.splice(index, 1)
      arr.splice(nextIndex, 0, target)
      return arr.map((p, i) => ({ ...p, sort_order: i }))
    })
  }

  const handleSaveGlobalPrompts = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    const invalidPrompt = globalPrompts.find(p => !p.label.trim() || (p.type !== 'lead_capture' && !p.prompt.trim()))
    if (invalidPrompt) {
      setError('通用按钮的文本和 Prompt 内容（非留资类型）不能为空。')
      return
    }
    setSavingGlobal(true)
    try {
      const payload: HomepagePromptPayload[] = globalPrompts.map((p, i) => ({
        ...(p.id.startsWith('draft_prompt_') ? {} : { id: p.id }),
        enabled: p.enabled,
        type: p.type ?? 'message',
        label: p.label,
        prompt: p.prompt,
        reply_text: p.reply_text ?? '',
        sort_order: i,
      }))
      const saved = await saveHomepageGlobalPrompts(payload)
      setGlobalPrompts(saved)
      setSuccess('通用按钮已保存。')
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存通用按钮失败')
    } finally {
      setSavingGlobal(false)
    }
  }

  const handleSavePage = async (e: FormEvent) => {
    e.preventDefault()
    if (!activePage) return

    setError(null)
    setSuccess(null)
    if (isBlank(activePage.pattern)) {
      setError('页面路径不能为空。')
      return
    }
    if (isBlank(activePage.label)) {
      setError('页面标签不能为空。')
      return
    }
    if (isBlank(activePage.greeting)) {
      setError('欢迎标题不能为空。')
      return
    }
    if (isBlank(activePage.placeholder)) {
      setError('输入框提示词不能为空。')
      return
    }

    const invalidPrompt = activePage.prompts.find(prompt =>
      isBlank(prompt.label) || (prompt.type !== 'lead_capture' && isBlank(prompt.prompt))
    )
    if (invalidPrompt) {
      setError('推荐列表中的按钮文本不能为空，且非留资类型的 Prompt 内容不能为空。')
      return
    }

    setSaving(true)
    try {
      const { page, created } = await saveHomepagePage(toSavePayload(activePage))
      setPages(prev => prev.map(item => item.id === activePage.id ? page : item))
      setActiveId(page.id)
      setSuccess(created ? '页面配置已新增并保存。' : '页面配置已保存。')
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDeletePage = async () => {
    if (!activePage) return
    if (activePage.pattern === '*') {
      setError('默认 fallback 页面不可删除。')
      return
    }

    const label = activePage.label || activePage.pattern || activePage.id
    if (!window.confirm(`确认删除页面标签「${label}」吗？`)) return

    if (activePage.id.startsWith('draft_page_')) {
      const nextPages = pages.filter(page => page.id !== activePage.id)
      setPages(nextPages)
      setActiveId(nextPages[0]?.id ?? null)
      setSuccess(`已删除未保存页面「${label}」`)
      return
    }

    setDeletingId(activePage.id)
    setError(null)
    setSuccess(null)
    try {
      await deleteHomepagePage(activePage.id)
      const nextPages = pages.filter(page => page.id !== activePage.id)
      setPages(nextPages)
      setActiveId(nextPages[0]?.id ?? null)
      setSuccess(`已删除页面「${label}」`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      {/* ── 通用按钮区（全站优先） ── */}
      <section className="reco-card">
        <form onSubmit={handleSaveGlobalPrompts}>
          <div className="recommendation-page-head">
            <div>
              <h1>通用按钮（全站优先）</h1>
              <p>所有页面首页都会优先显示这里配置的按钮，位于各页面推荐按钮之前。可配置 0 条。</p>
            </div>
            <div className="recommendation-page-links">
              <button type="button" className="admin-link-btn" onClick={handleAddGlobalPrompt}>
                + 新增通用按钮
              </button>
            </div>
          </div>

          <div className="homepage-inline-prompt-list">
            {globalPrompts.map((prompt, index) => (
              <div key={prompt.id} className="homepage-inline-prompt-card">
                <div className="homepage-inline-prompt-head">
                  <strong>通用按钮 {index + 1}</strong>
                  <div className="homepage-inline-prompt-actions">
                    <button type="button" onClick={() => moveGlobalPrompt(index, -1)} disabled={index === 0}>上移</button>
                    <button type="button" onClick={() => moveGlobalPrompt(index, 1)} disabled={index === globalPrompts.length - 1}>下移</button>
                    <button type="button" className="recommendation-danger-btn" onClick={() => handleDeleteGlobalPrompt(index)}>删除</button>
                  </div>
                </div>

                <div className="recommendation-form">
                  <label>
                    按钮文本
                    <input
                      type="text"
                      value={prompt.label}
                      onChange={(e) => handleGlobalPromptChange(index, 'label', e.target.value)}
                      placeholder="例如：联系我们"
                    />
                  </label>

                  <label>
                    按钮类型
                    <select
                      value={prompt.type ?? 'message'}
                      onChange={(e) => handleGlobalPromptChange(index, 'type', e.target.value as HomepagePromptType)}
                    >
                      <option value="message">普通问答（message）</option>
                      <option value="lead_capture">直接留资（lead_capture）</option>
                    </select>
                  </label>

                  <label className="recommendation-toggle">
                    <span>启用状态</span>
                    <input
                      type="checkbox"
                      checked={prompt.enabled}
                      onChange={(e) => handleGlobalPromptChange(index, 'enabled', e.target.checked)}
                    />
                  </label>

                  {(prompt.type ?? 'message') !== 'lead_capture' ? (
                    <label className="recommendation-form-full">
                      Prompt 内容
                      <textarea
                        value={prompt.prompt}
                        onChange={(e) => handleGlobalPromptChange(index, 'prompt', e.target.value)}
                        placeholder="用户点击后发送给 ChatKit 的完整提示词"
                        rows={3}
                      />
                    </label>
                  ) : (
                    <label className="recommendation-form-full">
                      AI 引导语（留资表单前显示，空则不显示）
                      <textarea
                        value={prompt.reply_text ?? ''}
                        onChange={(e) => handleGlobalPromptChange(index, 'reply_text', e.target.value)}
                        placeholder="例如：好的，请填写以下信息，我们会尽快与您联系。留空则直接弹出表单。"
                        rows={3}
                      />
                    </label>
                  )}
                </div>
              </div>
            ))}
            {globalPrompts.length === 0 && (
              <div className="homepage-inline-empty">暂无通用按钮，点击"新增通用按钮"即可添加。</div>
            )}
          </div>

          <div className="recommendation-form-actions">
            <button type="submit" disabled={savingGlobal}>
              {savingGlobal ? '保存中…' : '保存通用按钮'}
            </button>
          </div>
        </form>
      </section>

      {/* ── 页面路径标签（按 URL 匹配） ── */}
      <section className="reco-card">
        <div className="recommendation-page-head">
          <div>
            <h1>页面路径标签</h1>
            <p>按页面 URL 匹配首页推荐配置。支持直接填写映射表中的路径写法：若只填 `/fx` 这类路径，会默认补成 `www.ff.com`。</p>
          </div>
          <div className="recommendation-page-links">
            <button type="button" className="admin-link-btn" onClick={handleCreatePage}>
              + 新增页面标签
            </button>
            <button type="button" className="admin-link-btn" onClick={loadPages} disabled={loading}>
              {loading ? '刷新中…' : '刷新'}
            </button>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">加载中…</p>
        ) : (
          <div className="homepage-page-tabs">
            {pages.map(page => (
              <button
                key={page.id}
                type="button"
                className={`homepage-page-tab ${page.id === activeId ? 'active' : ''}`}
                onClick={() => {
                  setActiveId(page.id)
                  setError(null)
                  setSuccess(null)
                }}
              >
                <span>{page.label || page.pattern || '未命名页面'}</span>
                <small>{page.pattern || '待填写路径'}</small>
              </button>
            ))}
            {pages.length === 0 && <p className="homepage-page-empty">暂无页面标签，请先新增。</p>}
          </div>
        )}
      </section>

      <section className="reco-card">
        {!activePage ? (
          <p className="homepage-page-empty">请选择一个页面标签后开始编辑。</p>
        ) : (
          <form className="homepage-page-shell" onSubmit={handleSavePage}>
            <div className="recommendation-page-head">
              <div>
                <h1>{activePage.label || '未命名页面'}</h1>
                <p>当前页面匹配规则：{activePage.pattern || '待填写'}</p>
              </div>
              <div className="recommendation-page-links">
                <button
                  type="button"
                  className="recommendation-danger-btn"
                  onClick={handleDeletePage}
                  disabled={deletingId === activePage.id || activePage.pattern === '*'}
                >
                  {deletingId === activePage.id ? '删除中…' : '删除此页面'}
                </button>
              </div>
            </div>

            <div className="recommendation-form">
              <label className="recommendation-form-full">
                页面路径
                <input
                  type="text"
                  value={activePage.pattern}
                  onChange={(e) => handlePageFieldChange('pattern', e.target.value)}
                  placeholder="例如：/fx、robotics.ff.com/fx-aegis、https://www.ff.com/preorder/* 或 *"
                  required
                />
              </label>

              <label>
                页面标签
                <input
                  type="text"
                  value={activePage.label}
                  onChange={(e) => handlePageFieldChange('label', e.target.value)}
                  placeholder="例如：官网首页"
                  required
                />
              </label>

              <label>
                欢迎标题
                <input
                  type="text"
                  value={activePage.greeting}
                  onChange={(e) => handlePageFieldChange('greeting', e.target.value)}
                  placeholder="想了解 FF 的产品吗？"
                  required
                />
              </label>

              <label className="recommendation-form-full">
                输入框提示词
                <input
                  type="text"
                  value={activePage.placeholder}
                  onChange={(e) => handlePageFieldChange('placeholder', e.target.value)}
                  placeholder="Ask anything about FF..."
                  required
                />
              </label>

              <label className="recommendation-form-full">
                推荐信息
                <textarea
                  value={activePage.info_text}
                  onChange={(e) => handlePageFieldChange('info_text', e.target.value)}
                  placeholder="显示在推荐问题下方的纯文本提示信息（可留空）"
                  rows={3}
                />
              </label>
            </div>

            <div className="homepage-inline-prompts">
              <div className="recommendation-page-head">
                <div>
                  <h2>推荐列表</h2>
                  <p>推荐问题会跟随当前页面配置一起保存，不再单独提交。</p>
                </div>
                <div className="recommendation-page-links">
                  <button type="button" className="admin-link-btn" onClick={handleAddPrompt}>
                    + 新增推荐
                  </button>
                </div>
              </div>

              <div className="homepage-inline-prompt-list">
                {activePage.prompts.map((prompt, index) => (
                  <div key={prompt.id} className="homepage-inline-prompt-card">
                    <div className="homepage-inline-prompt-head">
                      <strong>推荐 {index + 1}</strong>
                      <div className="homepage-inline-prompt-actions">
                        <button type="button" onClick={() => movePrompt(index, -1)} disabled={index === 0}>
                          上移
                        </button>
                        <button
                          type="button"
                          onClick={() => movePrompt(index, 1)}
                          disabled={index === activePage.prompts.length - 1}
                        >
                          下移
                        </button>
                        <button
                          type="button"
                          className="recommendation-danger-btn"
                          onClick={() => handleDeletePrompt(index)}
                        >
                          删除
                        </button>
                      </div>
                    </div>

                    <div className="recommendation-form">
                      <label>
                        按钮文本
                        <input
                          type="text"
                          value={prompt.label}
                          onChange={(e) => handlePromptChange(index, 'label', e.target.value)}
                          placeholder="例如：FF 目前有哪些产品线？"
                        />
                      </label>

                      <label>
                        按钮类型
                        <select
                          value={prompt.type ?? 'message'}
                          onChange={(e) => handlePromptChange(index, 'type', e.target.value as HomepagePromptType)}
                        >
                          <option value="message">普通问答（message）</option>
                          <option value="lead_capture">直接留资（lead_capture）</option>
                        </select>
                      </label>

                      <label className="recommendation-toggle">
                        <span>启用状态</span>
                        <input
                          type="checkbox"
                          checked={prompt.enabled}
                          onChange={(e) => handlePromptChange(index, 'enabled', e.target.checked)}
                        />
                      </label>

                      {(prompt.type ?? 'message') !== 'lead_capture' ? (
                        <label className="recommendation-form-full">
                          Prompt 内容
                          <textarea
                            value={prompt.prompt}
                            onChange={(e) => handlePromptChange(index, 'prompt', e.target.value)}
                            placeholder="请输入用户点击后发送给 ChatKit 的完整提示词"
                            rows={4}
                          />
                        </label>
                      ) : (
                        <label className="recommendation-form-full">
                          AI 引导语（留资表单前显示，空则不显示）
                          <textarea
                            value={prompt.reply_text ?? ''}
                            onChange={(e) => handlePromptChange(index, 'reply_text', e.target.value)}
                            placeholder="例如：好的，请填写以下信息，我们会尽快与您联系。留空则直接弹出表单。"
                            rows={3}
                          />
                        </label>
                      )}
                    </div>
                  </div>
                ))}

                {activePage.prompts.length === 0 && (
                  <div className="homepage-inline-empty">
                    当前页面还没有推荐问题，点击“新增推荐”即可添加。
                  </div>
                )}
              </div>
            </div>

            <div className="recommendation-form-actions">
              <button type="submit" disabled={saving}>
                {saving ? '保存中…' : '保存当前页面'}
              </button>
            </div>
          </form>
        )}

        {success && <p className="lead-msg success">{success}</p>}
        {error && <p className="lead-msg error">{error}</p>}
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
