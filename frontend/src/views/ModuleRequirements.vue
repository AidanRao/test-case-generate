<template>
  <div class="min-h-screen bg-slate-50 p-6">
    <div class="mx-auto flex max-w-6xl flex-col gap-5">
      <header class="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          type="button"
          @click="goBack"
        >
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <ModuleSelectDropdown
          :model-value="moduleName"
          :project-name="projectName"
          :modules="moduleOptions"
          :can-create="!isReadOnlyProject && !isGenerationActive"
          @select="selectModule"
          @create="openCreateModule"
        />
        <div class="ml-auto flex flex-wrap items-center gap-2">
          <span class="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
            需求数 {{ moduleRequirements.length }}
          </span>
          <button
            class="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition"
            :class="isReadOnlyProject || isGenerationActive ? 'cursor-not-allowed bg-slate-100 text-slate-400' : 'bg-sky-600 text-white hover:bg-sky-700'"
            type="button"
            :disabled="isReadOnlyProject || isGenerationActive"
            @click="openCreateDialog"
          >
            <el-icon><Plus /></el-icon>
            新增需求
          </button>
        </div>
      </header>

      <main class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 px-6 py-4">
          <div class="min-w-0">
            <p class="text-sm font-semibold text-slate-800">模块需求</p>
          </div>
          <div class="ml-auto flex items-center gap-2 text-xs text-slate-500">
            <span>每页</span>
            <select
              v-model.number="pageSize"
              class="h-9 rounded-full border border-slate-200 px-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            >
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
            </select>
            <span>条</span>
          </div>
        </div>

        <div v-if="isLoading" class="px-6 py-12 text-center text-sm text-slate-400">
          正在加载需求...
        </div>
        <div v-else-if="loadError" class="px-6 py-12 text-center text-sm text-rose-500">
          {{ loadError }}
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[1120px] table-fixed divide-y divide-slate-200">
            <colgroup>
              <col class="w-[22%]" />
              <col class="w-[16%]" />
              <col class="w-[16%]" />
              <col class="w-[24%]" />
              <col class="w-[12%]" />
              <col class="w-[12%]" />
            </colgroup>
            <thead class="bg-slate-50">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">需求标题</th>
                <th class="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">需求编号</th>
                <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">需求类型</th>
                <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">需求内容</th>
                <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">测试用例数</th>
                <th class="px-4 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="(item, index) in paginatedRequirements"
                :key="getRequirementKey(item, index)"
                class="hover:bg-slate-50"
              >
                <td class="px-6 py-5">
                  <p class="truncate text-sm font-semibold text-slate-800" :title="item.title">{{ item.title }}</p>
                </td>
                <td class="px-6 py-5">
                  <p class="truncate text-sm text-slate-600" :title="getRequirementCode(item, index)">
                    {{ getRequirementCode(item, index) }}
                  </p>
                </td>
                <td class="px-4 py-5">
                  <p class="truncate text-sm text-slate-600" :title="item.type || '未分类'">
                    {{ item.type || '未分类' }}
                  </p>
                </td>
                <td class="px-4 py-5">
                  <p class="line-clamp-2 text-sm leading-6 text-slate-500" :title="item.content">
                    {{ item.content }}
                  </p>
                </td>
                <td class="px-4 py-5">
                  <span
                    class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="isRequirementGenerating(item) ? 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20' : isRequirementWaiting(item) ? 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/10' : getTestcaseCount(item) > 0 ? 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20' : 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/10'"
                  >
                    {{ formatTestcaseCount(item) }}
                  </span>
                </td>
                <td class="px-4 py-5 text-right">
                  <div class="inline-flex items-center gap-2 whitespace-nowrap">
                    <button
                      class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-700"
                      type="button"
                      @click="openRequirementDetail(item)"
                    >
                      查看
                    </button>
                    <button
                      class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                      :class="isReadOnlyProject || isGenerationActive ? 'cursor-not-allowed border-slate-100 text-slate-300' : 'border-rose-200 text-rose-600 hover:border-rose-300 hover:bg-rose-50'"
                      type="button"
                      :disabled="isReadOnlyProject || isGenerationActive"
                      @click="confirmDeleteRequirement(item)"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="moduleRequirements.length === 0">
                <td colspan="6" class="px-6 py-12 text-center text-sm text-slate-400">
                  当前模块暂无需求
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <PaginationBar
          :total-items="moduleRequirements.length"
          :current-page="currentPage"
          :page-size="pageSize"
          @update:currentPage="currentPage = $event"
        />
      </main>
    </div>

    <CreateRequirementDialog
      v-model="createRequirementVisible"
      :default-module="moduleName"
      @create="handleRequirementCreate"
    />

    <CreateModuleDialog
      v-model="createModuleVisible"
      :existing-modules="moduleOptions"
      @create="handleModuleCreate"
    />

    <RequirementDetailDialog
      v-model="detailVisible"
      :requirement="detailRequirement"
      :testcases="detailTestcases"
      :is-generating="detailRequirementGenerating"
      :is-waiting="detailRequirementWaiting"
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

  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import CreateModuleDialog from '../components/CreateModuleDialog.vue'
import CreateRequirementDialog from '../components/CreateRequirementDialog.vue'
import ModuleSelectDropdown from '../components/ModuleSelectDropdown.vue'
import PaginationBar from '../components/PaginationBar.vue'
import RequirementDetailDialog from '../components/RequirementDetailDialog.vue'
import type { RequirementDetailItem } from '../components/RequirementDetailDialog.vue'
import TestCaseDetailDialog from '../components/TestCaseDetailDialog.vue'
import type { RequirementTestCaseItem, TestCaseDetailItem } from '../data/testcase'
import { useAppFeedback } from '../composables/useAppFeedback'
import { useProjectTestcaseWorkspace } from '../composables/useProjectTestcaseWorkspace'
import {
  buildTestcases,
  getRequirementIdentity,
  isSameRequirement,
  type RequirementWithTestcases
} from '../composables/useRequirementTestcases'
import type { CreateRequirementPayload } from '../api/projects'
import type { Requirement } from '../data/projectStore'

type PageRequirement = RequirementWithTestcases & { module: string }

const router = useRouter()
const route = useRoute()
const { notify, confirm } = useAppFeedback()

const projectId = computed(() => String(route.params.projectId ?? ''))
const moduleName = computed(() => String(route.params.moduleName ?? ''))

const {
  moduleGroups,
  projectName,
  isReadOnlyProject,
  isLoading,
  loadError,
  processingRequirementIds,
  waitingRequirementIds,
  isGenerationActive,
  submitGeneration,
  saveRequirement,
  removeRequirement,
  addRequirement,
  addModule,
  saveTestcase,
  removeTestcase,
  createLocalRequirement,
  createLocalModule,
  deleteLocalRequirement,
  updateLocalRequirement
} = useProjectTestcaseWorkspace({ projectId })

const createRequirementVisible = ref(false)
const createModuleVisible = ref(false)
const detailVisible = ref(false)
const detailRequirement = ref<PageRequirement | null>(null)
const detailTestcases = ref<RequirementTestCaseItem[]>([])
const testcaseDetail = ref<TestCaseDetailItem | null>(null)
const testcaseDetailVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(5)
const detailRequirementGenerating = computed(() => {
  const requirementId = getRequirementIdentity(detailRequirement.value)
  return Boolean(requirementId && processingRequirementIds.value.has(requirementId))
})
const detailRequirementWaiting = computed(() => {
  const requirementId = getRequirementIdentity(detailRequirement.value)
  return Boolean(requirementId && waitingRequirementIds.value.has(requirementId))
})

const moduleOptions = computed(() => {
  const options = moduleGroups.value.map((item) => item.module)
  return moduleName.value && !options.includes(moduleName.value)
    ? [moduleName.value, ...options]
    : options
})

const selectedModuleGroup = computed(() =>
  moduleGroups.value.find((item) => item.module === moduleName.value) ?? null
)

const moduleRequirements = computed<PageRequirement[]>(() =>
  (selectedModuleGroup.value?.requirements ?? []).map((item) => ({
    ...item,
    module: moduleName.value
  })) as PageRequirement[]
)

const totalPages = computed(() => Math.max(1, Math.ceil(moduleRequirements.value.length / pageSize.value)))
const pageStartIndex = computed(() => (currentPage.value - 1) * pageSize.value)
const paginatedRequirements = computed(() =>
  moduleRequirements.value.slice(pageStartIndex.value, pageStartIndex.value + pageSize.value)
)

const getRequirementCode = (item: Requirement, index: number) =>
  item.code || item.ID || `REQ-${String(pageStartIndex.value + index + 1).padStart(3, '0')}`

const getRequirementKey = (item: Requirement, index: number) =>
  `${getRequirementCode(item, index)}-${pageStartIndex.value + index}`

const getTestcaseCount = (item: PageRequirement) => buildTestcases(item).length

const isRequirementGenerating = (item: PageRequirement) =>
  processingRequirementIds.value.has(getRequirementIdentity(item))

const isRequirementWaiting = (item: PageRequirement) =>
  waitingRequirementIds.value.has(getRequirementIdentity(item))

const formatTestcaseCount = (item: PageRequirement) => {
  if (isRequirementGenerating(item)) return '生成中'
  if (isRequirementWaiting(item)) return '等待中'
  const count = getTestcaseCount(item)
  return count > 0 ? `${count} 条` : '未生成'
}

const openCreateDialog = () => {
  if (isGenerationActive.value) {
    notify({ message: '测试用例生成期间不能新增需求' })
    return
  }
  if (isReadOnlyProject.value) {
    notify({ message: 'UniPortal 来源需求为只读，请在 UniPortal 中管理' })
    return
  }
  createRequirementVisible.value = true
}

const selectModule = (nextModuleName: string) => {
  if (!nextModuleName || nextModuleName === moduleName.value) {
    return
  }
  router.push({
    name: 'module-requirements',
    params: {
      projectId: projectId.value,
      moduleName: nextModuleName
    },
    query: route.query
  })
}

const openCreateModule = () => {
  if (isReadOnlyProject.value || isGenerationActive.value) {
    return
  }
  createModuleVisible.value = true
}

const openRequirementDetail = (item: PageRequirement) => {
  detailRequirement.value = item
  detailTestcases.value = buildTestcases(item)
  detailVisible.value = true
}

const openTestcaseDetail = (item: TestCaseDetailItem) => {
  testcaseDetail.value = item
  testcaseDetailVisible.value = true
}

const refreshOpenRequirementTestcases = (requirementIdentity: string, testcaseId?: string) => {
  const refreshedRequirement = moduleRequirements.value.find(
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

const confirmDeleteRequirement = async (item: PageRequirement) => {
  if (isReadOnlyProject.value) {
    return
  }
  const confirmed = await confirm({
    title: '删除需求',
    message: '确定要删除该需求吗？删除后无法恢复。',
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger'
  })
  if (!confirmed) return

  if (projectId.value.startsWith('local-')) {
    if (!deleteLocalRequirement(moduleName.value, item)) {
      notify({ message: '未找到要删除的需求', tone: 'error' })
      return
    }
    if (detailRequirement.value && isSameRequirement(detailRequirement.value, item)) {
      detailVisible.value = false
      detailRequirement.value = null
      detailTestcases.value = []
    }
    return
  }

  const requirementId = item.id || item.ID || item.code
  if (!requirementId) {
    notify({ message: '需求缺少可用的标识', tone: 'error' })
    return
  }
  try {
    await removeRequirement(requirementId)
    if (detailRequirement.value && isSameRequirement(detailRequirement.value, item)) {
      detailVisible.value = false
      detailRequirement.value = null
      detailTestcases.value = []
    }
  } catch {
    notify({ message: '需求删除失败，请稍后重试', tone: 'error' })
  }
}

const handleRequirementSave = async (payload: RequirementDetailItem) => {
  if (isReadOnlyProject.value) {
    return
  }

  const currentRequirement = detailRequirement.value
  if (!currentRequirement) {
    return
  }

  if (projectId.value.startsWith('local-')) {
    if (!updateLocalRequirement(moduleName.value, currentRequirement, payload)) {
      notify({ message: '未找到要修改的需求', tone: 'error' })
      return
    }
    const nextDetail = moduleRequirements.value.find((item) =>
      isSameRequirement(item, { ...payload, module: moduleName.value })
    )
    if (nextDetail) {
      detailRequirement.value = nextDetail
      detailTestcases.value = buildTestcases(nextDetail)
    }
    return
  }

  const requirementId = currentRequirement.id || payload.ID || payload.code
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
    detailRequirement.value = moduleRequirements.value.find((item) => getRequirementIdentity(item) === requirementId) ?? null
    if (detailRequirement.value) {
      detailTestcases.value = buildTestcases(detailRequirement.value)
    }
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
  } catch {
    notify({ message: '需求更新失败，请稍后重试', tone: 'error' })
  }
}

const handleRequirementDelete = async (payload: RequirementDetailItem) => {
  const target = detailRequirement.value ?? { ...payload, module: moduleName.value }
  confirmDeleteRequirement(target)
}

const handleRequirementGenerateTestcases = async () => {
  if (projectId.value.startsWith('local-')) {
    notify({ message: '本地项目暂不支持生成测试用例' })
    return
  }
  const requirement = detailRequirement.value
  const requirementId = requirement?.id || requirement?.ID || requirement?.code
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

const handleTestcaseSave = async (payload: TestCaseDetailItem) => {
  if (projectId.value.startsWith('local-')) {
    notify({ message: '本地项目暂不支持修改测试用例' })
    return
  }
  if (!payload.id) {
    notify({ message: '测试用例缺少可用的标识', tone: 'error' })
    return
  }
  const requirementIdentity = getRequirementIdentity(detailRequirement.value)
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
  if (projectId.value.startsWith('local-')) {
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

const handleRequirementCreate = async (payload: CreateRequirementPayload) => {
  if (isReadOnlyProject.value) {
    return
  }

  if (projectId.value.startsWith('local-')) {
    if (createLocalRequirement(payload)) {
      createRequirementVisible.value = false
      currentPage.value = Math.max(1, Math.ceil(moduleRequirements.value.length / pageSize.value))
    } else {
      notify({ message: '未找到项目，无法新增需求', tone: 'error' })
    }
    return
  }

  try {
    const result = await addRequirement(payload)
    createRequirementVisible.value = false
    currentPage.value = Math.max(1, Math.ceil(moduleRequirements.value.length / pageSize.value))
    const shouldGenerate = await confirm({
      title: '生成测试用例',
      message: '是否为新需求生成测试用例？',
      confirmText: '生成'
    })
    if (shouldGenerate) {
      try {
        const requirementId = result.id || result.code
        if (requirementId) {
          await submitGeneration([requirementId])
        }
      } catch {
        notify({ message: '测试用例生成任务提交失败，请稍后重试', tone: 'error' })
      }
    }
  } catch {
    notify({ message: '需求创建失败，请稍后重试', tone: 'error' })
  }
}

const handleModuleCreate = async (nextModuleName: string) => {
  if (isReadOnlyProject.value) {
    return
  }

  if (projectId.value.startsWith('local-')) {
    if (createLocalModule(nextModuleName)) {
      createModuleVisible.value = false
      selectModule(nextModuleName)
    } else {
      notify({ message: '项目不存在或模块名已存在', tone: 'error' })
    }
    return
  }

  try {
    const result = await addModule(nextModuleName)
    createModuleVisible.value = false
    selectModule(result.name || nextModuleName)
  } catch {
    notify({ message: '模块创建失败，请稍后重试', tone: 'error' })
  }
}

const goBack = () => {
  router.push({
    name: 'test-cases',
    params: { projectId: projectId.value },
    query: route.query
  })
}

watch([pageSize, moduleName], () => {
  currentPage.value = 1
})

watch(moduleRequirements, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
})

</script>
