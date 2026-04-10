type ApiResponse<T> = {
  code: number
  message: string
  data: T
}

const BASE_URL = (import.meta.env.VITE_BASE_URL as string) || '/api/v1'

const requestJson = async <T>(path: string, options: RequestInit = {}) => {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...(options.headers || {})
    }
  })
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
  return (await response.json()) as ApiResponse<T>
}

const requestBlob = async (path: string, options: RequestInit = {}) => {
  const response = await fetch(`${BASE_URL}${path}`, options)
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
  const blob = await response.blob()
  return { blob, headers: response.headers }
}

export { requestJson, requestBlob, type ApiResponse }
