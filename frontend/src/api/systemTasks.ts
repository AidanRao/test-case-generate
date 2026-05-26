import { requestJson } from './http'

export interface SystemTask {
  id: string
  name: string
  description: string
  enabled: boolean
  interval_seconds: number
  available: boolean
  running: boolean
}

const getSystemTasks = async () => {
  const response = await requestJson<{ list: SystemTask[] }>('/system/tasks')
  return response.data.list ?? []
}

const updateSystemTask = async (
  taskId: string,
  payload: { enabled: boolean; interval_seconds: number }
) => {
  const response = await requestJson<SystemTask>(`/system/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
  return response.data
}

export { getSystemTasks, updateSystemTask }
