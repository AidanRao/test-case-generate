import { computed, onMounted, onUnmounted, ref, watch, type ComputedRef } from 'vue'
import {
  calculateProjectCoverage,
  fetchProjectCoverage,
  fetchProjectCoverageCalculationStatus,
  type CoverageAnalysisResponse,
  type CoverageCalculationStatus
} from '../api/projects'

type UseCoverageCalculationJobsOptions = {
  projectId: ComputedRef<string>
  onCompleted: (coverage: CoverageAnalysisResponse) => void
  onFailed: (error: string | null) => void
  pollingInterval?: number
}

export const useCoverageCalculationJobs = ({
  projectId,
  onCompleted,
  onFailed,
  pollingInterval = 2000
}: UseCoverageCalculationJobsOptions) => {
  const calculationStatus = ref<CoverageCalculationStatus | null>(null)
  const pollingTimer = ref<number | null>(null)
  const trackedJobId = ref<string | null>(null)

  const isCalculating = computed(() => calculationStatus.value?.active === true)

  const stopPolling = () => {
    if (pollingTimer.value !== null) {
      window.clearTimeout(pollingTimer.value)
      pollingTimer.value = null
    }
  }

  const handleTerminalStatus = async (
    status: CoverageCalculationStatus,
    requestedProjectId: string
  ) => {
    if (!status.job_id || trackedJobId.value !== status.job_id) return
    trackedJobId.value = null
    if (status.status === 'completed') {
      try {
        const coverage = await fetchProjectCoverage(requestedProjectId)
        if (projectId.value === requestedProjectId && coverage) {
          onCompleted(coverage)
        }
      } catch {
        if (projectId.value === requestedProjectId) {
          onFailed('coverage_fetch_failed')
        }
      }
    } else if (status.status === 'failed') {
      onFailed(status.error)
    }
  }

  const schedulePolling = () => {
    stopPolling()
    pollingTimer.value = window.setTimeout(refreshStatus, pollingInterval)
  }

  const refreshStatus = async () => {
    const requestedProjectId = projectId.value
    if (!requestedProjectId || requestedProjectId.startsWith('local-')) {
      calculationStatus.value = null
      trackedJobId.value = null
      stopPolling()
      return
    }
    try {
      const status = await fetchProjectCoverageCalculationStatus(requestedProjectId)
      if (projectId.value !== requestedProjectId) return
      calculationStatus.value = status
      if (status.active) {
        trackedJobId.value = status.job_id
        schedulePolling()
      } else {
        stopPolling()
        await handleTerminalStatus(status, requestedProjectId)
      }
    } catch {
      if (projectId.value !== requestedProjectId) return
      if (trackedJobId.value) {
        schedulePolling()
      } else {
        calculationStatus.value = null
        stopPolling()
      }
    }
  }

  const submitCalculation = async () => {
    if (isCalculating.value) return calculationStatus.value
    const job = await calculateProjectCoverage(projectId.value)
    calculationStatus.value = job
    trackedJobId.value = job.job_id
    schedulePolling()
    return job
  }

  watch(projectId, () => {
    stopPolling()
    calculationStatus.value = null
    trackedJobId.value = null
    refreshStatus()
  })

  onMounted(refreshStatus)
  onUnmounted(stopPolling)

  return {
    coverageCalculationStatus: calculationStatus,
    isCoverageCalculating: isCalculating,
    refreshCoverageCalculationStatus: refreshStatus,
    submitCoverageCalculation: submitCalculation,
    stopCoverageCalculationPolling: stopPolling
  }
}
