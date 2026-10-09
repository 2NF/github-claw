async function req(url, opts) {
  const r = await fetch(url, opts)
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.error || `请求失败 (${r.status})`)
  return data
}

export const getFormats = () => req('/api/formats')
export const getStats = () => req('/api/stats')
export const listTasks = (kind) => req('/api/tasks' + (kind ? `?kind=${kind}` : ''))
export const getTask = (id) => req(`/api/tasks/${id}`)
export const deleteTask = (id) => req(`/api/tasks/${id}`, { method: 'DELETE' })
export const downloadUrl = (id) => `/api/tasks/${id}/download`
export const createTask = (fd) => req('/api/tasks', { method: 'POST', body: fd })

export function fmtSize(n) {
  if (n == null) return '-'
  if (n < 1024) return n + ' B'
  if (n < 1048576) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1048576).toFixed(2) + ' MB'
}
