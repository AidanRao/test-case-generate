<template>
  <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-wrap items-center gap-4">
      <div class="min-w-[220px] flex-1">
        <p class="text-sm font-semibold text-slate-900">知识库管理</p>
        <p class="mt-1 text-xs text-slate-500">沉淀项目经验、需求解释与用例要点</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <input
          v-model="searchText"
          class="h-10 w-56 rounded-full border border-slate-200 px-4 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
          placeholder="搜索条目名称或内容"
        />
        <select
          v-model="statusFilter"
          class="h-10 rounded-full border border-slate-200 px-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
        >
          <option value="all">全部状态</option>
          <option value="draft">草稿</option>
          <option value="published">已发布</option>
        </select>
        <select
          v-model="projectFilter"
          class="h-10 rounded-full border border-slate-200 px-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
        >
          <option value="all">全部项目</option>
          <option v-for="project in projects" :key="project.id" :value="String(project.id)">
            {{ project.name }}
          </option>
        </select>
        <button
          class="h-10 rounded-full bg-sky-600 px-4 text-sm font-semibold text-white transition hover:bg-sky-700"
          type="button"
          @click="openCreateDialog"
        >
          新建知识库
        </button>
      </div>
    </div>

    <div class="mt-5 flex min-h-[420px] gap-4">
      <div class="w-80 shrink-0 rounded-2xl border border-slate-100 bg-slate-50/60 p-3">
        <div v-if="filteredItems.length === 0" class="flex h-full items-center justify-center text-sm text-slate-400">
          暂无知识条目
        </div>
        <div v-else class="space-y-2">
          <button
            v-for="item in filteredItems"
            :key="item.id"
            class="w-full rounded-xl border border-transparent bg-white px-4 py-3 text-left transition hover:border-slate-200 hover:shadow-sm"
            :class="item.id === selectedId ? 'border-sky-200 bg-sky-50/50' : ''"
            @click="selectedId = item.id"
          >
            <div class="flex items-center justify-between gap-2">
              <p class="text-sm font-semibold text-slate-800">{{ item.title }}</p>
              <span
                class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                :class="item.status === 'published' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
              >
                {{ item.status === 'published' ? '已发布' : '草稿' }}
              </span>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-1 text-xs text-slate-500">
              <span v-if="getProjectName(item.projectId)" class="rounded-full bg-sky-50 px-2 py-0.5 font-medium text-sky-700">
                {{ getProjectName(item.projectId) }}
              </span>
              <span v-for="tag in item.tags.slice(0, 2)" :key="tag" class="rounded-full bg-slate-100 px-2 py-0.5">
                {{ tag }}
              </span>
              <span v-if="item.tags.length > 2" class="text-[11px] text-slate-400">+{{ item.tags.length - 2 }}</span>
            </div>
          </button>
        </div>
      </div>

      <div class="flex-1 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <div v-if="selectedItem" class="flex h-full flex-col">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 class="text-xl font-semibold text-slate-900">{{ selectedItem.title }}</h3>
              <p v-if="selectedItem.summary" class="mt-2 text-sm text-slate-500">{{ selectedItem.summary }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
                @click="openEditDialog(selectedItem)"
              >
                编辑
              </button>
              <button
                class="rounded-full border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700"
                @click="removeItem(selectedItem.id)"
              >
                删除
              </button>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span v-if="getProjectName(selectedItem.projectId)" class="rounded-full bg-sky-50 px-2 py-0.5 font-medium text-sky-700">
              {{ getProjectName(selectedItem.projectId) }}
            </span>
            <span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600">{{ selectedItem.status === 'published' ? '已发布' : '草稿' }}</span>
            <span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600">
              更新时间 {{ formatDate(selectedItem.updatedAt) }}
            </span>
            <span
              v-for="tag in selectedItem.tags"
              :key="tag"
              class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600"
            >
              {{ tag }}
            </span>
          </div>
          <div class="mt-5 flex-1 overflow-y-auto rounded-xl border border-slate-100 bg-slate-50/40 p-4 text-sm text-slate-700">
            <p v-if="selectedItem.content">{{ selectedItem.content }}</p>
            <p v-else class="text-slate-400">暂无内容</p>
          </div>
        </div>
        <div v-else class="flex h-full items-center justify-center text-sm text-slate-400">
          请选择知识条目查看详情
        </div>
      </div>
    </div>
  </div>

  <KnowledgeItemDialog
    v-model="dialogVisible"
    :mode="dialogMode"
    :projects="projects"
    :initial-item="editingItem"
    @submit="handleDialogSubmit"
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { KnowledgeBaseItem, KnowledgeStatus } from '../data/knowledgeBaseStore'
import type { ProjectRecord } from '../data/projectStore'
import { useAppFeedback } from '../composables/useAppFeedback'
import KnowledgeItemDialog from './KnowledgeItemDialog.vue'

const { confirm } = useAppFeedback()

const props = defineProps<{
  items: KnowledgeBaseItem[]
  projects: ProjectRecord[]
  initialProjectId?: string | null
  createSignal?: number
}>()

const emit = defineEmits<{
  (e: 'update:items', items: KnowledgeBaseItem[]): void
}>()

const searchText = ref('')
const statusFilter = ref<'all' | KnowledgeStatus>('all')
const projectFilter = ref('all')
const selectedId = ref<number | null>(props.items[0]?.id ?? null)

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingItem = ref<KnowledgeBaseItem | null>(null)

const filteredItems = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  return props.items.filter((item) => {
    const matchesKeyword =
      keyword.length === 0 ||
      item.title.toLowerCase().includes(keyword) ||
      item.summary.toLowerCase().includes(keyword) ||
      item.content.toLowerCase().includes(keyword)
    const matchesStatus = statusFilter.value === 'all' || item.status === statusFilter.value
    const matchesProject = projectFilter.value === 'all' || String(item.projectId) === projectFilter.value
    return matchesKeyword && matchesStatus && matchesProject
  })
})

watch(
  () => props.initialProjectId,
  (projectId) => {
    if (typeof projectId === 'string' && projectId) {
      projectFilter.value = String(projectId)
    }
  },
  { immediate: true }
)

watch(
  () => props.createSignal,
  (value) => {
    if (typeof value === 'number' && value > 0) {
      openCreateDialog()
    }
  }
)

watch(
  () => filteredItems.value,
  (items) => {
    if (!items.find((item) => item.id === selectedId.value)) {
      selectedId.value = items[0]?.id ?? null
    }
  },
  { immediate: true }
)

watch(
  () => props.items,
  (items) => {
    if (!items.find((item) => item.id === selectedId.value)) {
      selectedId.value = items[0]?.id ?? null
    }
  }
)

const selectedItem = computed(() => props.items.find((item) => item.id === selectedId.value) ?? null)

const getProjectName = (projectId: string | null) => {
  if (!projectId) {
    return ''
  }
  return props.projects.find((item) => item.id === projectId)?.name ?? ''
}

const formatDate = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  editingItem.value = null
  dialogVisible.value = true
}

const openEditDialog = (item: KnowledgeBaseItem) => {
  dialogMode.value = 'edit'
  editingItem.value = item
  dialogVisible.value = true
}

const handleDialogSubmit = (payload: {
  title: string
  tags: string[]
  projectId: string | null
  status: KnowledgeStatus
  summary: string
  content: string
}) => {
  const now = new Date().toISOString()
  if (dialogMode.value === 'edit' && editingItem.value) {
    const updated = props.items.map((item) =>
      item.id === editingItem.value?.id ? { ...item, ...payload, updatedAt: now } : item
    )
    emit('update:items', updated)
    return
  }
  const nextId = props.items.reduce((maxId, item) => Math.max(maxId, item.id), 0) + 1
  emit('update:items', [
    ...props.items,
    {
      id: nextId,
      updatedAt: now,
      ...payload
    }
  ])
}

const removeItem = async (id: number) => {
  const confirmed = await confirm({
    title: '删除知识条目',
    message: '确定要删除该知识条目吗？删除后无法恢复。',
    confirmText: '删除',
    tone: 'danger'
  })
  if (!confirmed) {
    return
  }
  emit(
    'update:items',
    props.items.filter((item) => item.id !== id)
  )
}
</script>
