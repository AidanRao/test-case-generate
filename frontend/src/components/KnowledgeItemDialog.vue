<template>
  <AppDialog
    :model-value="modelValue"
    :title="dialogTitle"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
  >
      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium text-slate-700">条目名称</label>
          <input
            v-model="title"
            class="mt-2 w-full rounded-xl border border-zinc-200 px-4 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            placeholder="请输入知识条目名称"
          />
          <p v-if="formErrors.title" class="mt-1 text-xs text-rose-600">{{ formErrors.title }}</p>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-slate-700">状态</label>
            <select
              v-model="status"
              class="mt-2 w-full rounded-xl border border-zinc-200 px-4 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            >
              <option value="draft">草稿</option>
              <option value="published">已发布</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">关联项目</label>
            <select
              v-model="projectId"
              class="mt-2 w-full rounded-xl border border-zinc-200 px-4 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            >
              <option value="">未关联</option>
              <option v-for="project in projects" :key="project.id" :value="String(project.id)">
                {{ project.name }}
              </option>
            </select>
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-slate-700">标签</label>
          <div class="mt-2 flex items-center gap-2">
            <input
              v-model="tagInput"
              class="h-10 flex-1 rounded-xl border border-zinc-200 px-4 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
              placeholder="输入标签后回车或点击加号"
              @keydown.enter.prevent="addTag()"
            />
            <button
              class="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-700"
              type="button"
              @click="addTag()"
            >
              <el-icon class="text-base"><Plus /></el-icon>
            </button>
          </div>
          <div v-if="tags.length > 0" class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="tag in tags"
              :key="tag"
              class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600"
            >
              {{ tag }}
              <button
                class="flex h-4 w-4 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-200 hover:text-slate-600"
                type="button"
                @click="removeTag(tag)"
              >
                ×
              </button>
            </span>
          </div>
          <p v-if="tagError" class="mt-2 text-xs text-rose-600">{{ tagError }}</p>
        </div>
        <div>
          <label class="text-sm font-medium text-slate-700">摘要</label>
          <textarea
            v-model="summary"
            rows="2"
            class="mt-2 w-full rounded-xl border border-zinc-200 px-4 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            placeholder="简短描述知识点内容"
          />
        </div>
        <div>
          <label class="text-sm font-medium text-slate-700">内容</label>
          <textarea
            v-model="content"
            rows="5"
            class="mt-2 w-full rounded-xl border border-zinc-200 px-4 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            placeholder="请输入知识点详细内容"
          />
          <p v-if="formErrors.content" class="mt-1 text-xs text-rose-600">{{ formErrors.content }}</p>
        </div>
      </div>
      <template #footer-start>
        <AppDialogButton @click="closeDialog">取消</AppDialogButton>
      </template>
      <template #footer-end>
        <AppDialogButton variant="primary" :disabled="submitDisabled" @click="submitDialog">
          {{ dialogActionLabel }}
        </AppDialogButton>
      </template>
  </AppDialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import type { KnowledgeBaseItem, KnowledgeStatus } from '../data/knowledgeBaseStore'
import type { ProjectRecord } from '../data/projectStore'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

const props = defineProps<{
  modelValue: boolean
  mode: 'create' | 'edit'
  projects: ProjectRecord[]
  initialItem?: KnowledgeBaseItem | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', payload: {
    title: string
    tags: string[]
    projectId: string | null
    status: KnowledgeStatus
    summary: string
    content: string
  }): void
}>()

const title = ref('')
const tagInput = ref('')
const tags = ref<string[]>([])
const projectId = ref('')
const status = ref<KnowledgeStatus>('draft')
const summary = ref('')
const content = ref('')
const tagError = ref('')

const formErrors = ref({
  title: '',
  content: ''
})

const dialogTitle = computed(() => (props.mode === 'edit' ? '编辑知识条目' : '新建知识条目'))
const dialogActionLabel = computed(() => (props.mode === 'edit' ? '保存' : '创建'))
const submitDisabled = computed(() => !title.value.trim() || !content.value.trim())

const resetForm = () => {
  title.value = ''
  tagInput.value = ''
  tags.value = []
  projectId.value = ''
  status.value = 'draft'
  summary.value = ''
  content.value = ''
  formErrors.value = { title: '', content: '' }
  tagError.value = ''
}

const initForm = async () => {
  const initial = props.initialItem
  title.value = initial?.title ?? ''
  tags.value = Array.isArray(initial?.tags) ? initial!.tags : []
  tagInput.value = ''
  projectId.value = initial?.projectId != null ? String(initial.projectId) : ''
  status.value = initial?.status ?? 'draft'
  summary.value = initial?.summary ?? ''
  content.value = initial?.content ?? ''
  formErrors.value = { title: '', content: '' }
  tagError.value = ''
  await nextTick()
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      initForm()
    } else {
      resetForm()
    }
  }
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const normalizeTag = (value: string) => value.trim().replace(/\s+/g, ' ')

const addTag = () => {
  const next = normalizeTag(tagInput.value)
  if (!next) {
    tagError.value = ''
    return
  }
  if (tags.value.includes(next)) {
    tagError.value = '该标签已存在'
    return
  }
  tags.value = [...tags.value, next]
  tagInput.value = ''
  tagError.value = ''
}

const removeTag = (value: string) => {
  tags.value = tags.value.filter((tag) => tag !== value)
  tagError.value = ''
}

const validateForm = () => {
  formErrors.value.title = title.value.trim() ? '' : '请输入条目名称'
  formErrors.value.content = content.value.trim() ? '' : '请输入内容'
  return !formErrors.value.title && !formErrors.value.content
}

const submitDialog = () => {
  if (submitDisabled.value || !validateForm()) return
  emit('submit', {
    title: title.value.trim(),
    tags: tags.value,
    projectId: projectId.value ? projectId.value : null,
    status: status.value,
    summary: summary.value.trim(),
    content: content.value.trim()
  })
  emit('update:modelValue', false)
}
</script>
