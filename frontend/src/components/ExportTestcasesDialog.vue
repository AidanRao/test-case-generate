<template>
  <el-dialog
    :model-value="modelValue"
    width="520px"
    align-center
    title="导出测试用例"
    @close="closeDialog"
  >
    <div class="space-y-4">
      <div class="grid gap-3">
        <button
          v-for="item in formats"
          :key="item.value"
          type="button"
          class="flex w-full items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left text-sm transition hover:border-slate-300 hover:bg-slate-50"
          :class="selectedFormat === item.value ? 'border-sky-400 bg-sky-50/60' : ''"
          @click="selectedFormat = item.value"
        >
          <div class="flex items-center gap-3">
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500">
              <el-icon class="text-base">
                <component :is="item.icon" />
              </el-icon>
            </span>
            <div>
              <p class="text-sm font-semibold text-slate-700">{{ item.label }}</p>
              <p class="text-xs text-slate-500">{{ item.description }}</p>
            </div>
          </div>
          <span
            class="h-2.5 w-2.5 rounded-full"
            :class="selectedFormat === item.value ? 'bg-sky-600' : 'bg-slate-200'"
          ></span>
        </button>
      </div>
      <div class="flex justify-end gap-2 pt-2">
        <button
          class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700"
          type="button"
          @click="closeDialog"
        >
          取消
        </button>
        <button
          class="rounded-full bg-sky-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-sky-700"
          type="button"
          @click="confirmExport"
        >
          导出
        </button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Document, Tickets, Grid } from '@element-plus/icons-vue'

export type ExportFormat = 'json' | 'md' | 'excel'

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
