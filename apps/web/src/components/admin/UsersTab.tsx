import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  createAdminUser, fetchAdminLoginLogs, fetchAdminUsers, updateAdminUser,
  type AdminUser, type LoginLogPage,
} from '@/api/admin'

function formatTime(value: string | null) {
  return value ? new Date(value).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false }) : '—'
}

export default function UsersTab() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadUsers = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    setError('')
    try {
      const rows = await fetchAdminUsers(signal)
      if (!signal?.aborted) setUsers(rows)
    } catch (err) {
      if (!signal?.aborted) setError(err instanceof Error ? err.message : '加载账号失败')
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void loadUsers(controller.signal)
    return () => controller.abort()
  }, [loadUsers])

  function resetForm() {
    setUsername('')
    setPassword('')
    setEditing(false)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      if (editing) await updateAdminUser(username, { password })
      else await createAdminUser(username, password)
      setSuccess(editing ? `已重置 ${username} 的密码，旧登录会话已失效。` : `账号 ${username} 已创建，请将账号和密码分配给使用者。`)
      resetForm()
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存账号失败')
    } finally {
      setBusy(false)
    }
  }

  async function toggleEnabled(user: AdminUser) {
    if (user.enabled && !window.confirm(`确认停用账号「${user.username}」？该账号的登录会话将失效。`)) return
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      await updateAdminUser(user.username, { enabled: !user.enabled })
      setSuccess(`账号 ${user.username} 已${user.enabled ? '停用' : '启用'}。`)
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新账号失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="reco-card admin-account-card">
        <h1>{editing ? '重置账号密码' : '分配普通账号'}</h1>
        <p>普通账号与管理员拥有相同的业务操作权限，账号管理和登录记录仅管理员可见。</p>
        <form className="recommendation-form" onSubmit={handleSubmit}>
          <label>
            账号
            <input value={username} onChange={event => setUsername(event.target.value)} required
              minLength={3} maxLength={64} pattern="[A-Za-z0-9][A-Za-z0-9_.\-]{2,63}"
              title="3–64 位字母、数字、下划线、点或短横线，以字母或数字开头"
              autoComplete="off" disabled={editing || busy} />
          </label>
          <label>
            {editing ? '新密码' : '初始密码'}
            <input type="password" value={password} onChange={event => setPassword(event.target.value)}
              required minLength={8} maxLength={128} autoComplete="new-password" disabled={busy} />
          </label>
          <div className="recommendation-form-actions">
            <button type="submit" disabled={busy}>{busy ? '保存中…' : editing ? '重置密码' : '创建账号'}</button>
            {editing && <button type="button" className="recommendation-secondary-btn" onClick={resetForm} disabled={busy}>取消重置</button>}
          </div>
        </form>
        {error && <p className="lead-msg error" role="alert">{error}</p>}
        {success && <p className="lead-msg success" role="status">{success}</p>}
      </section>

      <section className="reco-card admin-account-card">
        <div className="recommendation-page-head">
          <div><h2>账号列表</h2><p>时间以北京时间显示。</p></div>
          <button type="button" className="admin-link-btn" disabled={loading || busy} onClick={() => void loadUsers()}>刷新</button>
        </div>
        {loading ? <p role="status">加载中…</p> : (
          <div className="lead-table-wrap">
            <table className="lead-table">
              <thead><tr><th>账号</th><th>角色</th><th>状态</th><th>创建时间</th><th>最近登录</th><th>操作</th></tr></thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.username}>
                    <td>{user.username}</td><td>{user.role === 'admin' ? '管理员' : '普通账号'}</td>
                    <td><span className={user.enabled ? 'reco-badge-on' : 'reco-badge-off'}>{user.enabled ? '启用' : '停用'}</span></td>
                    <td>{formatTime(user.created_at)}</td><td>{formatTime(user.last_login_at)}</td>
                    <td>{user.role === 'admin' ? '内置管理员' : (
                      <div className="recommendation-row-actions">
                        <button type="button" disabled={busy} onClick={() => {
                          setUsername(user.username); setPassword(''); setEditing(true); setError(''); setSuccess('')
                          window.scrollTo({ top: 0, behavior: 'smooth' })
                        }}>重置密码</button>
                        <button type="button" disabled={busy} onClick={() => void toggleEnabled(user)}>{user.enabled ? '停用' : '启用'}</button>
                      </div>
                    )}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <LoginLogs />
    </>
  )
}

function LoginLogs() {
  const [username, setUsername] = useState('')
  const [filter, setFilter] = useState('')
  const [cursors, setCursors] = useState<(string | null)[]>([null])
  const [page, setPage] = useState<LoginLogPage>({ logs: [], after: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  const after = cursors[cursors.length - 1]

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    fetchAdminLoginLogs(filter, after, controller.signal)
      .then(value => { if (!controller.signal.aborted) setPage(value) })
      .catch(err => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : '加载登录记录失败') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [filter, after, revision])

  return (
    <section className="reco-card admin-account-card">
      <h2>登录记录</h2>
      <p>记录登录成功和失败，时间以北京时间显示，每页 25 条。</p>
      <form className="recommendation-form" onSubmit={event => {
        event.preventDefault(); setFilter(username.trim()); setCursors([null]); setRevision(value => value + 1)
      }}>
        <label>筛选账号<input value={username} onChange={event => setUsername(event.target.value)} maxLength={64} placeholder="留空查看全部" /></label>
        <div className="recommendation-form-actions"><button type="submit" disabled={loading}>查询 / 刷新</button></div>
      </form>
      {error && <p className="lead-msg error" role="alert">{error}</p>}
      {loading ? <p role="status">加载中…</p> : error ? null : page.logs.length === 0 ? <p>暂无登录记录</p> : (
        <div className="lead-table-wrap">
          <table className="lead-table">
            <thead><tr><th>账号</th><th>登录时间</th><th>IP</th><th>结果</th></tr></thead>
            <tbody>{page.logs.map((log, index) => (
              <tr key={`${log.timestamp}-${index}`}>
                <td>{log.username}</td><td>{formatTime(log.timestamp)}</td><td>{log.ip || '—'}</td>
                <td><span className={log.success ? 'reco-badge-on' : 'reco-badge-off'}>{log.success ? '成功' : '失败'}</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="admin-log-pagination">
        <button type="button" className="admin-link-btn" disabled={loading || cursors.length === 1} onClick={() => setCursors(value => value.slice(0, -1))}>上一页</button>
        <span>第 {cursors.length} 页</span>
        <button type="button" className="admin-link-btn" disabled={loading || !!error || !page.after} onClick={() => setCursors(value => [...value, page.after])}>下一页</button>
      </div>
    </section>
  )
}
