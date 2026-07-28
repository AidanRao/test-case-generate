<template>
  <div class="flex-1 overflow-y-auto rounded-xl border border-slate-100">
    <div
      v-if="items.length === 0"
      class="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500"
    >
      暂无需求数据
    </div>
    <div v-else class="space-y-2 p-2">
      <RequirementCard
        v-for="(item, index) in items"
        :key="item.id || item.ID || item.code || index"
        :requirement="item"
        :identifier="getItemId(item, index)"
        :testcase-count="item.testcaseCount"
        :generation-state="item.generationState"
        :selected="selectedIndex === index"
        @select="selectItem(index)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import RequirementCard from './requirements/RequirementCard.vue'

export interface RequirementListItem {
  title: string
  type: string
  id?: string
  ID?: string
  code?: string
  testcaseCount?: number
  generationState?: 'processing' | 'waiting'
}

const props = defineProps<{
  items: RequirementListItem[]
  selectedIndex: number
}>()

const emit = defineEmits<{
  (event: 'select', index: number): void
}>()

const getItemId = (item: { ID?: string; code?: string }, index: number) => {
  return item.code || `REQ-${String(index + 1).padStart(3, '0')}`
}

const selectItem = (index: number) => {
  emit('select', index)
}
</script>
