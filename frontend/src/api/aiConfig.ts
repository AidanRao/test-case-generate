import { requestJson } from './http'

export interface AIConfig {
  id: string
  api_key: string
  base_url: string
  model: string
  created_at: number
  updated_at: number
}

interface AIConfigListResponse {
  list: AIConfig[]
}

interface AIConfigResponse {
  id: string
  api_key: string
  base_url: string
  model: string
  created_at: number
  updated_at: number
}

const listConfigs = async () => {
  const response = await requestJson<AIConfigListResponse>('/ai/configs')
  return response.data.list ?? []
}

const getConfig = async (configId: string) => {
  const response = await requestJson<AIConfigResponse>(`/ai/configs/${configId}`)
  return response.data
}

const createConfig = async (payload: { api_key: string; base_url?: string; model?: string }) => {
  const response = await requestJson<AIConfigResponse>('/ai/configs', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
  return response.data
}

const updateConfig = async (configId: string, payload: { api_key?: string; base_url?: string; model?: string }) => {
  const response = await requestJson<AIConfigResponse>(`/ai/configs/${configId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
  return response.data
}

const deleteConfig = async (configId: string) => {
  const response = await requestJson<{ deleted: boolean }>(`/ai/configs/${configId}`, {
    method: 'DELETE'
  })
  return response.data
}

const getDefaultConfig = async () => {
  const response = await requestJson<AIConfigResponse | {}>('/ai/configs/default')
  return response.data
}

export {
  listConfigs,
  getConfig,
  createConfig,
  updateConfig,
  deleteConfig,
  getDefaultConfig
}