import type { ModuleGroup } from '../data/projectStore'
import { requestBlob, requestJson } from './http'

type ProjectListResponse = {
  list: Array<{
    id: string
    code: string
    title: string
    module_count: number
    requirement_count: number
  }>
}

type ProjectDetailResponse = {
  id: string
  code: string
  title: string
  requirements: Array<{
    id: string
    title: string
    type: string
    code: string
    content: string
    project_id: string
    module: string
    testcases: Array<{
      requirement_code: string
      requirement_id: string
      id: string
      title: string
      code: string
      type: string
      test_steps: Array<{ expectation: string; step_desc: string }>
      test_target_desc: string
      verify_method: string
    }>
  }>
}

type CreateProjectResponse = {
  id: string
}

type GenerateTestcasesAsyncResponse = {
  job_id: string
}

type GenerateTestcasesStatusResponse = {
  job_id?: string
  status: 'idle' | 'running' | 'done'
}

type DeleteProjectResponse = {
  deleted: boolean
}

type UpdateRequirementPayload = {
  title: string
  type: string
  content: string
  module?: string
}

type UpdateTestcasePayload = {
  title: string
  code: string
  type: string
  test_steps: Array<{ expectation: string; step_desc: string }>
  test_target_desc: string
  verify_method: string
}

export type CreateRequirementPayload = {
  title: string
  type: string
  code: string
  content: string
  module: string
}

const fetchProjectList = async () => {
  const response = await requestJson<ProjectListResponse>('/projects')
  return response.data.list ?? []
}

const fetchProjectDetail = async (projectId: string) => {
  const response = await requestJson<ProjectDetailResponse>(`/projects/${projectId}`)
  return response.data
}

const createProject = async (payload: { code: string; title: string; requirements: ModuleGroup[] }) => {
  const response = await requestJson<CreateProjectResponse>('/projects', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
  return response.data
}

const generateTestcasesAsync = async (projectId: string, requirementIds?: string[]) => {
  const body = requirementIds && requirementIds.length > 0
    ? { requirement_ids: requirementIds, replace: true }
    : { replace: true }
  const response = await requestJson<GenerateTestcasesAsyncResponse>(
    `/projects/${projectId}/testcases/generate/async`,
    {
      method: 'POST',
      body: JSON.stringify(body)
    }
  )
  return response.data
}

const fetchTestcaseGenerateStatus = async (projectId: string) => {
  const response = await requestJson<GenerateTestcasesStatusResponse>(
    `/projects/${projectId}/testcases/generate/async`
  )
  return response.data
}

const deleteProject = async (projectId: string) => {
  const response = await requestJson<DeleteProjectResponse>(`/projects/${projectId}`, {
    method: 'DELETE'
  })
  return response.data
}

const updateRequirement = async (projectId: string, requirementId: string, payload: UpdateRequirementPayload) => {
  const response = await requestJson<{ updated: boolean }>(
    `/projects/${projectId}/requirements/${requirementId}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload)
    }
  )
  return response.data
}

const deleteRequirement = async (projectId: string, requirementId: string) => {
  const response = await requestJson<{ deleted: boolean }>(
    `/projects/${projectId}/requirements/${requirementId}`,
    {
      method: 'DELETE'
    }
  )
  return response.data
}

const updateTestcase = async (projectId: string, testcaseId: string, payload: UpdateTestcasePayload) => {
  const response = await requestJson<{ updated: boolean }>(
    `/projects/${projectId}/testcases/${testcaseId}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload)
    }
  )
  return response.data
}

const deleteTestcase = async (projectId: string, testcaseId: string) => {
  const response = await requestJson<{ deleted: boolean }>(
    `/projects/${projectId}/testcases/${testcaseId}`,
    {
      method: 'DELETE'
    }
  )
  return response.data
}

const createRequirement = async (projectId: string, payload: CreateRequirementPayload) => {
  const response = await requestJson<any>(
    `/projects/${projectId}/requirements`,
    {
      method: 'POST',
      body: JSON.stringify(payload)
    }
  )
  return response.data
}

const updateProject = async (projectId: string, payload: { code: string; title: string }) => {
  const response = await requestJson<{ updated: boolean }>(
    `/projects/${projectId}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload)
    }
  )
  return response.data
}

const exportTestcasesExcel = async (projectId: string) => {
  return requestBlob(`/projects/${projectId}/testcases/export`)
}

export {
  fetchProjectList,
  fetchProjectDetail,
  createProject,
  updateProject,
  generateTestcasesAsync,
  fetchTestcaseGenerateStatus,
  deleteProject,
  updateRequirement,
  deleteRequirement,
  createRequirement,
  updateTestcase,
  deleteTestcase,
  exportTestcasesExcel
}
