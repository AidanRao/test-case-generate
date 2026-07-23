import type { ModuleGroup } from '../data/projectStore'
import type { TestCaseItem } from '../data/testcase'
import { requestBlob, requestJson } from './http'

type ProjectListResponse = {
  list: Array<{
    id: string
    code: string
    title: string
    source: 'local' | 'uniportal'
    module_count: number
    requirement_count: number
  }>
}

type ProjectDetailResponse = {
  id: string
  code: string
  title: string
  source: 'local' | 'uniportal'
  modules?: string[]
  requirements: Array<{
    id: string
    title: string
    type: string
    code: string
    content: string
    project_id: string
    module: string
    testcases: TestCaseItem[]
  }>
}

type CreateProjectResponse = {
  id: string
}

export type TestcaseGenerationStatus = {
  job_id: string | null
  project_id: string
  requirement_ids: string[]
  active_requirement_ids: string[]
  status: 'idle' | 'pending' | 'running' | 'completed' | 'failed'
  active: boolean
  created_at: number | null
  started_at: number | null
  finished_at: number | null
  current_requirement_id: string | null
  completed_requirement_ids: string[]
  completed_count: number
  total_count: number
  error: string | null
}

export type QualityInfoResponse = {
  success_count: number
  fail_count: number
  iterations: number
  duration: number
}

type DeleteProjectResponse = {
  deleted: boolean
}

type CreateModuleResponse = {
  name: string
}

export type UpdateRequirementPayload = {
  title: string
  type: string
  content: string
  module?: string
}

export type UpdateTestcasePayload = Pick<
  TestCaseItem,
  | 'title'
  | 'code'
  | 'type'
  | 'scenario_type'
  | 'priority'
  | 'test_steps'
  | 'test_target_desc'
  | 'verify_method'
>

export type CreateRequirementPayload = {
  title: string
  type: string
  code: string
  content: string
  module: string
}

const fetchProjectList = async (portalProjectId?: string | null) => {
  const suffix = portalProjectId
    ? `?portal_project_id=${encodeURIComponent(portalProjectId)}`
    : ''
  const response = await requestJson<ProjectListResponse>(`/projects${suffix}`)
  return response.data.list ?? []
}

const fetchProjectDetail = async (projectId: string) => {
  const response = await requestJson<ProjectDetailResponse>(`/projects/${projectId}`, {
    cache: 'no-store'
  })
  return response.data
}

const createProject = async (payload: { code: string; title: string; requirements: ModuleGroup[] }) => {
  const response = await requestJson<CreateProjectResponse>('/projects', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
  return response.data
}

const createTestcaseGenerationJob = async (projectId: string, requirementIds?: string[]) => {
  const body = requirementIds && requirementIds.length > 0
    ? { requirement_ids: requirementIds, replace: true }
    : { replace: true }
  const response = await requestJson<TestcaseGenerationStatus>(
    `/projects/${projectId}/testcase-generation-jobs`,
    {
      method: 'POST',
      body: JSON.stringify(body)
    }
  )
  return response.data
}

const fetchProjectTestcaseGenerationStatus = async (projectId: string) => {
  const response = await requestJson<TestcaseGenerationStatus>(
    `/projects/${projectId}/testcase-generation-jobs`
  )
  return response.data
}

const fetchProjectQuality = async (projectId: string) => {
  const response = await requestJson<QualityInfoResponse>(`/projects/${projectId}/quality`)
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

const createModule = async (projectId: string, name: string) => {
  const response = await requestJson<CreateModuleResponse>(
    `/projects/${projectId}/modules`,
    {
      method: 'POST',
      body: JSON.stringify({ name })
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
  fetchProjectQuality,
  createProject,
  updateProject,
  createTestcaseGenerationJob,
  fetchProjectTestcaseGenerationStatus,
  deleteProject,
  updateRequirement,
  deleteRequirement,
  createRequirement,
  createModule,
  updateTestcase,
  deleteTestcase,
  exportTestcasesExcel
}
