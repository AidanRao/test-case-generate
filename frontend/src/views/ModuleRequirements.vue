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
        <div ref="moduleSelectContainer" class="min-w-0" style="width: min(22rem, 100%);">
          <p class="text-xs font-medium text-sky-600">{{ projectName }}</p>
          <div class="module-select mt-1" @click.stop="toggleModuleDropdown">
            <div class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 shadow-sm">
              <span class="min-w-0 flex-1 truncate text-lg font-semibold text-slate-800">{{ moduleName }}</span>
              <div class="flex flex-col items-center gap-0.5 text-slate-400">
                <el-icon class="text-xs"><ArrowUp /></el-icon>
                <el-icon class="text-xs"><ArrowDown /></el-icon>
              </div>
            </div>
          </div>
        </div>
        <div class="ml-auto flex flex-wrap items-center gap-2">
          <span class="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
            需求数 {{ moduleRequirements.length }}
          </span>
          <button
            class="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition"
            :class="isReadOnlyProject ? 'cursor-not-allowed bg-slate-100 text-slate-400' : 'bg-sky-600 text-white hover:bg-sky-700'"
            type="button"
            :disabled="isReadOnlyProject"
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
                    :class="getTestcaseCount(item) > 0 ? 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20' : 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20'"
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
                      :class="isReadOnlyProject ? 'cursor-not-allowed border-slate-100 text-slate-300' : 'border-rose-200 text-rose-600 hover:border-rose-300 hover:bg-rose-50'"
                      type="button"
                      :disabled="isReadOnlyProject"
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

    <RequirementDetailDialog
      v-model="detailVisible"
      :requirement="detailRequirement"
      :testcases="detailTestcases"
      :is-generating="false"
      :read-only="isReadOnlyProject"
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

    <ConfirmDialog
      v-model="confirmVisible"
      :title="confirmTitle"
      :message="confirmMessage"
      :confirm-text="confirmConfirmText"
      :cancel-text="confirmCancelText"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />

    <Teleport to="body">
      <div
        v-if="moduleDropdownVisible"
        class="fixed inset-0 z-50"
        @click="closeModuleDropdown"
      >
        <div class="absolute inset-0 bg-black/20"></div>
        <div
          class="absolute rounded-xl border border-slate-200 bg-white shadow-xl z-50"
          :style="{
            top: dropdownPosition.top + 'px',
            left: dropdownPosition.left + 'px',
            width: Math.min(dropdownPosition.width, 560) + 'px'
          }"
        >
          <div class="flex items-center border-b border-slate-100 px-4 py-3">
            <div class="relative flex-1">
              <el-icon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400">
                <Search />
              </el-icon>
              <input
                ref="moduleSearchInput"
                v-model="moduleSearchQuery"
                type="text"
                placeholder="Find Module..."
                class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-10 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                @keydown.esc="closeModuleDropdown"
              />
            </div>
            <button
              class="ml-2 rounded-lg px-2 py-1 text-xs font-medium text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
              type="button"
              @click.stop="closeModuleDropdown"
            >
              Esc
            </button>
          </div>
          <div class="max-h-64 overflow-y-auto">
            <button
              v-for="module in filteredModuleOptions"
              :key="module"
              class="flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-slate-50"
              :class="module === moduleName ? 'bg-slate-50' : ''"
              type="button"
              @click.stop="selectModule(module)"
            >
              <span class="flex-1 text-sm font-medium text-slate-700">{{ module }}</span>
              <el-icon v-if="module === moduleName" class="h-4 w-4 text-sky-600">
                <Check />
              </el-icon>
            </button>
            <div v-if="filteredModuleOptions.length === 0" class="px-4 py-8 text-center text-sm text-slate-400">
              未找到匹配的模块
            </div>
          </div>
          <div class="border-t border-slate-100 px-4 py-3">
            <button
              class="flex w-full items-center gap-2 rounded-lg border border-dashed border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-500 transition hover:border-slate-300 hover:bg-slate-50"
              type="button"
              @click.stop="openCreateModule"
            >
              <el-icon class="h-4 w-4"><Plus /></el-icon>
              新增模块
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowUp, ArrowDown, Plus, Search, Check } from '@element-plus/icons-vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import CreateRequirementDialog from '../components/CreateRequirementDialog.vue'
import PaginationBar from '../components/PaginationBar.vue'
import RequirementDetailDialog from '../components/RequirementDetailDialog.vue'
import type { RequirementDetailItem, RequirementTestCaseItem } from '../components/RequirementDetailDialog.vue'
import TestCaseDetailDialog from '../components/TestCaseDetailDialog.vue'
import type { TestCaseDetailItem } from '../components/TestCaseDetailDialog.vue'
import { useConfirmDialog } from '../composables/useConfirmDialog'
import {
  createRequirement,
  deleteRequirement,
  deleteTestcase,
  fetchProjectDetail,
  generateTestcasesAsync,
  updateRequirement,
  updateTestcase
} from '../api/projects'
import type { CreateRequirementPayload } from '../api/projects'
import { loadProjects, saveProjects, type ModuleGroup, type ProjectRecord, type Requirement } from '../data/projectStore'

type RemoteRequirement = Requirement & {
  id?: string
  project_id?: string
  testcases?: RequirementTestCaseItem[]
  hasRemoteTestcases?: boolean
}

type PageRequirement = Requirement & {
  id?: string
  project_id?: string
  testcases?: RequirementTestCaseItem[]
  hasRemoteTestcases?: boolean
}

type RemoteModuleGroup = {
  module: string
  requirements: RemoteRequirement[]
}

const router = useRouter()
const route = useRoute()

const projectId = computed(() => String(route.params.projectId ?? ''))
const moduleName = computed(() => String(route.params.moduleName ?? ''))

const localProjects = ref<ProjectRecord[]>(loadProjects())
const remoteModules = ref<RemoteModuleGroup[] | null>(null)
const remoteProjectTitle = ref<string | null>(null)
const remoteProjectSource = ref<'local' | 'uniportal' | null>(null)
const isLoading = ref(false)
const loadError = ref('')
const createRequirementVisible = ref(false)
const detailVisible = ref(false)
const detailRequirement = ref<PageRequirement | null>(null)
const detailTestcases = ref<RequirementTestCaseItem[]>([])
const testcaseDetail = ref<TestCaseDetailItem | null>(null)
const testcaseDetailVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(5)
const moduleDropdownVisible = ref(false)
const moduleSearchQuery = ref('')
const moduleSearchInput = ref<HTMLInputElement | null>(null)
const moduleSelectContainer = ref<HTMLElement | null>(null)
const dropdownPosition = ref({ top: 0, left: 0, width: 0 })

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

const currentProject = computed<ProjectRecord | null>(() =>
  localProjects.value.find((item) => item.id === projectId.value) ?? null
)

const moduleGroups = computed<Array<ModuleGroup | RemoteModuleGroup>>(() =>
  remoteModules.value ?? currentProject.value?.modules ?? []
)

const moduleOptions = computed(() => {
  const options = moduleGroups.value.map((item) => item.module)
  return moduleName.value && !options.includes(moduleName.value)
    ? [moduleName.value, ...options]
    : options
})

const filteredModuleOptions = computed(() => {
  if (!moduleSearchQuery.value) {
    return moduleOptions.value
  }
  const query = moduleSearchQuery.value.toLowerCase()
  return moduleOptions.value.filter((module) => module.toLowerCase().includes(query))
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

const projectName = computed(() => remoteProjectTitle.value ?? currentProject.value?.name ?? '项目')
const isReadOnlyProject = computed(() =>
  remoteProjectSource.value === 'uniportal' || currentProject.value?.source === 'uniportal'
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

const formatTestcaseCount = (item: PageRequirement) => {
  const count = getTestcaseCount(item)
  return count > 0 ? `${count} 条` : '未生成'
}

const normalizeRequirementCode = (requirement: PageRequirement | null) =>
  requirement?.code || requirement?.ID || ''

const getRequirementIdentity = (item: PageRequirement) => item.id || item.ID || item.code || item.title

const isSameRequirement = (source: PageRequirement, target: PageRequirement) => {
  const sourceIdentity = getRequirementIdentity(source)
  const targetIdentity = getRequirementIdentity(target)
  if (sourceIdentity && targetIdentity) {
    return sourceIdentity === targetIdentity
  }
  return source.title === target.title && source.content === target.content
}

const mapRemoteModules = (requirements: RemoteRequirement[]): RemoteModuleGroup[] => {
  const moduleMap = new Map<string, RemoteModuleGroup>()
  requirements.forEach((item) => {
    const name = item.module || '未命名模块'
    if (!moduleMap.has(name)) {
      moduleMap.set(name, { module: name, requirements: [] })
    }
    moduleMap.get(name)!.requirements.push({
      ...item,
      ID: item.id ?? item.ID,
      hasRemoteTestcases: true
    })
  })
  return Array.from(moduleMap.values())
}

const buildTestcases = (requirement: PageRequirement | null): RequirementTestCaseItem[] => {
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

const loadProjectDetail = async () => {
  localProjects.value = loadProjects()
  remoteModules.value = null
  remoteProjectTitle.value = null
  remoteProjectSource.value = null
  loadError.value = ''

  if (!projectId.value || projectId.value.startsWith('local-')) {
    return
  }

  isLoading.value = true
  try {
    const detail = await fetchProjectDetail(projectId.value)
    remoteProjectTitle.value = detail.title
    remoteProjectSource.value = detail.source
    remoteModules.value = mapRemoteModules(detail.requirements ?? [])
  } catch {
    if (!currentProject.value) {
      loadError.value = '项目详情加载失败，请稍后重试'
    }
  } finally {
    isLoading.value = false
  }
}

const openCreateDialog = () => {
  if (isReadOnlyProject.value) {
    window.alert('UniPortal 来源需求为只读，请在 UniPortal 中管理')
    return
  }
  createRequirementVisible.value = true
}

const toggleModuleDropdown = () => {
  moduleDropdownVisible.value = !moduleDropdownVisible.value
  if (moduleDropdownVisible.value) {
    if (moduleSelectContainer.value) {
      const rect = moduleSelectContainer.value.getBoundingClientRect()
      dropdownPosition.value = {
        top: rect.bottom + 8,
        left: rect.left,
        width: rect.width
      }
    }
    setTimeout(() => {
      moduleSearchInput.value?.focus()
    }, 100)
  }
}

const closeModuleDropdown = () => {
  moduleDropdownVisible.value = false
  moduleSearchQuery.value = ''
}

const selectModule = (nextModuleName: string) => {
  if (!nextModuleName || nextModuleName === moduleName.value) {
    closeModuleDropdown()
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
  closeModuleDropdown()
}

const openCreateModule = () => {
  closeModuleDropdown()
  window.alert('新增模块功能暂未实现')
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

const createLocalRequirement = (payload: CreateRequirementPayload) => {
  const projects = loadProjects()
  const targetProject = projects.find((item) => item.id === projectId.value)
  if (!targetProject) {
    window.alert('未找到项目，无法新增需求')
    return false
  }

  const nextRequirement = {
    ID: `local-req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    code: payload.code,
    title: payload.title,
    type: payload.type,
    content: payload.content
  }
  const moduleIndex = targetProject.modules.findIndex((item) => item.module === payload.module)
  const nextModules = targetProject.modules.map((item) => ({
    ...item,
    requirements: [...item.requirements]
  }))
  const targetModule = moduleIndex >= 0 ? nextModules[moduleIndex] : undefined
  if (targetModule) {
    targetModule.requirements.push(nextRequirement)
  } else {
    nextModules.push({ module: payload.module, requirements: [nextRequirement] })
  }

  const updatedProjects = projects.map((item) =>
    item.id === targetProject.id
      ? {
          ...item,
          modules: nextModules,
          moduleCount: nextModules.length,
          requirementCount: nextModules.reduce((sum, group) => sum + group.requirements.length, 0)
        }
      : item
  )
  saveProjects(updatedProjects)
  localProjects.value = updatedProjects
  return true
}

const deleteLocalRequirement = (target: PageRequirement) => {
  const projects = loadProjects()
  const targetProject = projects.find((item) => item.id === projectId.value)
  if (!targetProject) {
    window.alert('未找到项目，无法删除需求')
    return false
  }

  let deleted = false
  const nextModules = targetProject.modules.map((group) => {
    if (group.module !== moduleName.value) {
      return { ...group, requirements: [...group.requirements] }
    }
    const requirements = group.requirements.filter((item) => {
      const shouldDelete = isSameRequirement({ ...item, module: group.module }, target)
      if (shouldDelete) {
        deleted = true
      }
      return !shouldDelete
    })
    return { ...group, requirements }
  })

  if (!deleted) {
    window.alert('未找到要删除的需求')
    return false
  }

  const updatedProjects = projects.map((item) =>
    item.id === targetProject.id
      ? {
          ...item,
          modules: nextModules,
          moduleCount: nextModules.length,
          requirementCount: nextModules.reduce((sum, group) => sum + group.requirements.length, 0)
        }
      : item
  )
  saveProjects(updatedProjects)
  localProjects.value = updatedProjects
  return true
}

const updateLocalRequirement = (target: PageRequirement, payload: RequirementDetailItem) => {
  const projects = loadProjects()
  const targetProject = projects.find((item) => item.id === projectId.value)
  if (!targetProject) {
    window.alert('未找到项目，无法修改需求')
    return false
  }

  let updated = false
  const nextModules = targetProject.modules.map((group) => {
    if (group.module !== moduleName.value) {
      return { ...group, requirements: [...group.requirements] }
    }
    const requirements = group.requirements.map((item) => {
      if (!isSameRequirement({ ...item, module: group.module }, target)) {
        return item
      }
      updated = true
      return {
        ...item,
        title: payload.title,
        type: payload.type,
        content: payload.content,
        code: payload.code ?? item.code,
        ID: payload.ID ?? item.ID
      }
    })
    return { ...group, requirements }
  })

  if (!updated) {
    window.alert('未找到要修改的需求')
    return false
  }

  const updatedProjects = projects.map((item) =>
    item.id === targetProject.id
      ? {
          ...item,
          modules: nextModules,
          moduleCount: nextModules.length,
          requirementCount: nextModules.reduce((sum, group) => sum + group.requirements.length, 0)
        }
      : item
  )
  saveProjects(updatedProjects)
  localProjects.value = updatedProjects
  const nextDetail = moduleRequirements.value.find((item) => isSameRequirement(item, { ...payload, module: moduleName.value }))
  if (nextDetail) {
    detailRequirement.value = nextDetail
    detailTestcases.value = buildTestcases(nextDetail)
  }
  return true
}

const confirmDeleteRequirement = (item: PageRequirement) => {
  if (isReadOnlyProject.value) {
    return
  }
  openConfirm({
    title: '删除需求',
    message: '确定要删除该需求吗？删除后无法恢复。',
    confirmText: '删除',
    cancelText: '取消',
    onConfirm: async () => {
      if (projectId.value.startsWith('local-')) {
        if (deleteLocalRequirement(item) && detailRequirement.value && isSameRequirement(detailRequirement.value, item)) {
          detailVisible.value = false
          detailRequirement.value = null
          detailTestcases.value = []
        }
        return
      }

      const requirementId = item.id || item.ID || item.code
      if (!requirementId) {
        window.alert('需求缺少可用的标识')
        return
      }
      try {
        await deleteRequirement(projectId.value, requirementId)
        await loadProjectDetail()
        if (detailRequirement.value && isSameRequirement(detailRequirement.value, item)) {
          detailVisible.value = false
          detailRequirement.value = null
          detailTestcases.value = []
        }
      } catch {
        window.alert('需求删除失败，请稍后重试')
      }
    }
  })
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
    updateLocalRequirement(currentRequirement, payload)
    return
  }

  const requirementId = currentRequirement.id || payload.ID || payload.code
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
    await loadProjectDetail()
    detailRequirement.value = moduleRequirements.value.find((item) => getRequirementIdentity(item) === requirementId) ?? null
    if (detailRequirement.value) {
      detailTestcases.value = buildTestcases(detailRequirement.value)
    }
    openConfirm({
      title: '生成测试用例',
      message: '是否基于最新需求重新生成测试用例？已生成的用例将被替换。',
      confirmText: '生成',
      onConfirm: async () => {
        try {
          await generateTestcasesAsync(projectId.value, [requirementId])
          await loadProjectDetail()
        } catch {
          window.alert('测试用例生成任务提交失败，请稍后重试')
        }
      }
    })
  } catch {
    window.alert('需求更新失败，请稍后重试')
  }
}

const handleRequirementDelete = async (payload: RequirementDetailItem) => {
  const target = detailRequirement.value ?? { ...payload, module: moduleName.value }
  confirmDeleteRequirement(target)
}

const handleRequirementGenerateTestcases = async () => {
  if (projectId.value.startsWith('local-')) {
    window.alert('本地项目暂不支持生成测试用例')
    return
  }
  const requirement = detailRequirement.value
  const requirementId = requirement?.id || requirement?.ID || requirement?.code
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
        await loadProjectDetail()
      } catch {
        window.alert('测试用例生成任务提交失败，请稍后重试')
      }
    }
  })
}

const handleTestcaseSave = async (payload: TestCaseDetailItem) => {
  if (projectId.value.startsWith('local-')) {
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
    await loadProjectDetail()
    testcaseDetailVisible.value = false
  } catch {
    window.alert('测试用例更新失败，请稍后重试')
  }
}

const handleTestcaseDelete = async (payload: TestCaseDetailItem) => {
  if (projectId.value.startsWith('local-')) {
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
        await loadProjectDetail()
        testcaseDetailVisible.value = false
      } catch {
        window.alert('测试用例删除失败，请稍后重试')
      }
    }
  })
}

const handleRequirementCreate = async (payload: CreateRequirementPayload) => {
  if (isReadOnlyProject.value) {
    return
  }

  if (projectId.value.startsWith('local-')) {
    if (createLocalRequirement(payload)) {
      createRequirementVisible.value = false
      currentPage.value = Math.max(1, Math.ceil(moduleRequirements.value.length / pageSize.value))
    }
    return
  }

  try {
    const result = await createRequirement(projectId.value, payload)
    await loadProjectDetail()
    createRequirementVisible.value = false
    currentPage.value = Math.max(1, Math.ceil(moduleRequirements.value.length / pageSize.value))
    openConfirm({
      title: '生成测试用例',
      message: '是否为新需求生成测试用例？',
      confirmText: '生成',
      onConfirm: async () => {
        try {
          const requirementId = result.id || result.code
          if (requirementId) {
            await generateTestcasesAsync(projectId.value, [requirementId])
          }
          await loadProjectDetail()
        } catch {
          window.alert('测试用例生成任务提交失败，请稍后重试')
        }
      }
    })
  } catch {
    window.alert('需求创建失败，请稍后重试')
  }
}

const goBack = () => {
  router.push({
    name: 'test-cases',
    params: { projectId: projectId.value },
    query: route.query
  })
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && moduleDropdownVisible.value) {
    closeModuleDropdown()
  }
}

watch([pageSize, moduleName], () => {
  currentPage.value = 1
})

watch(moduleRequirements, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
})

watch(projectId, () => {
  loadProjectDetail()
})

onMounted(() => {
  loadProjectDetail()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.module-select {
  width: min(22rem, 100%);
  cursor: pointer;
}
</style>
