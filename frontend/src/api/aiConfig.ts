import { requestJson } from './http'

export interface AIConfig {
  has_api_key: boolean
  base_url: string
  model: string
  updated_at: number
}

export interface AIConfigInput {
  api_key?: string
  base_url: string
  model: string
}

export interface ConnectionTestResult {
  success: boolean
  status_code: number | null
  duration_ms: number
  message: string
  detail: string
}

const getConfig = async () => {
  const response = await requestJson<AIConfig>('/ai/config')
  return response.data
}

const saveConfig = async (payload: AIConfigInput) => {
  const response = await requestJson<AIConfig>('/ai/config', {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
  return response.data
}

const testBackendConnection = async (payload: AIConfigInput) => {
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
