<template>
  <div class="flex-1 overflow-y-auto rounded-xl border border-slate-100">
    <div
      v-if="items.length === 0"
      class="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500"
    >
      暂无需求数据
    </div>
    <div v-else class="divide-y divide-slate-100">
      <button
        v-for="(item, index) in items"
        :key="index"
        class="group w-full px-4 py-3 text-left transition hover:bg-slate-50"
        :class="selectedIndex === index ? 'bg-sky-50/60' : ''"
        @click="selectItem(index)"
      >
        <div class="flex items-center justify-between gap-3">
          <p
            class="text-sm font-semibold text-slate-800 transition group-hover:text-sky-700"
            :class="selectedIndex === index ? 'text-sky-700' : ''"
          >
            {{ item.title }}
          </p>
          <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
            {{ getItemId(item, index) }}
          </span>
        </div>
        <div class="mt-2 flex items-center gap-2 text-xs text-slate-500">
          <span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600">
            {{ item.type }}
          </span>
          <span
            v-if="item.isGenerating"
            class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-700"
          >
            <span class="h-3 w-3 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600"></span>
            生成中
          </span>
          <span v-else class="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
            测试用例数 {{ item.testcaseCount ?? 0 }}
          </span>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface RequirementListItem {
  title: string
  type: string
  ID?: string
  code?: string
  testcaseCount?: number
  isGenerating?: boolean
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
