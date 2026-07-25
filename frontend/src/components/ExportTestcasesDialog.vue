<template>
  <AppDialog
    :model-value="modelValue"
    title="导出测试用例"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="grid gap-3">
      <div
        v-for="item in formats"
        :key="item.value"
        class="overflow-hidden rounded-xl border transition"
        :class="selectedFormat === item.value
          ? 'border-zinc-950 bg-zinc-50 shadow-sm'
          : 'border-zinc-200 bg-white hover:border-zinc-300'"
      >
        <button
          type="button"
          class="flex w-full items-center justify-between px-4 py-3 text-left text-sm transition hover:bg-zinc-50"
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

        <div
          v-if="item.value === 'word' && selectedFormat === 'word'"
          class="border-t border-zinc-200 px-4 py-3"
        >
          <p v-if="wordTemplatesLoading" class="text-xs text-zinc-500">
            正在加载模板
          </p>
          <p v-else-if="wordTemplatesError" class="text-xs text-red-600">
            {{ wordTemplatesError }}
          </p>
          <p v-else-if="wordTemplates.length === 0" class="text-xs text-zinc-500">
            暂无可用模板
          </p>
          <template v-else>
            <button
              v-for="template in wordTemplates"
              :key="template.template_id"
              type="button"
              class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm"
              :class="selectedTemplateId === template.template_id
                ? 'bg-zinc-100 text-zinc-950'
                : 'text-zinc-600 hover:bg-zinc-50'"
              :aria-pressed="selectedTemplateId === template.template_id"
              @click="selectedTemplateId = template.template_id"
            >
              <span
                class="h-2.5 w-2.5 rounded-full"
                :class="selectedTemplateId === template.template_id
                  ? 'bg-zinc-950'
                  : 'bg-zinc-200'"
              ></span>
              {{ template.name }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <template #footer-start>
      <AppDialogButton @click="closeDialog">取消</AppDialogButton>
    </template>
    <template #footer-end>
      <AppDialogButton
        variant="primary"
        :disabled="wordExportDisabled"
        @click="confirmExport"
      >
        导出
      </AppDialogButton>
    </template>
  </AppDialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Document, Tickets, Grid } from '@element-plus/icons-vue'
import type { WordReportTemplate } from '../api/projects'
import {
  buildExportSelection,
  selectInitialTemplateId,
  type ExportFormat,
  type ExportSelection
} from '../composables/wordTemplateSelection'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

const props = defineProps<{
  modelValue: boolean
  wordTemplates: WordReportTemplate[]
  wordTemplatesLoading: boolean
  wordTemplatesError: string
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'export', value: ExportSelection): void
}>()

const selectedFormat = ref<ExportFormat>('json')
const selectedTemplateId = ref('')

const formats = computed(() => [
  { value: 'json' as const, label: 'JSON', description: '结构化数据，便于二次处理', icon: Document },
  { value: 'md' as const, label: 'Markdown', description: '文档格式，便于阅读分享', icon: Tickets },
  { value: 'word' as const, label: 'Word', description: '测试报告，适合评审归档', icon: Document },
  { value: 'excel' as const, label: 'Excel', description: '表格格式，适合统计', icon: Grid }
])

const wordExportDisabled = computed(
  () => selectedFormat.value === 'word' && (
    props.wordTemplatesLoading
    || Boolean(props.wordTemplatesError)
    || !selectedTemplateId.value
  )
)

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      selectedFormat.value = 'json'
      selectedTemplateId.value = selectInitialTemplateId(
        props.wordTemplates,
        selectedTemplateId.value
      )
    }
  }
)

watch(
  () => props.wordTemplates,
  (templates) => {
    selectedTemplateId.value = selectInitialTemplateId(
      templates,
      selectedTemplateId.value
    )
  }
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const confirmExport = () => {
  const selection = buildExportSelection(
    selectedFormat.value,
    selectedTemplateId.value
  )
  if (!selection) {
    return
  }
  emit('export', selection)
  emit('update:modelValue', false)
}
</script>
