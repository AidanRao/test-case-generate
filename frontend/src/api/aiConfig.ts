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

export interface ConnectionTestResult {
  success: boolean
  status_code: number | null
  duration_ms: number
  message: string
  detail: string
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

const testBackendConnection = async (payload: { api_key: string; base_url: string; model: string }) => {
  const response = await requestJson<ConnectionTestResult>('/ai/config/test', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
  return response.data
}

export {
  getConfig,
  saveConfig,
  testBackendConnection
}
