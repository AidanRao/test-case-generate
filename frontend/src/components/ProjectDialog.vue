<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
  >
    <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">{{ dialogTitle }}</h2>
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          @click="closeDialog"
        >
          ×
        </button>
      </div>
      <div class="mt-5 space-y-4">
        <template v-if="isCreateMode && step === 2">
          <div>
            <h3 class="text-sm font-medium text-slate-700">需求预览</h3>
            <div class="mt-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-sm">
              <div
                v-if="isParsing"
                class="flex items-center gap-3 rounded-lg border border-dashed border-slate-200 bg-white px-4 py-4 text-sm text-slate-600"
              >
                <div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-sky-600"></div>
                <span>{{ parsingText }}</span>
              </div>
              <div
                v-else-if="!isFileValid"
                class="rounded-lg border border-dashed border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600"
              >
                {{ formErrors.file || '需求文件不符合要求' }}
              </div>
              <div v-else class="space-y-3">
                <div class="flex items-center gap-2 text-xs text-slate-500">
                  <span class="rounded-full bg-slate-100 px-2 py-0.5">模块数 {{ modules.length }}</span>
                  <span class="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700">
                    需求数 {{ totalRequirements }}
                  </span>
                </div>
                <div class="space-y-2">
                  <div
                    v-for="(group, groupIndex) in modules"
                    :key="groupIndex"
                    class="rounded-lg border border-slate-200 bg-white px-3 py-2"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-medium text-slate-700">{{ group.module }}</span>
                      <span class="text-xs text-slate-500">需求 {{ group.requirements.length }}</span>
                    </div>
                    <ul class="mt-2 space-y-1 text-xs text-slate-500">
                      <li v-for="(item, idx) in group.requirements" :key="idx">
                        {{ item.title }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template v-else-if="isCreateMode && step === 3">
          <div class="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <h3 class="text-sm font-medium text-slate-700">生成测试用例</h3>
            <p class="mt-2 text-xs text-slate-500">请选择在创建项目后的生成方式</p>
            <div class="mt-4 space-y-3 text-sm text-slate-600">
              <label class="flex items-start gap-3 rounded-xl border border-slate-200 px-3 py-3">
                <input v-model="generateMode" type="radio" value="now" class="mt-1 h-4 w-4" />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-slate-700">立刻生成</span>
                  </div>
                  <p class="mt-1 text-xs text-slate-500">创建完成后立即开始生成任务</p>
                </div>
              </label>
              <label class="flex items-start gap-3 rounded-xl border border-slate-200 px-3 py-3">
                <input v-model="generateMode" type="radio" value="later" class="mt-1 h-4 w-4" />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-slate-700">稍后生成</span>
                  </div>
                  <p class="mt-1 text-xs text-slate-500">可在项目详情页随时触发生成</p>
                </div>
              </label>
            </div>
          </div>
        </template>
        <template v-else>
          <div>
            <label class="text-sm font-medium text-slate-700">项目名称</label>
            <input
              v-model="name"
              class="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
              placeholder="请输入项目名称"
            />
            <p v-if="formErrors.name" class="mt-1 text-xs text-rose-600">{{ formErrors.name }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">项目编号</label>
            <input
              v-model="code"
              class="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
              placeholder="例如 PRJ-002"
            />
            <p v-if="formErrors.code" class="mt-1 text-xs text-rose-600">{{ formErrors.code }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">需求文件</label>
            <input
              ref="fileInputRef"
              type="file"
              accept=".json,application/json"
              class="mt-2 w-full rounded-xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500"
              @change="handleFileChange"
            />
            <p v-if="fileName" class="mt-2 text-xs text-slate-500">已选择：{{ fileName }}</p>
            <p v-if="formErrors.file" class="mt-1 text-xs text-rose-600">{{ formErrors.file }}</p>
          </div>
        </template>
      </div>
      <div class="mt-6 flex justify-end gap-3">
        <button
          class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
          @click="handleSecondaryAction"
        >
          {{ secondaryLabel }}
        </button>
        <button
          class="rounded-full bg-sky-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-700"
          :class="primaryDisabled ? 'cursor-not-allowed opacity-60 hover:bg-sky-600' : ''"
          :disabled="primaryDisabled"
          @click="handlePrimaryAction"
        >
          {{ primaryLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { ModuleGroup } from '../data/projectStore'

const props = defineProps<{
  modelValue: boolean
  mode: 'create' | 'edit'
  initialName?: string
  initialCode?: string
  initialModules?: ModuleGroup[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', payload: { name: string; code: string; modules: ModuleGroup[]; generateNow?: boolean }): void
}>()

const name = ref('')
const code = ref('')
const fileName = ref('')
const modules = ref<ModuleGroup[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const step = ref(1)
const isFileValid = ref(false)
const isParsing = ref(false)
const parsingText = ref('需求解析中...')
const generateMode = ref<'now' | 'later'>('now')

const formErrors = ref({
  name: '',
  code: '',
  file: ''
})

const dialogTitle = computed(() => (props.mode === 'edit' ? '编辑项目' : '新建项目'))
const isCreateMode = computed(() => props.mode === 'create')
const primaryLabel = computed(() => {
  if (!isCreateMode.value) return '保存'
  if (step.value === 1) return '下一步'
  if (step.value === 2) return '下一步'
  return '创建'
})
const secondaryLabel = computed(() => {
  if (!isCreateMode.value) return '取消'
  return step.value === 1 ? '取消' : '上一步'
})
const primaryDisabled = computed(() => isCreateMode.value && step.value === 2 && !isFileValid.value)
const totalRequirements = computed(() =>
  modules.value.reduce((sum, group) => sum + group.requirements.length, 0)
)

const resetForm = () => {
  name.value = ''
  code.value = ''
  fileName.value = ''
  modules.value = []
  selectedFile.value = null
  step.value = 1
  isFileValid.value = false
  isParsing.value = false
  generateMode.value = 'now'
  formErrors.value = { name: '', code: '', file: '' }
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const initForm = async () => {
  name.value = props.initialName ?? ''
  code.value = props.initialCode ?? ''
  modules.value = props.initialModules ?? []
  fileName.value = props.mode === 'edit' && modules.value.length > 0 ? '已加载现有需求' : ''
  selectedFile.value = null
  step.value = 1
  isFileValid.value = props.mode === 'edit' ? modules.value.length > 0 : false
  isParsing.value = false
  generateMode.value = 'now'
  formErrors.value = { name: '', code: '', file: '' }
  await nextTick()
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
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

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }
  selectedFile.value = file
  fileName.value = file.name
  formErrors.value.file = ''
  isFileValid.value = false
}

const validateBase = () => {
  formErrors.value.name = name.value.trim() ? '' : '请输入项目名称'
  formErrors.value.code = code.value.trim() ? '' : '请输入项目编号'
  return !formErrors.value.name && !formErrors.value.code
}

const parseRequirementFile = async () => {
  isParsing.value = true
  parsingText.value = '需求解析中...'
  formErrors.value.file = ''
  modules.value = []
  isFileValid.value = false
  if (!selectedFile.value) {
    formErrors.value.file = '请上传 json 格式的需求文件'
    isParsing.value = false
    return
  }
  try {
    const delay = 1000 + Math.floor(Math.random() * 1000)
    const text = await selectedFile.value.text()
    await new Promise<void>((resolve) => {
      window.setTimeout(() => resolve(), delay)
    })
    const parsed = JSON.parse(text)
    if (!Array.isArray(parsed)) {
      formErrors.value.file = '需求文件格式不正确，请上传数组格式的 JSON'
      isParsing.value = false
      return
    }
    let invalidFound = false
    const normalized = parsed
      .map((item) => {
        if (!item || typeof item !== 'object') {
          invalidFound = true
          return null
        }
        const moduleName = typeof item.module === 'string' && item.module.trim() ? item.module.trim() : ''
        if (!moduleName || !Array.isArray(item.requirements)) {
          invalidFound = true
          return null
        }
        const requirements = item.requirements
          .map((req: any) => {
            const title = typeof req?.title === 'string' ? req.title.trim() : ''
            const type = typeof req?.type === 'string' ? req.type.trim() : ''
            const code = typeof req?.code === 'string' ? req.code.trim() : (typeof req?.ID === 'string' ? req.ID.trim() : '')
            const content = typeof req?.content === 'string' ? req.content.trim() : ''
            if (!title || !type || !code || !content) {
              invalidFound = true
              return null
            }
            return { title, type, code, content, ID: req?.ID }
          })
          .filter(Boolean)
        if (requirements.length === 0) {
          invalidFound = true
          return null
        }
        return { module: moduleName, requirements }
      })
      .filter(Boolean) as ModuleGroup[]
    if (normalized.length === 0 || invalidFound) {
      formErrors.value.file = '需求文件字段缺失或格式不正确'
      isParsing.value = false
      return
    }
    modules.value = normalized
    isFileValid.value = true
    isParsing.value = false
  } catch {
    formErrors.value.file = '需求文件解析失败，请确认是合法的 JSON'
    isParsing.value = false
  }
}

const handlePrimaryAction = async () => {
  if (!isCreateMode.value) {
    if (!validateBase()) return
    emit('submit', {
      name: name.value.trim(),
      code: code.value.trim(),
      modules: modules.value
    })
    emit('update:modelValue', false)
    return
  }
  if (step.value === 1) {
    if (!validateBase()) {
      return
    }
    step.value = 2
    await parseRequirementFile()
    return
  }
  if (step.value === 2) {
    if (!validateBase() || !isFileValid.value) {
      return
    }
    step.value = 3
    return
  }
  if (!validateBase() || !isFileValid.value) {
    return
  }
  emit('submit', {
    name: name.value.trim(),
    code: code.value.trim(),
    modules: modules.value,
    generateNow: generateMode.value === 'now'
  })
  emit('update:modelValue', false)
}

const handleSecondaryAction = () => {
  if (!isCreateMode.value) {
    closeDialog()
    return
  }
  if (step.value === 1) {
    closeDialog()
    return
  }
  step.value = step.value === 2 ? 1 : 2
}
</script>
