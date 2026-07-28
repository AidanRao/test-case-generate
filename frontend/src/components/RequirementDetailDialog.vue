<template>
  <AppDialog
    :model-value="modelValue"
    title="需求详情"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template v-if="!isEditing && !readOnly" #header-actions>
      <AppDialogButton
        class="!min-h-7 !px-3 !py-1 text-xs"
        @click="startEdit"
      >
        编辑
      </AppDialogButton>
      <AppDialogButton
        variant="danger"
        class="!min-h-7 !px-3 !py-1 text-xs"
        @click="handleDelete"
      >
        删除
      </AppDialogButton>
    </template>

    <div class="space-y-6">
      <div>
        <button
          class="flex min-w-0 items-center gap-2 text-left text-base font-semibold text-slate-800 transition hover:text-slate-600"
          type="button"
          :aria-expanded="requirementExpanded"
          @click="toggleRequirement"
        >
          <el-icon class="text-sm text-slate-500">
            <ArrowDown v-if="requirementExpanded" />
            <ArrowRight v-else />
          </el-icon>
          <span>基本信息</span>
        </button>
        <div v-show="requirementExpanded" class="mt-4 grid gap-4 rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-sm">
          <div class="grid grid-cols-2 gap-4">
            <div class="min-w-0">
              <p class="text-xs font-medium text-slate-400">需求标题</p>
              <input
                v-if="isEditing"
                v-model="draftRequirement.title"
                class="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
              />
              <p v-else class="mt-1 truncate font-medium text-slate-700" :title="displayRequirement.title">{{ displayRequirement.title }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-slate-400">需求类型</p>
              <select
                v-if="isEditing"
                v-model="draftRequirement.type"
                class="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
              >
                <option value="功能需求">功能需求</option>
                <option value="可靠性需求">可靠性需求</option>
                <option value="安全性需求">安全性需求</option>
                <option value="强度需求">强度需求</option>
                <option value="性能需求">性能需求</option>
                <option value="接口需求">接口需求</option>
                <option value="数据处理需求">数据处理需求</option>
                <option value="边界需求">边界需求</option>
                <option value="容量需求">容量需求</option>
                <option value="余量需求">余量需求</option>
              </select>
              <span v-else class="mt-1 inline-flex rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-700">
                {{ displayRequirement.type }}
              </span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs font-medium text-slate-400">需求编号</p>
              <p class="mt-1 font-medium text-slate-700">{{ displayRequirement.id }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-slate-400">所属功能</p>
              <p class="mt-1 font-medium text-slate-700">{{ displayRequirement.module }}</p>
            </div>
          </div>
          <div>
            <button
              class="flex items-center gap-1 text-xs font-medium text-slate-400 transition hover:text-slate-500"
              type="button"
              :aria-expanded="requirementContentExpanded"
              @click="toggleRequirementContent"
            >
              <span>需求详情</span>
              <el-icon class="text-xs">
                <ArrowDown v-if="requirementContentExpanded" />
                <ArrowRight v-else />
              </el-icon>
            </button>
            <textarea
              v-if="isEditing && requirementContentExpanded"
              v-model="draftRequirement.content"
              rows="4"
              class="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            ></textarea>
            <div
              v-else-if="requirementContentExpanded"
              class="requirement-markdown mt-1 text-slate-600"
              v-html="renderedRequirementContent"
            ></div>
          </div>
        </div>
      </div>

      <div>
        <div class="flex items-center justify-between">
          <button
            class="flex min-w-0 items-center gap-2 text-left text-base font-semibold text-slate-800 transition hover:text-slate-600"
            type="button"
            :aria-expanded="testcasesExpanded"
            @click="toggleTestcases"
          >
            <el-icon class="text-sm text-slate-500">
              <ArrowDown v-if="testcasesExpanded" />
              <ArrowRight v-else />
            </el-icon>
            <span>测试项列表</span>
            <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500">
              {{ testcases.length }}
            </span>
          </button>
          <GenerationStatusBadge
            v-if="isGenerating"
            active
            label="生成中"
          />
          <GenerationStatusBadge
            v-else-if="isWaiting"
            label="等待中"
          />
          <AppDialogButton
            v-else
            class="!min-h-7 !px-3 !py-1 text-xs"
            :disabled="generationDisabled"
            @click="emitGenerate"
          >
            {{ testcases.length > 0 ? '重新生成测试用例' : '生成测试用例' }}
          </AppDialogButton>
        </div>
        <div v-show="testcasesExpanded" class="mt-4 space-y-3">
          <div
            v-if="testcases.length === 0"
            class="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm"
            :class="isGenerating ? 'text-amber-600' : isWaiting ? 'text-slate-600' : 'text-slate-500'"
          >
            <div v-if="isGenerating" class="flex items-center gap-2">
              <span class="h-3 w-3 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600"></span>
              正在生成测试用例
            </div>
            <span v-else-if="isWaiting">等待生成测试用例</span>
            <span v-else>暂无测试项</span>
          </div>
          <div v-else class="space-y-2">
            <TestCaseCard
              v-for="(item, index) in testcases"
              :key="item.id || item.code || index"
              :testcase="item"
              @select="openTestcase(item)"
            />
          </div>
        </div>
      </div>
    </div>

    <template v-if="isEditing" #footer-start>
      <AppDialogButton @click="cancelEdit">取消</AppDialogButton>
    </template>
    <template v-if="isEditing" #footer-end>
      <AppDialogButton variant="primary" :disabled="saveDisabled" @click="saveEdit">
        保存
      </AppDialogButton>
    </template>
  </AppDialog>
</template>

<script setup lang="ts">
import DOMPurify from 'dompurify'
import { ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import { katex } from '@mdit/plugin-katex'
import MarkdownIt from 'markdown-it'
import 'katex/dist/katex.min.css'
import { computed, ref, watch } from 'vue'
import type { RequirementTestCaseItem } from '../data/testcase'
import GenerationStatusBadge from './generation/GenerationStatusBadge.vue'
import TestCaseCard from './testcases/TestCaseCard.vue'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'
export interface RequirementDetailItem {
  title: string
  type: string
  module: string
  content: string
  ID?: string
  code?: string
}

const props = defineProps<{
  modelValue: boolean
  requirement: RequirementDetailItem | null
  testcases: RequirementTestCaseItem[]
  isGenerating?: boolean
  isWaiting?: boolean
  generationDisabled?: boolean
  readOnly?: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'open-testcase', value: RequirementTestCaseItem): void
  (event: 'save', value: RequirementDetailItem): void
  (event: 'delete', value: RequirementDetailItem): void
  (event: 'generate-testcases'): void
}>()

const isEditing = ref(false)
const requirementExpanded = ref(true)
const requirementContentExpanded = ref(true)
const testcasesExpanded = ref(true)
const draftRequirement = ref<RequirementDetailItem>({
  title: '',
  type: '',
  module: '',
  content: ''
})

watch(
  () => props.requirement,
  (value) => {
    if (value) {
      draftRequirement.value = { ...value }
    } else {
      draftRequirement.value = { title: '', type: '', module: '', content: '' }
    }
    isEditing.value = false
    requirementExpanded.value = true
    requirementContentExpanded.value = true
    testcasesExpanded.value = true
  },
  { immediate: true }
)

const displayRequirement = computed(() => {
  const source = isEditing.value ? draftRequirement.value : props.requirement
  return {
    id: source?.code || '暂无',
    title: source?.title || '暂无需求',
    type: source?.type || '未知类型',
    module: source?.module || '未知功能',
    content: source?.content || '无详细内容'
  }
})
const saveDisabled = computed(() => !draftRequirement.value.title.trim() || !draftRequirement.value.content.trim())

const markdownRenderer = new MarkdownIt({
  breaks: true,
  html: true,
  linkify: true
}).use(katex, {
  throwOnError: false
})

const renderMarkdown = (markdown: string) => {
  const html = markdownRenderer.render(markdown)
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['target'],
    USE_PROFILES: {
      html: true,
      mathMl: true,
      svg: true
    }
  })
}

const renderedRequirementContent = computed(() => renderMarkdown(displayRequirement.value.content))

const startEdit = () => {
  if (!props.requirement) return
  draftRequirement.value = { ...props.requirement }
  requirementExpanded.value = true
  requirementContentExpanded.value = true
  testcasesExpanded.value = false
  isEditing.value = true
}

const cancelEdit = () => {
  if (props.requirement) {
    draftRequirement.value = { ...props.requirement }
  }
  isEditing.value = false
}

const saveEdit = () => {
  if (saveDisabled.value) return
  emit('save', { ...draftRequirement.value })
  isEditing.value = false
}

const handleDelete = () => {
  if (!props.requirement) return
  emit('delete', props.requirement)
}

const emitGenerate = () => {
  emit('generate-testcases')
}

const toggleRequirement = () => {
  requirementExpanded.value = !requirementExpanded.value
}

const toggleRequirementContent = () => {
  requirementContentExpanded.value = !requirementContentExpanded.value
}

const toggleTestcases = () => {
  testcasesExpanded.value = !testcasesExpanded.value
}

const openTestcase = (item: RequirementTestCaseItem) => {
  emit('open-testcase', item)
}
</script>

<style scoped>
.requirement-markdown {
  line-height: 1.7;
  overflow-x: auto;
  word-break: break-word;
}

.requirement-markdown :deep(p),
.requirement-markdown :deep(ul),
.requirement-markdown :deep(ol),
.requirement-markdown :deep(pre),
.requirement-markdown :deep(blockquote),
.requirement-markdown :deep(table) {
  margin-top: 0.5rem;
}

.requirement-markdown :deep(h1),
.requirement-markdown :deep(h2),
.requirement-markdown :deep(h3),
.requirement-markdown :deep(h4),
.requirement-markdown :deep(h5),
.requirement-markdown :deep(h6) {
  margin-top: 0.75rem;
  font-weight: 700;
  color: #334155;
}

.requirement-markdown :deep(ul) {
  list-style: disc;
  padding-left: 1.25rem;
}

.requirement-markdown :deep(ol) {
  list-style: decimal;
  padding-left: 1.25rem;
}

.requirement-markdown :deep(a) {
  color: #0284c7;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.requirement-markdown :deep(blockquote) {
  border-left: 3px solid #cbd5e1;
  padding-left: 0.75rem;
  color: #475569;
}

.requirement-markdown :deep(code) {
  border-radius: 0.25rem;
  background: #e2e8f0;
  padding: 0.05rem 0.25rem;
  color: #334155;
  font-size: 0.85em;
}

.requirement-markdown :deep(pre) {
  overflow-x: auto;
  border-radius: 0.5rem;
  background: #0f172a;
  padding: 0.75rem;
  color: #e2e8f0;
}

.requirement-markdown :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.requirement-markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.requirement-markdown :deep(th),
.requirement-markdown :deep(td) {
  border: 1px solid #cbd5e1;
  padding: 0.5rem 0.625rem;
  text-align: left;
  vertical-align: top;
}

.requirement-markdown :deep(th) {
  background: #e2e8f0;
  color: #334155;
  font-weight: 700;
}
</style>
