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
            <el-tooltip
              content="根据当前需求，智能推断出隐藏的需求，完善需求文档"
              placement="top"
              :show-after="200"
            >
              <button
                class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                type="button"
              >
                需求补全
              </button>
            </el-tooltip>
          </div>
        </div>
        <div class="flex min-h-0 flex-1 flex-col gap-5 px-5 py-4">
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <p class="text-xs font-medium text-slate-400">需求类型统计</p>
              <span class="rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-700">
                需求数 {{ requirements.length }}
              </span>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="item in requirementTypeStats"
                :key="item.type"
                class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
              >
                {{ item.type }} {{ item.count }}
              </span>
              <span
                v-if="requirementTypeStats.length === 0"
                class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500"
              >
                暂无需求
              </span>
            </div>
          </div>
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
        :generation-status="effectiveGenerationStatus"
        @open-requirement="openRequirementFromCoverage"
      />
    </div>

    <div class="relative flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <TestCaseBoard
        :data="graphData"
        @open-requirement="openRequirementFromBoard"
        @open-testcase="openTestcaseDetail"
        @create-requirement="handleCreateRequirement"
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
    @open-testcase="openTestcaseDetail"
    @save="handleRequirementSave"
    @delete="handleRequirementDelete"
    @generate-testcases="handleRequirementGenerateTestcases"
  />

  <TestCaseDetailDialog
    v-model="testcaseDetailVisible"
    :testcase="testcaseDetail"
    @save="handleTestcaseSave"
    @delete="handleTestcaseDelete"
  />

  <ExportTestcasesDialog v-model="exportDialogVisible" @export="handleExport" />

  <ConfirmDialog
    v-model="confirmVisible"
    :title="confirmTitle"
    :message="confirmMessage"
    :confirm-text="confirmConfirmText"
    :cancel-text="confirmCancelText"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  />

  <!-- 新增需求弹窗 -->
  <CreateRequirementDialog
    v-model="createRequirementVisible"
    :default-module="selectedModule"
    @create="handleRequirementCreate"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Download } from '@element-plus/icons-vue'
import { buildRequirements, loadProjects, type ModuleGroup, type Requirement } from '../data/projectStore'
import TestCaseBoard from '../components/TestCaseBoard.vue'
import type { BoardNode } from '../components/TestCaseBoard.vue'
import RequirementList from '../components/RequirementList.vue'
import RequirementDetailDialog from '../components/RequirementDetailDialog.vue'
import type { RequirementDetailItem, RequirementTestCaseItem } from '../components/RequirementDetailDialog.vue'
import CreateRequirementDialog from '../components/CreateRequirementDialog.vue'
import QualityInfoCard from '../components/QualityInfoCard.vue'
import TestCaseDetailDialog from '../components/TestCaseDetailDialog.vue'
import type { TestCaseDetailItem } from '../components/TestCaseDetailDialog.vue'
import ExportTestcasesDialog from '../components/ExportTestcasesDialog.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { useConfirmDialog } from '../composables/useConfirmDialog'
import { useTestcaseExport } from '../composables/useTestcaseExport'
import {
  deleteRequirement,
  deleteTestcase,
  fetchProjectDetail,
  fetchTestcaseGenerateStatus,
  generateTestcasesAsync,
  updateRequirement,
  updateTestcase,
  createRequirement,
} from '../api/projects'
import type { CreateRequirementPayload } from '../api/projects'

// 重命名为与API类型一致
interface CreateRequirementForm extends CreateRequirementPayload {}


const router = useRouter()
const route = useRoute()

const projectId = computed(() => String(route.params.projectId ?? ''))
const currentProject = computed(() => {
  const list = loadProjects()
  if (list.length === 0) {
    return {
      id: 'local-0',
      name: '暂无项目',
      code: '',
      modules: [] as ModuleGroup[]
    }
  }
  return list.find((item) => item.id === projectId.value) ?? list[0]
})

type RequirementWithCases = Requirement & { testcases?: RequirementTestCaseItem[]; hasRemoteTestcases?: boolean }
type RemoteRequirement = ModuleGroup['requirements'][number] & {
  testcases?: RequirementTestCaseItem[]
  hasRemoteTestcases?: boolean
  ID?: string
}
type RemoteModuleGroup = ModuleGroup & { requirements: RemoteRequirement[] }

const remoteModules = ref<RemoteModuleGroup[] | null>(null)
const remoteProjectTitle = ref<string | null>(null)

const moduleGroups = computed<ModuleGroup[]>(() => remoteModules.value ?? currentProject.value?.modules ?? [])
const requirements = computed<RequirementWithCases[]>(() => buildRequirements(moduleGroups.value) as RequirementWithCases[])
const requirementItems = computed(() => {
  const isRunning = generationStatus.value?.status === 'running'
  return requirements.value.map((item) => {
    const testcaseCount = buildTestcases(item).length
    return {
      ...item,
      testcaseCount,
      isGenerating: isRunning && testcaseCount === 0
    }
  })
})

const requirementGeneratingMap = computed(() => {
  const map = new Map<string, boolean>()
  requirementItems.value.forEach((item) => {
    const requirementId = item.ID || item.code || item.title
    map.set(requirementId, Boolean(item.isGenerating))
  })
  return map
})
const projectName = computed(() => remoteProjectTitle.value ?? currentProject.value?.name ?? '项目')
const selectedRequirementIndex = ref(0)
const requirementTypeStats = computed(() => {
  const stats = new Map<string, number>()
  requirements.value.forEach((item) => {
    const type = item.type || '未知类型'
    stats.set(type, (stats.get(type) ?? 0) + 1)
  })
  return Array.from(stats.entries()).map(([type, count]) => ({ type, count }))
})
const hasAnyTestcases = computed(() => requirements.value.some((item) => buildTestcases(item).length > 0))
const showGenerateTestcasesButton = computed(() => {
  const status = generationStatus.value?.status
  return isRemoteProject.value && !hasAnyTestcases.value && status !== 'running'
})
const effectiveGenerationStatus = computed(() => {
  const status = generationStatus.value
  if (!status) return status
  if (status.status === 'idle' && hasAnyTestcases.value) {
    return { ...status, status: 'done' as const }
  }
  return status
})
const showExportButton = computed(() => effectiveGenerationStatus.value?.status === 'done' && hasAnyTestcases.value)

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
const detailRequirementGenerating = ref(false)

const testcaseDetail = ref<TestCaseDetailItem | null>(null)
const testcaseDetailVisible = ref(false)

// 新增需求相关
const createRequirementVisible = ref(false)
const selectedModule = ref('')
const {
  confirmVisible,
  confirmTitle,
  confirmMessage,
  confirmConfirmText,
  confirmCancelText,
  openConfirm,
  handleConfirm,
  handleCancel
} = useConfirmDialog()
const isRemoteProject = computed(() => !!projectId.value && !projectId.value.startsWith('local-'))

const selectRequirement = (index: number) => {
  selectedRequirementIndex.value = index
}

const openRequirementDetail = (index: number) => {
  selectRequirement(index)
  const requirement = requirements.value[index] ?? null
  detailRequirement.value = requirement
  detailTestcases.value = buildTestcases(detailRequirement.value)
  if (requirement) {
    const requirementId = requirement.ID || requirement.code || requirement.title
    detailRequirementGenerating.value = requirementGeneratingMap.value.get(requirementId) ?? false
  } else {
    detailRequirementGenerating.value = false
  }
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
  const requirementId = requirement.ID || requirement.code || requirement.title
  detailRequirementGenerating.value = requirementGeneratingMap.value.get(requirementId) ?? false
  detailVisible.value = true
}

const openRequirementFromCoverage = (requirement: RequirementWithCases) => {
  openRequirementFromBoard(requirement)
}

const openTestcaseDetail = (item: TestCaseDetailItem) => {
  testcaseDetail.value = item
  testcaseDetailVisible.value = true
}

const handleRequirementSave = async (payload: RequirementDetailItem) => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持修改需求')
    return
  }
  const requirementId = payload.ID || payload.code
  if (!requirementId) {
    window.alert('需求缺少可用的标识')
    return
  }
  try {
    await updateRequirement(projectId.value, requirementId, {
      title: payload.title,
      type: payload.type,
      content: payload.content
    })
    await loadRemoteProjectDetail()
    openConfirm({
      title: '生成测试用例',
      message: '是否基于最新需求重新生成测试用例？已生成的用例将被替换。',
      confirmText: '生成',
      onConfirm: async () => {
        try {
          await generateTestcasesAsync(projectId.value, [requirementId])
          await loadRemoteProjectDetail()
          refreshGenerationStatus()
        } catch {
          window.alert('测试用例生成任务提交失败，请稍后重试')
        }
      }
    })
    detailVisible.value = false
  } catch {
    window.alert('需求更新失败，请稍后重试')
  }
}

const handleRequirementDelete = async (payload: RequirementDetailItem) => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持删除需求')
    return
  }
  const requirementId = payload.ID || payload.code
  if (!requirementId) {
    window.alert('需求缺少可用的标识')
    return
  }
  openConfirm({
    title: '删除需求',
    message: '确定要删除该需求吗？删除后该需求的所有测试用例也将被删除，无法恢复。',
    confirmText: '删除',
    cancelText: '取消',
    onConfirm: async () => {
      try {
        await deleteRequirement(projectId.value, requirementId)
        await loadRemoteProjectDetail()
        detailVisible.value = false
      } catch {
        window.alert('需求删除失败，请稍后重试')
      }
    }
  })
}

// 处理新增需求菜单项点击
const handleCreateRequirement = (module: string) => {
  selectedModule.value = module
  createRequirementVisible.value = true
}

// 处理新增需求表单提交
const handleRequirementCreate = async (payload: CreateRequirementForm) => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持新增需求')
    return
  }
  try {
    const result = await createRequirement(projectId.value, payload)
    await loadRemoteProjectDetail()
    createRequirementVisible.value = false
    
    // 打开生成测试用例确认弹窗
    openConfirm({
      title: '生成测试用例',
      message: '是否为新需求生成测试用例？',
      confirmText: '生成',
      onConfirm: async () => {
        try {
          const requirementId = result.id || result.code
          await generateTestcasesAsync(projectId.value, [requirementId])
          await loadRemoteProjectDetail()
          refreshGenerationStatus()
        } catch {
          window.alert('测试用例生成任务提交失败，请稍后重试')
        }
      }
    })
  } catch {
    window.alert('需求创建失败，请稍后重试')
  }
}

const handleRequirementGenerateTestcases = async () => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持生成测试用例')
    return
  }
  const requirement = detailRequirement.value
  const requirementId = requirement?.ID || requirement?.code
  if (!requirementId) {
    window.alert('需求缺少可用的标识')
    return
  }
  openConfirm({
    title: '生成测试用例',
    message: '将为该需求重新生成测试用例，已生成的用例将被替换。',
    confirmText: '生成',
    onConfirm: async () => {
      try {
        await generateTestcasesAsync(projectId.value, [requirementId])
        await loadRemoteProjectDetail()
        refreshGenerationStatus()
      } catch {
        window.alert('测试用例生成任务提交失败，请稍后重试')
      }
    }
  })
}

const handleProjectGenerateTestcases = async () => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持生成测试用例')
    return
  }
  if (requirements.value.length === 0) {
    window.alert('暂无需求，无法生成测试用例')
    return
  }
  openConfirm({
    title: '生成测试用例',
    message: '将根据当前需求生成测试用例，已生成的用例将被替换。',
    confirmText: '生成',
    onConfirm: async () => {
      try {
        await generateTestcasesAsync(projectId.value)
        await loadRemoteProjectDetail()
        refreshGenerationStatus()
      } catch {
        window.alert('测试用例生成任务提交失败，请稍后重试')
      }
    }
  })
}
const handleTestcaseSave = async (payload: TestCaseDetailItem) => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持修改测试用例')
    return
  }
  if (!payload.id) {
    window.alert('测试用例缺少可用的标识')
    return
  }
  try {
    await updateTestcase(projectId.value, payload.id, {
      title: payload.title,
      code: payload.code,
      type: payload.type,
      test_steps: payload.test_steps ?? [],
      test_target_desc: payload.test_target_desc,
      verify_method: payload.verify_method
    })
    await loadRemoteProjectDetail()
    testcaseDetailVisible.value = false
  } catch {
    window.alert('测试用例更新失败，请稍后重试')
  }
}

const handleTestcaseDelete = async (payload: TestCaseDetailItem) => {
  if (!isRemoteProject.value) {
    window.alert('本地项目暂不支持删除测试用例')
    return
  }
  if (!payload.id) {
    window.alert('测试用例缺少可用的标识')
    return
  }
  openConfirm({
    title: '删除测试用例',
    message: '确定要删除该测试用例吗？删除后无法恢复。',
    confirmText: '删除',
    cancelText: '取消',
    onConfirm: async () => {
      try {
        await deleteTestcase(projectId.value, payload.id as string)
        await loadRemoteProjectDetail()
        testcaseDetailVisible.value = false
      } catch {
        window.alert('测试用例删除失败，请稍后重试')
      }
    }
  })
}

const goBack = () => {
  router.push({ name: 'projects' })
}


const baseQualityInfo = ref({
  fail_count: 0,
  iterations: 3,
  duration: 5.2
})

const qualityInfo = computed(() => {
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
  let successCount = 0
  requirements.value.forEach((item) => {
    const testcases = buildTestcases(item)
    if (testcases.length > 0) {
      successCount += 1
    }
    testcases.forEach((testcase) => {
      const key = testcase.type || '功能测试'
      typeStats.set(key, (typeStats.get(key) ?? 0) + 1)
    })
  })
  return {
    ...baseQualityInfo.value,
    success_count: successCount,
    req_type_stats: Object.fromEntries(typeStats)
  }
})

const generationStatus = ref<{ status: 'idle' | 'running' | 'done' | 'error'; job_id?: string } | null>(null)
const statusPollingTimer = ref<number | null>(null)

const nodeSizes = {
  root: { width: 200, height: 34 },
  feature: { width: 190, height: 32 },
  subfeature: { width: 220, height: 32 },
  testcase: { width: 200, height: 30 }
}

const normalizeRequirementCode = (requirement: Requirement | null) =>
  requirement?.code || requirement?.ID || ''

const buildTestcases = (requirement: RequirementWithCases | null): RequirementTestCaseItem[] => {
  if (!requirement) return []
  if (requirement.hasRemoteTestcases) {
    return requirement.testcases ?? []
  }
  if (Array.isArray(requirement.testcases) && requirement.testcases.length > 0) {
    return requirement.testcases
  }

  const requirement_code = normalizeRequirementCode(requirement)
  const requirement_id = requirement.ID || requirement.code || requirement.title
  const fragments = (requirement.content || '')
    .split(/[；。]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3)

  if (fragments.length === 0) {
    return []
  }

  return fragments.map((fragment, index) => {
    const baseCode = requirement_code || `REQ-${String(index + 1).padStart(3, '0')}`
    return {
      id: '',
      requirement_code,
      requirement_id,
      title: `${requirement.title}-测试点${index + 1}`,
      code: `TC-${baseCode}-${String(index + 1).padStart(3, '0')}`,
      type: '功能测试',
      test_steps: [
        {
          step_desc: fragment,
          expectation: '符合预期'
        }
      ],
      test_target_desc: fragment,
      verify_method: 'TESTING'
    }
  })
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

const mapRemoteModules = (remoteRequirements: Array<{
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
}>): RemoteModuleGroup[] => {
  const moduleMap = new Map<string, RemoteModuleGroup>()
  remoteRequirements.forEach((item) => {
    const moduleName = item.module || '未命名模块'
    if (!moduleMap.has(moduleName)) {
      moduleMap.set(moduleName, { module: moduleName, requirements: [] })
    }
    const testcases = (item.testcases || []).map((tc) => ({
      requirement_code: tc.requirement_code,
      requirement_id: tc.requirement_id,
      id: tc.id,
      title: tc.title,
      code: tc.code,
      type: tc.type,
      test_steps: tc.test_steps ?? [],
      test_target_desc: tc.test_target_desc,
      verify_method: tc.verify_method
    }))
    moduleMap.get(moduleName)!.requirements.push({
      ID: item.id,
      title: item.title,
      type: item.type,
      code: item.code,
      content: item.content,
      testcases,
      hasRemoteTestcases: true
    })
  })
  return Array.from(moduleMap.values())
}

const loadRemoteProjectDetail = async () => {
  const remoteId = projectId.value
  if (!remoteId) {
    remoteModules.value = null
    remoteProjectTitle.value = null
    return
  }
  try {
    const detail = await fetchProjectDetail(remoteId)
    remoteProjectTitle.value = detail.title
    remoteModules.value = mapRemoteModules(detail.requirements ?? [])
  } catch {
    remoteModules.value = null
    remoteProjectTitle.value = null
  }
}

const stopStatusPolling = () => {
  if (statusPollingTimer.value) {
    window.clearInterval(statusPollingTimer.value)
    statusPollingTimer.value = null
  }
}

const refreshGenerationStatus = async (allowStartPolling = true) => {
  const remoteId = projectId.value
  if (!remoteId || remoteId.startsWith('local-')) {
    generationStatus.value = { status: 'idle' }
    stopStatusPolling()
    return
  }
  try {
    const status = await fetchTestcaseGenerateStatus(remoteId)
    generationStatus.value = status
    if (status.status === 'running' && allowStartPolling) {
      if (!statusPollingTimer.value) {
        statusPollingTimer.value = window.setInterval(() => {
          loadRemoteProjectDetail()
          refreshGenerationStatus(false)
        }, 5000)
      }
      return
    }
    if (status.status !== 'running') {
      stopStatusPolling()
    }
  } catch {
    generationStatus.value = { status: 'error' }
    stopStatusPolling()
  }
}

onMounted(() => {
  loadRemoteProjectDetail()
  refreshGenerationStatus()
})

watch(projectId, () => {
  loadRemoteProjectDetail()
  refreshGenerationStatus()
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>
