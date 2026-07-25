<template>
  <AppDialog
    :model-value="modelValue"
    title="测试用例详情"
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
        <div class="grid gap-4 rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-sm">
          <div class="min-h-14">
            <p class="text-xs font-medium text-slate-400">用例标题</p>
            <div class="mt-1 flex items-center gap-2">
              <div
                v-if="isEditing"
                class="relative h-8 w-11 shrink-0 rounded-full"
                :class="getPriorityBadgeClass(draftTestcase.priority)"
              >
                <select
                  v-model="draftTestcase.priority"
                  aria-label="优先级"
                  class="relative z-10 h-full w-full cursor-pointer appearance-none rounded-full bg-transparent pl-2 pr-4 text-xs font-semibold outline-none ring-1 ring-inset ring-black/5 transition focus:ring-2 focus:ring-zinc-400"
                >
                  <option v-for="item in PRIORITY_LEVELS" :key="item" :value="item">
                    {{ item }}
                  </option>
                </select>
                <span class="pointer-events-none absolute right-1.5 top-1/2 z-20 -translate-y-1/2 text-[9px] leading-none opacity-60">▾</span>
              </div>
              <span
                v-else
                class="inline-flex h-6 min-w-10 shrink-0 items-center justify-center rounded-full px-1.5 text-xs font-semibold"
                :class="getPriorityBadgeClass(displayTestcase.priority)"
              >
                {{ displayTestcase.priority || '暂无' }}
              </span>
              <input
                v-if="isEditing"
                v-model="draftTestcase.title"
                class="h-8 min-w-0 flex-1 rounded-lg border border-zinc-200 px-3 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
              />
              <p v-else class="min-w-0 flex-1 break-words font-semibold leading-6 text-slate-700">
                {{ displayTestcase.title }}
              </p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs font-medium text-slate-400">用例类型</p>
              <select
                v-if="isEditing"
                v-model="draftTestcase.type"
                class="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
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
            <div>
              <p class="text-xs font-medium text-slate-400">用例场景</p>
              <select
                v-if="isEditing"
                v-model="draftTestcase.scenario_type"
                class="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
              >
                <option v-for="item in SCENARIO_TYPES" :key="item" :value="item">
                  {{ item }}
                </option>
              </select>
              <span v-else class="mt-1 inline-flex rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-700">
                {{ displayTestcase.scenario_type }}
              </span>
            </div>
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
              class="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
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
                  class="w-full rounded-lg border border-zinc-200 px-2 py-1 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
                />
                <span v-else>{{ step.step_desc }}</span>
              </div>
              <div class="px-4 py-3 text-slate-600">
                <input
                  v-if="isEditing"
                  :value="draftTestcase.test_steps[index]?.expectation ?? ''"
                  @input="updateStep(index, 'expectation', ($event.target as HTMLInputElement).value)"
                  class="w-full rounded-lg border border-zinc-200 px-2 py-1 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
                />
                <span v-else>{{ step.expectation }}</span>
              </div>
              <div class="flex items-center px-2">
                <AppDialogButton
                  v-if="isEditing"
                  variant="danger"
                  class="!min-h-7 !px-2 !py-0.5 text-xs"
                  @click="removeStep(index)"
                >
                  删除
                </AppDialogButton>
              </div>
            </div>
          </div>
          <div v-if="isEditing" class="mt-3 flex items-center gap-2">
            <AppDialogButton
              class="!min-h-7 !px-3 !py-1 text-xs"
              @click="addStep"
            >
              新增步骤
            </AppDialogButton>
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
import { computed, ref, watch } from 'vue'
import {
  PRIORITY_LEVELS,
  SCENARIO_TYPES,
  type TestCaseDetailItem,
  type TestCasePriority
} from '../data/testcase'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

type EditableTestCase = Omit<TestCaseDetailItem, 'test_steps'> & {
  test_steps: Array<{ expectation: string; step_desc: string }>
}

const props = defineProps<{
  modelValue: boolean
  testcase: TestCaseDetailItem | null
  readOnly?: boolean
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
  scenario_type: SCENARIO_TYPES[0],
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
        scenario_type: SCENARIO_TYPES[0],
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
    scenario_type: source?.scenario_type || SCENARIO_TYPES[0],
    priority: source?.priority,
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
const saveDisabled = computed(() => !draftTestcase.value.title.trim())

const priorityBadgeClasses: Record<TestCasePriority, string> = {
  P0: 'bg-rose-50 text-rose-700',
  P1: 'bg-amber-50 text-amber-700',
  P2: 'bg-sky-50 text-sky-700',
  P3: 'bg-slate-200 text-slate-600'
}

const getPriorityBadgeClass = (priority?: TestCasePriority) =>
  priority ? priorityBadgeClasses[priority] : 'bg-slate-100 text-slate-500'

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
  if (saveDisabled.value) return
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
