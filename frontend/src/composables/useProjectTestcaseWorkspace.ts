import { onMounted, watch, type ComputedRef } from 'vue'
import {
  createModule,
  createRequirement,
  deleteRequirement,
  deleteTestcase,
  updateRequirement,
  updateTestcase,
  type CreateRequirementPayload,
  type UpdateRequirementPayload,
  type UpdateTestcasePayload
} from '../api/projects'
import { useProjectDetail } from './useProjectDetail'
import { useLocalProjectMutations } from './useLocalProjectMutations'
import { useTestcaseGenerationJobs } from './useTestcaseGenerationJobs'

type UseProjectTestcaseWorkspaceOptions = {
  projectId: ComputedRef<string>
  fallbackToFirstProject?: boolean
  includeQuality?: boolean
}

export const useProjectTestcaseWorkspace = ({
  projectId,
  fallbackToFirstProject = false,
  includeQuality = false
}: UseProjectTestcaseWorkspaceOptions) => {
  const projectDetail = useProjectDetail({
    projectId,
    fallbackToFirstProject,
    includeQuality
  })
  const generationJobs = useTestcaseGenerationJobs({
    projectId,
    refreshProject: projectDetail.loadProjectDetail
  })
  const localMutations = useLocalProjectMutations({
    projectId,
    localProjects: projectDetail.localProjects
  })

  const saveRequirement = async (
    requirementId: string,
    payload: UpdateRequirementPayload
  ) => {
    const result = await updateRequirement(projectId.value, requirementId, payload)
    await projectDetail.loadProjectDetail()
    return result
  }

  const removeRequirement = async (requirementId: string) => {
    const result = await deleteRequirement(projectId.value, requirementId)
    await projectDetail.loadProjectDetail()
    return result
  }

  const addRequirement = async (payload: CreateRequirementPayload) => {
    const result = await createRequirement(projectId.value, payload)
    await projectDetail.loadProjectDetail()
    return result
  }

  const addModule = async (name: string) => {
    const result = await createModule(projectId.value, name)
    await projectDetail.loadProjectDetail()
    return result
  }

  const saveTestcase = async (testcaseId: string, payload: UpdateTestcasePayload) => {
    const result = await updateTestcase(projectId.value, testcaseId, payload)
    await projectDetail.loadProjectDetail()
    return result
  }

  const removeTestcase = async (testcaseId: string) => {
    const result = await deleteTestcase(projectId.value, testcaseId)
    await projectDetail.loadProjectDetail()
    return result
  }

  watch(projectId, () => {
    projectDetail.loadProjectDetail()
  })

  onMounted(() => {
    projectDetail.loadProjectDetail()
  })

  return {
    ...projectDetail,
    ...generationJobs,
    ...localMutations,
    refreshProject: projectDetail.loadProjectDetail,
    saveRequirement,
    removeRequirement,
    addRequirement,
    addModule,
    saveTestcase,
    removeTestcase
  }
}
