<template>
  <div class="min-h-screen bg-gradient-to-b from-white to-slate-50">
    <div class="mx-auto max-w-6xl px-6 py-10">
      <div class="flex gap-6">
        <aside class="w-72 shrink-0 space-y-4">
          <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-sm font-medium text-sky-600">项目管理</p>
            <h1 class="mt-2 text-xl font-semibold text-slate-900">测试用例智能生成工具</h1>
            <p class="mt-2 text-sm text-slate-500">选择一个项目进入测试用例管理页面</p>
            <div class="mt-4 inline-flex rounded-full bg-sky-50 px-4 py-2 text-xs font-semibold text-sky-700">
              总项目数：{{ projects.length }}
            </div>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p class="text-xs font-semibold text-slate-500">快捷操作</p>
            <div class="mt-4 space-y-2">
              <button
                class="flex w-full items-center justify-start gap-2 rounded-xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-700"
                type="button"
                @click="openCreateDialog"
              >
                <el-icon class="text-base"><FolderOpened /></el-icon>
                新建项目
              </button>
              <button
                class="flex w-full items-center justify-start gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
                type="button"
                @click="openKnowledgeCreate"
              >
                <el-icon class="text-base"><Collection /></el-icon>
                新建知识库
              </button>
            </div>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between">
              <p class="text-xs font-semibold text-slate-500">最近访问</p>
              <span class="text-xs text-slate-400">{{ recentProjects.length }}</span>
            </div>
            <div class="mt-3 space-y-2">
              <div
                v-for="entry in recentProjects"
                :key="entry.project.id"
                class="flex items-center justify-between gap-2 rounded-xl border border-slate-100 px-3 py-2 text-sm text-slate-600"
              >
                <button class="min-w-0 flex-1 truncate text-left font-semibold text-slate-700" @click="goToTestCases(entry.project.id)">
                  {{ entry.project.name }}
                </button>
              </div>
              <p v-if="recentProjects.length === 0" class="text-xs text-slate-400">暂无访问记录</p>
            </div>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between">
              <p class="text-xs font-semibold text-slate-500">知识库概览</p>
              <span class="text-xs text-slate-400">{{ knowledgeItems.length }}</span>
            </div>
            <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-xl bg-slate-50 px-3 py-2 text-slate-500">
                草稿
                <span class="ml-2 font-semibold text-slate-700">{{ draftCount }}</span>
              </div>
              <div class="rounded-xl bg-slate-50 px-3 py-2 text-slate-500">
                已发布
                <span class="ml-2 font-semibold text-slate-700">{{ publishedCount }}</span>
              </div>
            </div>
            <div class="mt-3 space-y-2">
              <div
                v-for="item in latestKnowledge"
                :key="item.id"
                class="rounded-xl border border-slate-100 px-3 py-2 text-xs text-slate-600"
              >
                <p class="truncate font-semibold text-slate-700">{{ item.title }}</p>
                <p class="mt-1 text-slate-400">更新于 {{ formatDate(item.updatedAt) }}</p>
              </div>
              <p v-if="latestKnowledge.length === 0" class="text-xs text-slate-400">暂无知识条目</p>
            </div>
          </div>
        </aside>
        <div class="flex-1">
          <div class="mb-4 flex items-center justify-between">
            <div class="inline-flex rounded-full border border-slate-200 bg-white p-1 shadow-sm">
              <button
                class="rounded-full px-4 py-2 text-sm font-semibold transition"
                :class="activeSection === 'projects' ? 'bg-sky-600 text-white' : 'text-slate-600 hover:bg-slate-50'"
                type="button"
                @click="activeSection = 'projects'"
              >
                项目管理
              </button>
              <button
                class="rounded-full px-4 py-2 text-sm font-semibold transition"
                :class="activeSection === 'knowledge' ? 'bg-sky-600 text-white' : 'text-slate-600 hover:bg-slate-50'"
                type="button"
                @click="activeSection = 'knowledge'"
              >
                知识库管理
              </button>
            </div>
            <button
              class="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
              type="button"
              @click="goToSettings"
            >
              <el-icon class="text-base"><Setting /></el-icon>
              系统设置
            </button>
          </div>

          <div v-if="activeSection === 'projects'" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 bg-white px-6 py-4">
              <input
                v-model="searchText"
                class="h-10 w-64 rounded-full border border-slate-200 px-4 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
                placeholder="搜索项目名称或编号"
              />
              <div class="ml-auto flex items-center gap-2 text-xs text-slate-500">
                <span>每页</span>
                <select
                  v-model.number="pageSize"
                  class="h-9 rounded-full border border-slate-200 px-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
                >
                  <option :value="5">5</option>
                  <option :value="10">10</option>
                  <option :value="15">15</option>
                </select>
                <span>条</span>
              </div>
            </div>
            <table class="min-w-full divide-y divide-slate-200">
              <thead class="bg-slate-50">
                <tr>
                  <th class="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">项目名称</th>
                  <th class="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">一级功能数</th>
                  <th class="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">二级需求数</th>
                  <th class="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="(project, index) in paginatedRows" :key="project.id" class="hover:bg-slate-50">
                  <td class="px-6 py-5">
                    <div class="flex items-center gap-3">
                      <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 text-sky-600">
                        {{ pageStartIndex + index + 1 }}
                      </div>
                      <div>
                        <p class="text-sm font-semibold text-slate-900">{{ project.name }}</p>
                        <p class="mt-1 text-xs text-slate-500">项目编号：{{ project.code }}</p>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <div class="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                      {{ project.moduleCount }} 个功能
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <div class="inline-flex items-center rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
                      {{ project.requirementCount }} 条需求
                    </div>
                  </td>
                  <td class="px-6 py-5 text-right">
                    <div class="inline-flex items-center gap-2">
                      <button
                        class="inline-flex items-center gap-2 rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700"
                        @click="goToTestCases(project.id)"
                      >
                        进入项目
                        <span class="text-base">→</span>
                      </button>
                      <button
                        class="inline-flex items-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
                        @click="openEditDialog(project)"
                      >
                        编辑
                      </button>
                      <button
                        class="inline-flex items-center rounded-full border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700"
                        @click="removeProject(project.id)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredRows.length === 0">
                  <td colspan="4" class="px-6 py-10 text-center text-sm text-slate-400">
                    {{ emptyText }}
                  </td>
                </tr>
              </tbody>
            </table>
            <PaginationBar
              :total-items="filteredRows.length"
              :current-page="currentPage"
              :page-size="pageSize"
              @update:currentPage="currentPage = $event"
            />
          </div>

          <KnowledgeBasePanel
            v-else
            :items="knowledgeItems"
            :projects="projects"
            :initial-project-id="knowledgeProjectId"
            :create-signal="knowledgeCreateSignal"
            @update:items="handleKnowledgeUpdate"
          />
        </div>
      </div>
    </div>

    <ProjectDialog
      v-model="dialogVisible"
      :mode="dialogMode"
      :initial-name="dialogInitial.name"
      :initial-code="dialogInitial.code"
      :initial-modules="dialogInitial.modules"
      @submit="handleDialogSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Collection, FolderOpened, Setting } from '@element-plus/icons-vue'
import KnowledgeBasePanel from '../components/KnowledgeBasePanel.vue'
import PaginationBar from '../components/PaginationBar.vue'
import ProjectDialog from '../components/ProjectDialog.vue'
import { createProject, deleteProject, fetchProjectList, generateTestcasesAsync, updateProject } from '../api/projects'
import { loadKnowledgeBase, saveKnowledgeBase, type KnowledgeBaseItem } from '../data/knowledgeBaseStore'
import { buildRequirements, loadProjects, saveProjects, type ModuleGroup, type ProjectRecord } from '../data/projectStore'
import { loadRecentProjects, recordProjectVisit } from '../data/recentProjectStore'

const router = useRouter()
const route = useRoute()

const activeSection = ref<'projects' | 'knowledge'>(route.query.tab === 'knowledge' ? 'knowledge' : 'projects')

watch(
  () => route.query.tab,
  (tab) => {
    if (tab === 'knowledge') {
      activeSection.value = 'knowledge'
      return
    }
    if (tab === 'projects') {
      activeSection.value = 'projects'
    }
  }
)

watch(activeSection, (value) => {
  if (route.query.tab === value) {
    return
  }
  router.replace({ query: { ...route.query, tab: value } })
})

const projects = ref<ProjectRecord[]>(loadProjects())
const knowledgeItems = ref<KnowledgeBaseItem[]>(loadKnowledgeBase())
const recentEntries = ref(loadRecentProjects())
const knowledgeCreateSignal = ref(0)
const knowledgeProjectId = computed(() => {
  const raw = route.query.projectId
  if (typeof raw === 'string' && raw) {
    return raw
  }
  if (Array.isArray(raw) && typeof raw[0] === 'string') {
    return raw[0]
  }
  return null
})

const projectRows = computed(() =>
  projects.value.map((item) => ({
    ...item,
    moduleCount: item.moduleCount ?? item.modules.length,
    requirementCount: item.requirementCount ?? buildRequirements(item.modules).length
  }))
)

const recentProjects = computed(() =>
  recentEntries.value
    .map((entry) => ({
      project: projects.value.find((item) => item.id === entry.projectId),
      visitedAt: entry.visitedAt
    }))
    .filter((entry): entry is { project: ProjectRecord; visitedAt: string } => !!entry.project)
)

const latestKnowledge = computed(() =>
  [...knowledgeItems.value]
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, 3)
)

const draftCount = computed(() => knowledgeItems.value.filter((item) => item.status === 'draft').length)
const publishedCount = computed(() => knowledgeItems.value.filter((item) => item.status === 'published').length)

const searchText = ref('')
const pageSize = ref(10)
const currentPage = ref(1)

const filteredRows = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  if (!keyword) {
    return projectRows.value
  }
  return projectRows.value.filter(
    (item) => item.name.toLowerCase().includes(keyword) || item.code.toLowerCase().includes(keyword)
  )
})

const emptyText = computed(() => {
  if (projects.value.length === 0) {
    return '暂无项目，请先新建项目'
  }
  if (searchText.value.trim()) {
    return '未找到匹配的项目'
  }
  return '暂无项目，请先新建项目'
})

const pageStartIndex = computed(() => {
  if (filteredRows.value.length === 0) {
    return 0
  }
  return (currentPage.value - 1) * pageSize.value
})

const pageEndIndex = computed(() => {
  if (filteredRows.value.length === 0) {
    return 0
  }
  return Math.min(filteredRows.value.length, pageStartIndex.value + pageSize.value)
})

const paginatedRows = computed(() => filteredRows.value.slice(pageStartIndex.value, pageEndIndex.value))

watch([searchText, pageSize], () => {
  currentPage.value = 1
})

watch(
  () => filteredRows.value.length,
  () => {
    const nextTotalPages = Math.max(1, Math.ceil(filteredRows.value.length / pageSize.value))
    if (currentPage.value > nextTotalPages) {
      currentPage.value = nextTotalPages
    }
  }
)

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingProjectId = ref<string | null>(null)
const dialogInitial = reactive({
  name: '',
  code: '',
  modules: [] as ModuleGroup[]
})

const openCreateDialog = () => {
  dialogInitial.name = ''
  dialogInitial.code = ''
  dialogInitial.modules = []
  editingProjectId.value = null
  dialogMode.value = 'create'
  dialogVisible.value = true
}

const openKnowledgeCreate = () => {
  knowledgeCreateSignal.value = Date.now()
  activeSection.value = 'knowledge'
}

const openEditDialog = (project: ProjectRecord) => {
  editingProjectId.value = project.id
  dialogInitial.name = project.name
  dialogInitial.code = project.code
  dialogInitial.modules = project.modules
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

const handleDialogSubmit = async (payload: {
  name: string
  code: string
  modules: ModuleGroup[]
  generateNow?: boolean
}) => {
  const { generateNow, ...basePayload } = payload
  if (dialogMode.value === 'edit' && editingProjectId.value) {
    const projectId = editingProjectId.value
    if (!projectId.startsWith('local-')) {
      try {
        await updateProject(projectId, {
          code: basePayload.code,
          title: basePayload.name
        })
      } catch {
        window.alert('项目更新失败，请稍后重试')
        return
      }
    }
    const updated = projects.value.map((item) =>
      item.id === editingProjectId.value ? { ...item, ...basePayload } : item
    )
    projects.value = updated
    saveProjects(updated)
    return
  }
  let nextId: string | null = null
  try {
    const created = await createProject({
      code: basePayload.code,
      title: basePayload.name,
      requirements: basePayload.modules
    })
    nextId = created.id
  } catch {
    nextId = null
  }
  const finalId = nextId ?? `local-${projects.value.length + 1}`
  const updated = [
    ...projects.value,
    {
      id: finalId,
      name: basePayload.name,
      code: basePayload.code,
      modules: basePayload.modules,
      moduleCount: basePayload.modules.length,
      requirementCount: buildRequirements(basePayload.modules).length
    }
  ]
  projects.value = updated
  saveProjects(updated)
  if (generateNow && nextId) {
    try {
      await generateTestcasesAsync(nextId)
    } catch {
      window.alert('测试用例生成任务提交失败，请稍后在项目内重试')
    }
  }
  if (generateNow && !nextId) {
    window.alert('项目已保存到本地，无法提交测试用例生成任务')
  }
}

const handleKnowledgeUpdate = (items: KnowledgeBaseItem[]) => {
  knowledgeItems.value = items
  saveKnowledgeBase(items)
}

const removeProject = async (projectId: string) => {
  const confirmed = window.confirm('确定要删除该项目吗？删除后无法恢复。')
  if (!confirmed) {
    return
  }
  if (!projectId.startsWith('local-')) {
    try {
      await deleteProject(projectId)
    } catch {
      window.alert('删除失败，请稍后重试')
      return
    }
  }
  const updated = projects.value.filter((item) => item.id !== projectId)
  projects.value = updated
  saveProjects(updated)
}

const goToTestCases = (projectId: string) => {
  router.push({ name: 'test-cases', params: { projectId } })
  recentEntries.value = recordProjectVisit(projectId)
}

const goToSettings = () => {
  router.push({ name: 'settings' })
}

const formatDate = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString()
}

const mapApiProjects = (list: Array<{ id: string; code: string; title: string; module_count: number; requirement_count: number }>) => {
  const localProjects = loadProjects()
  return list.map((item) => {
    const matched = localProjects.find((project) => project.code === item.code)
    return {
      id: item.id,
      name: item.title,
      code: item.code,
      modules: matched?.modules ?? [],
      moduleCount: item.module_count,
      requirementCount: item.requirement_count
    }
  })
}

const loadRemoteProjects = async () => {
  try {
    const list = await fetchProjectList()
    projects.value = mapApiProjects(list)
  } catch {
    projects.value = loadProjects()
  }
}

onMounted(() => {
  loadRemoteProjects()
})
</script>
