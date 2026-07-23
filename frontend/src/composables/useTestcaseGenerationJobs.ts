import { computed, onMounted, onUnmounted, ref, watch, type ComputedRef } from 'vue'
import {
  createTestcaseGenerationJob,
  fetchProjectTestcaseGenerationStatus,
  type TestcaseGenerationStatus
} from '../api/projects'

type UseTestcaseGenerationJobsOptions = {
  projectId: ComputedRef<string>
  refreshProject: () => Promise<unknown>
  pollingInterval?: number
}

export const useTestcaseGenerationJobs = ({
  projectId,
  refreshProject,
  pollingInterval = 5000
}: UseTestcaseGenerationJobsOptions) => {
  const generationStatus = ref<TestcaseGenerationStatus | null>(null)
  const pollingTimer = ref<number | null>(null)

  const activeRequirementIds = computed(
    () => new Set(generationStatus.value?.active_requirement_ids ?? [])
  )
  const isGenerationActive = computed(() => generationStatus.value?.active === true)

  const stopPolling = () => {
    if (pollingTimer.value) {
      window.clearTimeout(pollingTimer.value)
      pollingTimer.value = null
    }
  }

  const schedulePolling = () => {
    stopPolling()
    pollingTimer.value = window.setTimeout(async () => {
      await Promise.allSettled([refreshProject(), refreshStatus()])
    }, pollingInterval)
  }

  const refreshStatus = async () => {
    const requestedProjectId = projectId.value
    if (!requestedProjectId || requestedProjectId.startsWith('local-')) {
      generationStatus.value = null
      stopPolling()
      return
    }
    try {
      const status = await fetchProjectTestcaseGenerationStatus(requestedProjectId)
      if (projectId.value !== requestedProjectId) return
      generationStatus.value = status
      if (status.active) {
        schedulePolling()
      } else {
        stopPolling()
      }
    } catch {
      generationStatus.value = null
      stopPolling()
    }
  }

  const submitGeneration = async (requirementIds?: string[]) => {
    const job = await createTestcaseGenerationJob(projectId.value, requirementIds)
    generationStatus.value = job
    await refreshProject()
    await refreshStatus()
    return job
  }

  watch(projectId, () => {
    stopPolling()
    refreshStatus()
  })

  onMounted(() => {
    refreshStatus()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    generationStatus,
    activeRequirementIds,
    isGenerationActive,
    refreshGenerationStatus: refreshStatus,
    submitGeneration,
    stopGenerationStatusPolling: stopPolling
  }
}
