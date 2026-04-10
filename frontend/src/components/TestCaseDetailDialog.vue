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
          <h3 class="text-base font-semibold text-slate-800">测试用例详情</h3>
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
            <p class="text-xs font-medium text-slate-400">用例标题</p>
            <input
              v-if="isEditing"
              v-model="draftTestcase.title"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            />
            <p v-else class="mt-1 font-medium text-slate-700">{{ displayTestcase.title }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-slate-400">用例类型</p>
            <select
              v-if="isEditing"
              v-model="draftTestcase.type"
              class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            >
              <option value="功能测试">功能测试</option>
              <option value="可靠性测试">可靠性测试</option>
              <option value="安全性测试">安全性测试</option>
              <option value="强度测试">强度测试</option>
              <option value="性能测试">性能测试</option>
              <option value="接口测试">接口测试</option>
              <option value="数据处理测试">数据处理测试</option>
              <option value="边界测试">边界测试</option>
              <option value="容量测试">容量测试</option>
              <option value="余量测试">余量测试</option>
            </select>
            <span v-else class="mt-1 inline-flex rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
              {{ displayTestcase.type }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs font-medium text-slate-400">用例编号</p>
              <p class="mt-1 font-medium text-slate-700">{{ displayTestcase.code }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-slate-400">验证方式</p>
              <p class="mt-1 font-medium text-slate-700">{{ displayTestcase.verify_method }}</p>
            </div>
          </div>
          <div>
            <p class="text-xs font-medium text-slate-400">验证目标</p>
            <textarea
              v-if="isEditing"
              v-model="draftTestcase.test_target_desc"
              rows="3"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            ></textarea>
            <p v-else class="mt-1 leading-relaxed text-slate-600">{{ displayTestcase.test_target_desc }}</p>
          </div>
        </div>
      </div>

      <div>
        <h3 class="text-base font-semibold text-slate-800">测试步骤</h3>
        <div class="mt-4">
          <div
            v-if="displayTestcase.test_steps.length === 0"
            class="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500"
          >
            暂无步骤
          </div>
          <div v-else class="overflow-hidden rounded-xl border border-slate-200 bg-white text-sm">
            <div class="grid grid-cols-[120px_1fr_1fr_auto] bg-slate-50 text-slate-500">
              <div class="px-4 py-2 text-xs font-medium">步骤</div>
              <div class="px-4 py-2 text-xs font-medium">操作</div>
              <div class="px-4 py-2 text-xs font-medium">预期结果</div>
              <div class="px-4 py-2 text-xs font-medium"></div>
            </div>
            <div
              v-for="(step, index) in stepItems"
              :key="index"
              class="grid grid-cols-[120px_1fr_1fr_auto] border-t border-slate-100"
            >
              <div class="px-4 py-3 font-medium text-slate-700">第 {{ index + 1 }} 步</div>
              <div class="px-4 py-3 text-slate-600">
                <input
                  v-if="isEditing"
                  :value="draftTestcase.test_steps[index]?.step_desc ?? ''"
                  @input="updateStep(index, 'step_desc', ($event.target as HTMLInputElement).value)"
                  class="w-full rounded-lg border border-slate-200 px-2 py-1 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
                />
                <span v-else>{{ step.step_desc }}</span>
              </div>
              <div class="px-4 py-3 text-slate-600">
                <input
                  v-if="isEditing"
                  :value="draftTestcase.test_steps[index]?.expectation ?? ''"
                  @input="updateStep(index, 'expectation', ($event.target as HTMLInputElement).value)"
                  class="w-full rounded-lg border border-slate-200 px-2 py-1 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
                />
                <span v-else>{{ step.expectation }}</span>
              </div>
              <div class="flex items-center px-2">
                <button
                  v-if="isEditing"
                  class="rounded-full border border-rose-200 px-2 py-0.5 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700"
                  type="button"
                  @click="removeStep(index)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
          <div v-if="isEditing" class="mt-3 flex items-center gap-2">
            <button
              class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
              type="button"
              @click="addStep"
            >
              新增步骤
            </button>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export interface TestCaseDetailItem {
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

type EditableTestCase = Omit<TestCaseDetailItem, 'test_steps'> & {
  test_steps: Array<{ expectation: string; step_desc: string }>
}

const props = defineProps<{
  modelValue: boolean
  testcase: TestCaseDetailItem | null
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'save', value: TestCaseDetailItem): void
  (event: 'delete', value: TestCaseDetailItem): void
}>()

const isEditing = ref(false)
const draftTestcase = ref<EditableTestCase>({
  id: '',
  code: '',
  title: '',
  type: '',
  requirement_id: '',
  requirement_code: '',
  test_steps: [],
  test_target_desc: '',
  verify_method: ''
})

watch(
  () => props.testcase,
  (value) => {
    if (value) {
      draftTestcase.value = {
        ...value,
        test_steps: (value.test_steps ?? []).map((step) => ({ ...step }))
      }
    } else {
      draftTestcase.value = {
        id: '',
        code: '',
        title: '',
        type: '',
        requirement_id: '',
        requirement_code: '',
        test_steps: [],
        test_target_desc: '',
        verify_method: ''
      }
    }
    isEditing.value = false
  },
  { immediate: true }
)

const displayTestcase = computed<TestCaseDetailItem>(() => {
  const source = isEditing.value ? draftTestcase.value : props.testcase
  return {
    id: source?.id,
    code: source?.code || '暂无',
    title: source?.title || '暂无',
    type: source?.type || '未知类型',
    requirement_id: source?.requirement_id,
    requirement_code: source?.requirement_code,
    test_steps: source?.test_steps ?? [],
    test_target_desc: source?.test_target_desc || '无',
    verify_method: source?.verify_method || '未知'
  }
})

const stepItems = computed(() => {
  return isEditing.value ? draftTestcase.value.test_steps : displayTestcase.value.test_steps
})

const closeDialog = () => {
  emit('update:modelValue', false)
}

const startEdit = () => {
  if (!props.testcase) return
  draftTestcase.value = {
    ...props.testcase,
    test_steps: (props.testcase.test_steps ?? []).map((step) => ({ ...step }))
  }
  isEditing.value = true
}

const cancelEdit = () => {
  if (props.testcase) {
    draftTestcase.value = {
      ...props.testcase,
      test_steps: (props.testcase.test_steps ?? []).map((step) => ({ ...step }))
    }
  }
  isEditing.value = false
}

const saveEdit = () => {
  emit('save', { ...draftTestcase.value })
  isEditing.value = false
}

const handleDelete = () => {
  if (!props.testcase) return
  emit('delete', props.testcase)
}

const addStep = () => {
  draftTestcase.value.test_steps = [
    ...draftTestcase.value.test_steps,
    { step_desc: '', expectation: '' }
  ]
}

const removeStep = (index: number) => {
  draftTestcase.value.test_steps = draftTestcase.value.test_steps.filter((_, idx) => idx !== index)
}

const updateStep = (index: number, field: 'step_desc' | 'expectation', value: string) => {
  const steps = draftTestcase.value.test_steps
  if (!steps[index]) {
    return
  }
  steps[index] = {
    ...steps[index],
    [field]: value
  }
  draftTestcase.value.test_steps = [...steps]
}
</script>
