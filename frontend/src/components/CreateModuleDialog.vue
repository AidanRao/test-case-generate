<template>
  <el-dialog
    :model-value="modelValue"
    width="420px"
    align-center
    title="新增模块"
    @close="closeDialog"
  >
    <div class="space-y-2">
      <p class="text-xs font-medium text-slate-400">模块名</p>
      <input
        ref="nameInput"
        v-model="moduleName"
        class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
        placeholder="请输入模块名"
        @keydown.enter="submitForm"
      />
    </div>
    <template #footer>
      <div class="flex items-center gap-3">
        <button
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          type="button"
          @click="closeDialog"
        >
          取消
        </button>
        <button
          class="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-700"
          type="button"
          @click="submitForm"
        >
          确定
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  existingModules: string[]
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'create', value: string): void
}>()

const moduleName = ref('')
const nameInput = ref<HTMLInputElement | null>(null)

watch(
  () => props.modelValue,
  async (value) => {
    if (!value) {
      return
    }
    moduleName.value = ''
    await nextTick()
    nameInput.value?.focus()
  }
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const submitForm = () => {
  const nextModuleName = moduleName.value.trim()
  if (!nextModuleName) {
    window.alert('请输入模块名')
    return
  }
  if (props.existingModules.includes(nextModuleName)) {
    window.alert('模块名已存在')
    return
  }
  emit('create', nextModuleName)
}
</script>
