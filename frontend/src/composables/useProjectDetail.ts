import { computed, ref, type ComputedRef } from 'vue'
import { fetchProjectDetail, fetchProjectQuality, type QualityInfoResponse } from '../api/projects'
import { loadProjects, type ModuleGroup, type ProjectRecord } from '../data/projectStore'
import {
  mapRemoteModules,
  type ModuleGroupWithTestcases
} from './useRequirementTestcases'

type UseProjectDetailOptions = {
  projectId: ComputedRef<string>
  fallbackToFirstProject?: boolean
  includeQuality?: boolean
}

const emptyProject: ProjectRecord = {
  id: 'local-0',
  name: '暂无项目',
  code: '',
  modules: []
}

export const useProjectDetail = ({
  projectId,
  fallbackToFirstProject = false,
  includeQuality = false
}: UseProjectDetailOptions) => {
  const localProjects = ref<ProjectRecord[]>(loadProjects())
  const remoteModules = ref<ModuleGroupWithTestcases[] | null>(null)
  const remoteProjectTitle = ref<string | null>(null)
  const remoteProjectSource = ref<'local' | 'uniportal' | null>(null)
  const remoteQualityInfo = ref<QualityInfoResponse | null>(null)
  const isLoading = ref(false)
  const loadError = ref('')

  const isRemoteProject = computed(() => !!projectId.value && !projectId.value.startsWith('local-'))

  const currentProject = computed<ProjectRecord | null>(() => {
    const matchedProject = localProjects.value.find((item) => item.id === projectId.value)
    if (matchedProject) {
      return matchedProject
    }
    if (!fallbackToFirstProject) {
      return null
    }
    return localProjects.value[0] ?? emptyProject
  })

  const moduleGroups = computed<ModuleGroup[]>(() => (
    remoteModules.value ?? currentProject.value?.modules ?? []
  ) as ModuleGroup[])

  const projectName = computed(() => remoteProjectTitle.value ?? currentProject.value?.name ?? '项目')

  const isReadOnlyProject = computed(() =>
    remoteProjectSource.value === 'uniportal' || currentProject.value?.source === 'uniportal'
  )

  const loadProjectDetail = async () => {
    localProjects.value = loadProjects()
    remoteModules.value = null
    remoteProjectTitle.value = null
    remoteProjectSource.value = null
    remoteQualityInfo.value = null
    loadError.value = ''

    if (!isRemoteProject.value) {
      return
    }

    isLoading.value = true
    try {
      const detail = await fetchProjectDetail(projectId.value)
      remoteProjectTitle.value = detail.title
      remoteProjectSource.value = detail.source
      remoteModules.value = mapRemoteModules(detail.requirements ?? [], detail.modules ?? [])
      if (includeQuality) {
        remoteQualityInfo.value = await fetchProjectQuality(projectId.value).catch(() => null)
      }
    } catch {
      if (!currentProject.value) {
        loadError.value = '项目详情加载失败，请稍后重试'
      }
    } finally {
      isLoading.value = false
    }
  }

  return {
    localProjects,
    remoteModules,
    remoteProjectTitle,
    remoteProjectSource,
    remoteQualityInfo,
    isLoading,
    loadError,
    isRemoteProject,
    currentProject,
    moduleGroups,
    projectName,
    isReadOnlyProject,
    loadProjectDetail
  }
}
