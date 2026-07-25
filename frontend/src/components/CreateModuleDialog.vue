<template>
  <AppDialog
    :model-value="modelValue"
    title="新增模块"
    size="sm"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="space-y-2">
      <label for="module-name" class="text-sm font-medium text-zinc-700">模块名</label>
      <input
        id="module-name"
        ref="nameInput"
        v-model="moduleName"
        class="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-800 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
        placeholder="请输入模块名"
        @keydown.enter="submitForm"
      />
      <p v-if="moduleError" class="text-xs text-red-600">{{ moduleError }}</p>
    </div>

    <template #footer-start>
      <AppDialogButton @click="closeDialog">取消</AppDialogButton>
    </template>
    <template #footer-end>
      <AppDialogButton variant="primary" :disabled="submitDisabled" @click="submitForm">
        确定
      </AppDialogButton>
    </template>
  </AppDialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

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
const normalizedModuleName = computed(() => moduleName.value.trim())
const moduleError = computed(() => {
  if (!normalizedModuleName.value) return ''
  return props.existingModules.includes(normalizedModuleName.value) ? '模块名已存在' : ''
})
const submitDisabled = computed(() => !normalizedModuleName.value || Boolean(moduleError.value))

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
  if (submitDisabled.value) return
  emit('create', normalizedModuleName.value)
}
</script>
