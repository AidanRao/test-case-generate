import { requestJson } from './http'

export interface AIConfig {
  api_key: string
  base_url: string
  model: string
  updated_at: number
}

interface AIConfigResponse {
  api_key: string
  base_url: string
  model: string
  updated_at: number
}

const getConfig = async () => {
  const response = await requestJson<AIConfigResponse>('/ai/config')
  return response.data
}

const saveConfig = async (payload: { api_key: string; base_url?: string; model?: string }) => {
  const response = await requestJson<AIConfigResponse>('/ai/config', {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
  return response.data
}

export {
  getConfig,
  saveConfig
}