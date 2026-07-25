<template>
  <div class="flex h-screen gap-6 bg-slate-50 p-6">
    <div class="flex w-[380px] min-w-[320px] flex-col gap-4">
      <div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="flex items-center gap-3 border-b border-slate-100 px-5 py-4">
          <button
            @click="goBack"
            class="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          >
            <el-icon><ArrowLeft /></el-icon>
          </button>
          <div class="min-w-0">
            <p class="text-xs font-medium text-sky-600">项目</p>
            <p class="truncate text-base font-semibold text-slate-800">{{ projectName }}</p>
          </div>
          <div class="ml-auto flex items-center gap-2">
          <button
            v-if="showGenerateTestcasesButton"
            type="button"
            @click="handleProjectGenerateTestcases"
            class="rounded-full bg-sky-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-sky-700"
          >
            生成测试用例
          </button>
            <button
              class="rounded-full border px-3 py-1 text-xs font-semibold transition"
              :class="isReadOnlyProject ? 'cursor-not-allowed border-slate-100 text-slate-300' : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'"
              :disabled="isReadOnlyProject"
              type="button"
            >
              需求补全
            </button>
          </div>
        </div>
        <div class="flex min-h-0 flex-1 flex-col gap-5 px-5 py-4">
          <el-popover
            :visible="requirementStatsOpen"
            placement="bottom-start"
            :width="280"
            :show-arrow="false"
            :teleported="true"
            popper-class="!rounded-xl !border-slate-200 !p-3 !shadow-lg"
          >
            <template #reference>
              <div
                class="flex w-fit cursor-default items-center gap-2"
                @mouseenter="showRequirementStats"
                @mouseleave="hideRequirementStats"
              >
                <span class="text-xs font-medium text-slate-400 transition hover:text-slate-600">
                  需求类型
                </span>
                <span class="rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-700 transition hover:bg-sky-100">
                  需求总数 {{ requirements.length }}
                </span>
              </div>
            </template>
            <div
              id="requirement-type-stats-popover"
              role="dialog"
              aria-label="需求类型统计"
            >
              <div class="mb-2 text-xs font-semibold text-slate-700">需求类型统计</div>
              <div v-if="requirementTypeStats.length" class="flex flex-wrap gap-2">
                <span
                  v-for="item in requirementTypeStats"
                  :key="item.type"
                  class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                >
                  {{ item.type }} {{ item.count }}
                </span>
              </div>
              <p v-else class="text-xs text-slate-400">暂无需求</p>
            </div>
          </el-popover>
          <RequirementList
            :items="requirementItems"
            :selected-index="selectedRequirementIndex"
            @select="openRequirementDetail"
          />
        </div>
      </div>

      <QualityInfoCard
        :data="qualityInfo"
        :coverage="coverageInfo"
        :coverage-detail="coverageDetail"
        :generation-status="generationStatus"
        @open-requirement="openRequirementFromCoverage"
      />
    </div>

    <div class="relative flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <TestCaseBoard
        :data="graphData"
        @open-requirement="openRequirementFromBoard"
        @open-testcase="openTestcaseDetail"
        @open-module="openModuleRequirements"
      />
      <div class="absolute left-5 top-5 flex gap-2">
        <button
          v-if="showExportButton"
          type="button"
          class="flex items-center gap-1 rounded-full bg-sky-600 px-3 py-1 text-xs font-semibold text-white shadow-sm transition hover:bg-sky-700"
          @click="openExportDialog"
        >
          <el-icon class="text-sm"><Download /></el-icon>
          导出测试用例
        </button>
      </div>
      <div class="absolute right-5 top-5 flex gap-2 rounded-lg bg-white/90 px-3 py-2 shadow-sm backdrop-blur-sm">
        <span class="inline-flex items-center rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">模块</span>
        <span class="inline-flex items-center rounded bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">需求</span>
        <span class="inline-flex items-center rounded bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-500/10">测试项</span>
      </div>
    </div>
  </div>

  <RequirementDetailDialog
    v-model="detailVisible"
    :requirement="detailRequirement"
    :testcases="detailTestcases"
    :is-generating="detailRequirementGenerating"
    :generation-disabled="isGenerationActive"
    :read-only="isReadOnlyProject || isGenerationActive"
    @open-testcase="openTestcaseDetail"
    @save="handleRequirementSave"
    @delete="handleRequirementDelete"
    @generate-testcases="handleRequirementGenerateTestcases"
  />

  <TestCaseDetailDialog
    v-model="testcaseDetailVisible"
    :testcase="testcaseDetail"
    :read-only="isGenerationActive"
    @save="handleTestcaseSave"
    @delete="handleTestcaseDelete"
  />

  <ExportTestcasesDialog v-model="exportDialogVisible" @export="handleExport" />

</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Download } from '@element-plus/icons-vue'
import { buildRequirements, type Requirement } from '../data/projectStore'
import TestCaseBoard from '../components/TestCaseBoard.vue'
import type { BoardNode } from '../components/TestCaseBoard.vue'
import RequirementList from '../components/RequirementList.vue'
import RequirementDetailDialog from '../components/RequirementDetailDialog.vue'
import type { RequirementDetailItem } from '../components/RequirementDetailDialog.vue'
import QualityInfoCard from '../components/QualityInfoCard.vue'
import TestCaseDetailDialog from '../components/TestCaseDetailDialog.vue'
import type { RequirementTestCaseItem, TestCaseDetailItem } from '../data/testcase'
import ExportTestcasesDialog from '../components/ExportTestcasesDialog.vue'
import { useAppFeedback } from '../composables/useAppFeedback'
import { useProjectTestcaseWorkspace } from '../composables/useProjectTestcaseWorkspace'
import {
  buildTestcases,
  getRequirementIdentity,
  type RequirementWithTestcases
} from '../composables/useRequirementTestcases'
import { useTestcaseExport } from '../composables/useTestcaseExport'
import type { QualityInfoResponse } from '../api/projects'


const router = useRouter()
const route = useRoute()
const { notify, confirm } = useAppFeedback()

const projectId = computed(() => String(route.params.projectId ?? ''))
type RequirementWithCases = RequirementWithTestcases & { module: string }

const {
  remoteQualityInfo,
  isRemoteProject,
  moduleGroups,
  projectName,
  isReadOnlyProject,
  generationStatus,
  activeRequirementIds,
  isGenerationActive,
  submitGeneration,
  saveRequirement,
  removeRequirement,
  saveTestcase,
  removeTestcase
} = useProjectTestcaseWorkspace({
  projectId,
  fallbackToFirstProject: true,
  includeQuality: true
})

const requirements = computed<RequirementWithCases[]>(() => buildRequirements(moduleGroups.value) as RequirementWithCases[])
const requirementItems = computed(() => {
  return requirements.value.map((item) => {
    const testcaseCount = buildTestcases(item).length
    const requirementId = String(item.ID || item.code || item.title)
    return {
      ...item,
      testcaseCount,
      isGenerating: activeRequirementIds.value.has(requirementId)
    }
  })
})

const selectedRequirementIndex = ref(0)
const requirementTypeStats = computed(() => {
  const stats = new Map<string, number>()
  requirements.value.forEach((item) => {
    const type = item.type || '未知类型'
    stats.set(type, (stats.get(type) ?? 0) + 1)
  })
  return Array.from(stats.entries()).map(([type, count]) => ({ type, count }))
})
const requirementStatsOpen = ref(false)

const showRequirementStats = () => {
  requirementStatsOpen.value = true
}

const hideRequirementStats = () => {
  requirementStatsOpen.value = false
}
const hasAnyTestcases = computed(() => requirements.value.some((item) => buildTestcases(item).length > 0))
const showGenerateTestcasesButton = computed(() => {
  return isRemoteProject.value && !hasAnyTestcases.value && !isGenerationActive.value
})
const showExportButton = computed(() => hasAnyTestcases.value)

const coverageInfo = computed(() => {
  const total = requirements.value.length
  const covered = requirements.value.filter((item) => buildTestcases(item).length > 0).length
  const rate = total === 0 ? 0 : covered / total
  return {
    total,
    covered,
    rate
  }
})

const coverageDetail = computed(() =>
  moduleGroups.value.map((group, index) => {
    const items = group.requirements.map((item) => {
      const requirement = { ...item, module: group.module } as Requirement
      const testcaseCount = buildTestcases(requirement).length
      const requirementId = requirement.ID || requirement.code || requirement.title
      return {
        id: requirementId,
        title: requirement.title,
        covered: testcaseCount > 0,
        testcaseCount,
        requirement
      }
    })
    const coveredCount = items.filter((item) => item.covered).length
    return {
      moduleId: `M-${String(index + 1).padStart(2, '0')}`,
      moduleTitle: group.module,
      coveredCount,
      totalCount: items.length,
      items
    }
  })
)

const detailVisible = ref(false)
const detailRequirement = ref<Requirement | null>(null)
const detailTestcases = ref<RequirementTestCaseItem[]>([])
const detailRequirementGenerating = computed(() => {
  const requirement = detailRequirement.value
  if (!requirement) return false
  const requirementId = String(requirement.ID || requirement.code || requirement.title)
  return activeRequirementIds.value.has(requirementId)
})

const testcaseDetail = ref<TestCaseDetailItem | null>(null)
const testcaseDetailVisible = ref(false)

const selectRequirement = (index: number) => {
  selectedRequirementIndex.value = index
}

const openRequirementDetail = (index: number) => {
  selectRequirement(index)
  const requirement = requirements.value[index] ?? null
  detailRequirement.value = requirement
  detailTestcases.value = buildTestcases(detailRequirement.value)
  detailVisible.value = true
}

const openRequirementFromBoard = (requirement: RequirementWithCases) => {
  const targetIndex = requirements.value.findIndex((item) => {
    if (requirement.ID || requirement.code) {
      return item.ID === requirement.ID || item.code === requirement.code
    }
    return item.title === requirement.title
  })
  if (targetIndex >= 0) {
    selectRequirement(targetIndex)
  }
  detailRequirement.value = requirement
  detailTestcases.value = buildTestcases(requirement)
  detailVisible.value = true
}

const openRequirementFromCoverage = (requirement: RequirementWithCases) => {
  openRequirementFromBoard(requirement)
}

const openTestcaseDetail = (item: TestCaseDetailItem) => {
  testcaseDetail.value = item
  testcaseDetailVisible.value = true
}

const refreshOpenRequirementTestcases = (requirementIdentity: string, testcaseId?: string) => {
  const refreshedRequirement = requirements.value.find(
    (item) => getRequirementIdentity(item) === requirementIdentity
  ) ?? null
  if (!refreshedRequirement) {
    return
  }

  detailRequirement.value = refreshedRequirement
  detailTestcases.value = buildTestcases(refreshedRequirement)
  if (testcaseId) {
    testcaseDetail.value = detailTestcases.value.find(
      (item) => String(item.id) === String(testcaseId)
    ) ?? null
  }
}

const openModuleRequirements = (module: string) => {
  if (!module) {
    return
  }
  const targetRoute = router.resolve({
    name: 'module-requirements',
    params: {
      projectId: projectId.value,
      moduleName: module
    },
    query: route.query
  })
  window.open(targetRoute.href, '_blank', 'noopener,noreferrer')
}

const handleRequirementSave = async (payload: RequirementDetailItem) => {
  if (isReadOnlyProject.value) {
    return
  }
  if (!isRemoteProject.value) {
    notify({ message: '本地项目暂不支持修改需求' })
    return
  }
  const requirementId = payload.ID || payload.code
  if (!requirementId) {
    notify({ message: '需求缺少可用的标识', tone: 'error' })
    return
  }
  try {
    await saveRequirement(requirementId, {
      title: payload.title,
      type: payload.type,
      content: payload.content
    })
    const shouldGenerate = await confirm({
      title: '生成测试用例',
      message: '是否基于最新需求重新生成测试用例？已生成的用例将被替换。',
      confirmText: '生成'
    })
    if (shouldGenerate) {
      try {
        await submitGeneration([requirementId])
      } catch {
        notify({ message: '测试用例生成任务提交失败，请稍后重试', tone: 'error' })
      }
    }
    detailVisible.value = false
  } catch {
    notify({ message: '需求更新失败，请稍后重试', tone: 'error' })
  }
}

const handleRequirementDelete = async (payload: RequirementDetailItem) => {
  if (isReadOnlyProject.value) {
    return
  }
  if (!isRemoteProject.value) {
    notify({ message: '本地项目暂不支持删除需求' })
    return
  }
  const requirementId = payload.ID || payload.code
  if (!requirementId) {
    notify({ message: '需求缺少可用的标识', tone: 'error' })
    return
  }
  const confirmed = await confirm({
    title: '删除需求',
    message: '确定要删除该需求吗？删除后该需求的所有测试用例也将被删除，无法恢复。',
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger'
  })
  if (!confirmed) return
  try {
    await removeRequirement(requirementId)
    detailVisible.value = false
  } catch {
    notify({ message: '需求删除失败，请稍后重试', tone: 'error' })
  }
}

const handleRequirementGenerateTestcases = async () => {
  if (!isRemoteProject.value) {
    notify({ message: '本地项目暂不支持生成测试用例' })
    return
  }
  const requirement = detailRequirement.value
  const requirementId = requirement?.ID || requirement?.code
  if (!requirementId) {
    notify({ message: '需求缺少可用的标识', tone: 'error' })
    return
  }
  const confirmed = await confirm({
    title: '生成测试用例',
    message: '将为该需求重新生成测试用例，已生成的用例将被替换。',
    confirmText: '生成'
  })
  if (!confirmed) return
  try {
    await submitGeneration([requirementId])
  } catch {
    notify({ message: '测试用例生成任务提交失败，请稍后重试', tone: 'error' })
  }
}

const handleProjectGenerateTestcases = async () => {
  if (!isRemoteProject.value) {
    notify({ message: '本地项目暂不支持生成测试用例' })
    return
  }
  if (requirements.value.length === 0) {
    notify({ message: '暂无需求，无法生成测试用例' })
    return
  }
  const confirmed = await confirm({
    title: '生成测试用例',
    message: '将根据当前需求生成测试用例，已生成的用例将被替换。',
    confirmText: '生成'
  })
  if (!confirmed) return
  try {
    await submitGeneration()
  } catch {
    notify({ message: '测试用例生成任务提交失败，请稍后重试', tone: 'error' })
  }
}
const handleTestcaseSave = async (payload: TestCaseDetailItem) => {
  if (!isRemoteProject.value) {
    notify({ message: '本地项目暂不支持修改测试用例' })
    return
  }
  if (!payload.id) {
    notify({ message: '测试用例缺少可用的标识', tone: 'error' })
    return
  }
  const requirementIdentity = getRequirementIdentity(
    detailRequirement.value as RequirementWithTestcases | null
  )
  try {
    await saveTestcase(payload.id, {
      title: payload.title,
      code: payload.code,
      type: payload.type,
      scenario_type: payload.scenario_type,
      priority: payload.priority,
      test_steps: payload.test_steps ?? [],
      test_target_desc: payload.test_target_desc,
      verify_method: payload.verify_method
    })
    refreshOpenRequirementTestcases(requirementIdentity, payload.id)
    testcaseDetailVisible.value = false
  } catch {
    notify({ message: '测试用例更新失败，请稍后重试', tone: 'error' })
  }
}

const handleTestcaseDelete = async (payload: TestCaseDetailItem) => {
  if (!isRemoteProject.value) {
    notify({ message: '本地项目暂不支持删除测试用例' })
    return
  }
  if (!payload.id) {
    notify({ message: '测试用例缺少可用的标识', tone: 'error' })
    return
  }
  const confirmed = await confirm({
    title: '删除测试用例',
    message: '确定要删除该测试用例吗？删除后无法恢复。',
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger'
  })
  if (!confirmed) return
  try {
    await removeTestcase(payload.id as string)
    testcaseDetailVisible.value = false
  } catch {
    notify({ message: '测试用例删除失败，请稍后重试', tone: 'error' })
  }
}

const goBack = () => {
  const portalProjectId = typeof route.query.portal_project_id === 'string'
    ? route.query.portal_project_id
    : null
  router.push({
    name: 'projects',
    query: portalProjectId ? { portal_project_id: portalProjectId } : {}
  })
}


const computedReqTypeStats = computed(() => {
  const fixedTypes = [
    '功能测试',
    '可靠性测试',
    '安全性测试',
    '强度测试',
    '性能测试',
    '接口测试',
    '数据处理测试',
    '边界测试',
    '容量测试',
    '余量测试'
  ]
  const typeStats = new Map<string, number>(fixedTypes.map((type) => [type, 0]))
  requirements.value.forEach((item) => {
    const testcases = buildTestcases(item)
    testcases.forEach((testcase) => {
      const key = testcase.type || '功能测试'
      typeStats.set(key, (typeStats.get(key) ?? 0) + 1)
    })
  })
  return Object.fromEntries(typeStats)
})

const fallbackQualityInfo = computed<QualityInfoResponse>(() => {
  let successCount = 0
  requirements.value.forEach((item) => {
    if (buildTestcases(item).length > 0) {
      successCount += 1
    }
  })
  return {
    fail_count: 0,
    iterations: hasAnyTestcases.value ? 1 : 0,
    duration: 0,
    success_count: successCount
  }
})

const qualityInfo = computed(() => ({
  ...(remoteQualityInfo.value ?? fallbackQualityInfo.value),
  req_type_stats: computedReqTypeStats.value
}))

const nodeSizes = {
  root: { width: 200, height: 34 },
  feature: { width: 190, height: 32 },
  subfeature: { width: 220, height: 32 },
  testcase: { width: 200, height: 30 }
}

const { exportDialogVisible, openExportDialog, handleExport } = useTestcaseExport({
  moduleGroups,
  projectName,
  projectId,
  buildTestcases
})

const buildTestcaseNodes = (
  testcases: RequirementTestCaseItem[],
  moduleIndex: number,
  requirementIndex: number
): BoardNode[] => {
  if (testcases.length === 0) {
    return []
  }

  return testcases.map((item, index) => ({
    id: `tc-${moduleIndex}-${requirementIndex}-${index}`,
    type: 'testcase',
    label: item.title || `测试点 ${index + 1}`,
    width: nodeSizes.testcase.width,
    height: nodeSizes.testcase.height,
    testcase: item
  }))
}

const graphData = computed<BoardNode>(() => {
  const moduleNodes: BoardNode[] = moduleGroups.value.map((group, moduleIndex) => ({
    id: `m-${moduleIndex}`,
    type: 'feature',
    label: group.module,
    width: nodeSizes.feature.width,
    height: nodeSizes.feature.height,
    children: group.requirements.map((req, requirementIndex): BoardNode => {
      const requirement = { ...req, module: group.module } as RequirementWithCases
      const testcases = buildTestcases(requirement)
      return {
        id: `r-${moduleIndex}-${requirementIndex}`,
        type: 'subfeature',
        label: req.title,
        width: nodeSizes.subfeature.width,
        height: nodeSizes.subfeature.height,
        requirement,
        children: buildTestcaseNodes(testcases, moduleIndex, requirementIndex)
      }
    })
  }))

  return {
    id: 'root',
    type: 'root',
    label: projectName.value,
    width: nodeSizes.root.width,
    height: nodeSizes.root.height,
    children: moduleNodes
  }
})

watch(requirements, (nextRequirements) => {
  if (nextRequirements.length === 0) {
    selectedRequirementIndex.value = 0
    return
  }
  if (selectedRequirementIndex.value >= nextRequirements.length) {
    selectedRequirementIndex.value = 0
  }
}, { immediate: true })

</script>
