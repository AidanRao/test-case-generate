<template>
  <el-dialog
    :model-value="modelValue"
    :width="dialogWidth"
    align-center
    append-to-body
    class="app-dialog"
    modal-class="app-dialog-overlay"
    :show-close="false"
    :close-on-click-modal="closeOnClickOutside"
    :close-on-press-escape="closeOnPressEscape"
    @update:model-value="handleModelUpdate"
    @close="emit('close')"
  >
    <template #header>
      <div v-if="title || description || $slots['header-actions']" class="app-dialog__header">
        <div v-if="title || description" class="app-dialog__heading">
          <h2 v-if="title" class="app-dialog__title">{{ title }}</h2>
          <p v-if="description" class="app-dialog__description">{{ description }}</p>
        </div>
        <div v-if="$slots['header-actions']" class="app-dialog__header-actions">
          <slot name="header-actions" />
        </div>
      </div>
    </template>

    <slot />

    <template v-if="hasFooter()" #footer>
      <div class="app-dialog__actions">
        <div class="app-dialog__actions-start">
          <slot name="footer-start" />
        </div>
        <div class="app-dialog__actions-end">
          <slot name="footer-end" />
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue'

export type AppDialogSize = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    description?: string
    size?: AppDialogSize
    closeOnClickOutside?: boolean
    closeOnPressEscape?: boolean
  }>(),
  {
    title: '',
    description: '',
    size: 'md',
    closeOnClickOutside: true,
    closeOnPressEscape: true
  }
)

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'close'): void
}>()

const slots = useSlots()

const widths: Record<AppDialogSize, string> = {
  sm: '420px',
  md: '520px',
  lg: '760px'
}

const dialogWidth = computed(() => widths[props.size])
// Named slots can be added and removed dynamically by the parent (for example,
// detail dialogs only expose actions while editing). Read the slots during each
// render instead of caching their initial presence in a computed value.
const hasFooter = () => Boolean(slots['footer-start'] || slots['footer-end'])

const handleModelUpdate = (value: boolean) => {
  emit('update:modelValue', value)
}
</script>
