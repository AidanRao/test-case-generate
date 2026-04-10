<template>
  <el-dialog
    :model-value="modelValue"
    width="420px"
    align-center
    @close="handleCancel"
  >
    <div class="space-y-4">
      <h3 class="text-base font-semibold text-slate-800">{{ title }}</h3>
      <p class="text-sm text-slate-600">{{ message }}</p>
      <div class="flex justify-end gap-2">
        <button
          class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
          type="button"
          @click="handleCancel"
        >
          {{ cancelText }}
        </button>
        <button
          class="rounded-full bg-sky-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-sky-700"
          type="button"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    message: string
    confirmText?: string
    cancelText?: string
  }>(),
  {
    title: '确认操作',
    confirmText: '确定',
    cancelText: '取消'
  }
)

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'confirm'): void
  (event: 'cancel'): void
}>()

const handleConfirm = () => {
  emit('confirm')
  emit('update:modelValue', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>
