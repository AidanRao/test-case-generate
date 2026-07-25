<template>
  <AppDialog
    :model-value="modelValue"
    title="导出测试用例"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="grid gap-3">
      <button
        v-for="item in formats"
        :key="item.value"
        type="button"
        class="flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left text-sm transition"
        :class="selectedFormat === item.value
          ? 'border-zinc-950 bg-zinc-50 shadow-sm'
          : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50'"
        @click="selectedFormat = item.value"
      >
        <div class="flex items-center gap-3">
          <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 text-zinc-600">
            <el-icon class="text-base">
              <component :is="item.icon" />
            </el-icon>
          </span>
          <div>
            <p class="text-sm font-semibold text-zinc-800">{{ item.label }}</p>
            <p class="text-xs text-zinc-500">{{ item.description }}</p>
          </div>
        </div>
        <span
          class="h-2.5 w-2.5 rounded-full"
          :class="selectedFormat === item.value ? 'bg-zinc-950' : 'bg-zinc-200'"
        ></span>
      </button>
    </div>

    <template #footer-start>
      <AppDialogButton @click="closeDialog">取消</AppDialogButton>
    </template>
    <template #footer-end>
      <AppDialogButton variant="primary" @click="confirmExport">导出</AppDialogButton>
    </template>
  </AppDialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Document, Tickets, Grid } from '@element-plus/icons-vue'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

export type ExportFormat = 'json' | 'md' | 'word' | 'excel'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'export', value: ExportFormat): void
}>()

const selectedFormat = ref<ExportFormat>('json')

const formats = computed(() => [
  { value: 'json' as const, label: 'JSON', description: '结构化数据，便于二次处理', icon: Document },
  { value: 'md' as const, label: 'Markdown', description: '文档格式，便于阅读分享', icon: Tickets },
  { value: 'word' as const, label: 'Word', description: '测试报告，适合评审归档', icon: Document },
  { value: 'excel' as const, label: 'Excel', description: '表格格式，适合统计', icon: Grid }
])

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      selectedFormat.value = 'json'
    }
  }
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const confirmExport = () => {
  emit('export', selectedFormat.value)
  emit('update:modelValue', false)
}
</script>
