<template>
  <el-dialog
    :model-value="modelValue"
    width="720px"
    align-center
    @close="closeDialog"
  >
    <div class="space-y-6">
      <div>
        <div class="flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-800">
            需求详情
            <span class="ml-2 text-sm font-medium text-slate-500">({{ displayRequirement.id }})</span>
          </h3>
          <div class="mt-3 flex items-center gap-2">
            <button
              v-if="!isEditing"
              class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
              type="button"
              @click="startEdit"
            >
              编辑
            </button>
            <button
              v-if="!isEditing"
              class="rounded-full border border-rose-200 px-3 py-1 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700"
              type="button"
              @click="handleDelete"
            >
              删除
            </button>
            <button
              v-if="isEditing"
              class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
              type="button"
              @click="cancelEdit"
            >
              取消
            </button>
            <button
              v-if="isEditing"
              class="rounded-full bg-sky-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-sky-700"
              type="button"
              @click="saveEdit"
            >
              保存
            </button>
          </div>
        </div>
        <div class="mt-4 grid gap-4 rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-sm">
          <div>
            <p class="text-xs font-medium text-slate-400">需求标题</p>
            <input
              v-if="isEditing"
              v-model="draftRequirement.title"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            />
            <p v-else class="mt-1 font-medium text-slate-700">{{ displayRequirement.title }}</p>
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
            <p class="text-xs font-medium text-slate-400">需求类型</p>
            <select
              v-if="isEditing"
              v-model="draftRequirement.type"
              class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
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
          <div>
            <p class="text-xs font-medium text-slate-400">需求详情</p>
            <textarea
              v-if="isEditing"
              v-model="draftRequirement.content"
              rows="4"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            ></textarea>
            <p v-else class="mt-1 leading-relaxed text-slate-600">{{ displayRequirement.content }}</p>
          </div>
        </div>
      </div>

      <div>
        <div class="flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-800">测试项列表</h3>
          <button
            v-if="!isGenerating"
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
            type="button"
            @click="emitGenerate"
          >
            {{ testcases.length > 0 ? '重新生成测试用例' : '生成测试用例' }}
          </button>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-if="testcases.length === 0"
            class="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm"
            :class="isGenerating ? 'text-amber-600' : 'text-slate-500'"
          >
            <div v-if="isGenerating" class="flex items-center gap-2">
              <span class="h-3 w-3 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600"></span>
              正在生成测试用例
            </div>
            <span v-else>暂无测试项</span>
          </div>
          <div v-else class="space-y-2">
            <button
              v-for="(item, index) in testcases"
              :key="item.id || item.code || index"
              type="button"
              class="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm transition hover:border-slate-300 hover:bg-slate-50"
              @click="openTestcase(item)"
            >
              <div class="min-w-0">
                <p class="truncate font-medium text-slate-700">{{ item.title }}</p>
              </div>
              <span class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                {{ item.type }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
export interface RequirementDetailItem {
  title: string
  type: string
  module: string
  content: string
  ID?: string
  code?: string
}

export interface RequirementTestCaseItem {
  id?: string
  code: string
  title: string
  type: string
  requirement_id?: string
  requirement_code?: string
  test_steps: Array<{ expectation: string; step_desc: string }>
  test_target_desc: string
  verify_method: string
}

const props = defineProps<{
  modelValue: boolean
  requirement: RequirementDetailItem | null
  testcases: RequirementTestCaseItem[]
  isGenerating?: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'open-testcase', value: RequirementTestCaseItem): void
  (event: 'save', value: RequirementDetailItem): void
  (event: 'delete', value: RequirementDetailItem): void
  (event: 'generate-testcases'): void
}>()

const isEditing = ref(false)
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

const closeDialog = () => {
  emit('update:modelValue', false)
}

const startEdit = () => {
  if (!props.requirement) return
  draftRequirement.value = { ...props.requirement }
  isEditing.value = true
}

const cancelEdit = () => {
  if (props.requirement) {
    draftRequirement.value = { ...props.requirement }
  }
  isEditing.value = false
}

const saveEdit = () => {
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

const openTestcase = (item: RequirementTestCaseItem) => {
  emit('open-testcase', item)
}
</script>
