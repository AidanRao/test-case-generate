<template>
  <AppDialog
    :model-value="modelValue"
    :title="title"
    size="sm"
    @update:model-value="handleModelUpdate"
  >
    <p class="text-sm leading-6 text-zinc-600">{{ message }}</p>

    <template #footer-start>
      <AppDialogButton @click="handleCancel">{{ cancelText }}</AppDialogButton>
    </template>
    <template #footer-end>
      <AppDialogButton :variant="tone === 'danger' ? 'danger' : 'primary'" @click="handleConfirm">
        {{ confirmText }}
      </AppDialogButton>
    </template>
  </AppDialog>
</template>

<script setup lang="ts">
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    message: string
    confirmText?: string
    cancelText?: string
    tone?: 'primary' | 'danger'
  }>(),
  {
    title: '确认操作',
    confirmText: '确定',
    cancelText: '取消',
    tone: 'primary'
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

const handleModelUpdate = (value: boolean) => {
  if (!value) {
    handleCancel()
    return
  }
  emit('update:modelValue', value)
}
</script>
