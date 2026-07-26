<template>
  <div v-if="items.length" class="mt-1 flex flex-wrap items-center gap-1 pl-7 text-[11px]">
    <span class="text-zinc-400">测试用例证据：</span>
    <button
      v-for="item in items"
      :key="item.id"
      class="max-w-full truncate rounded bg-white/80 px-1.5 py-0.5 font-medium text-sky-600 ring-1 ring-inset ring-sky-100 transition hover:bg-sky-100 hover:text-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-300"
      type="button"
      :title="item.title"
      @click.stop="emit('open-testcase', item)"
    >
      {{ item.title || item.code || item.id }}
    </button>
  </div>
  <p v-else class="mt-1 pl-7 text-[11px] text-zinc-400">暂无测试用例证据</p>
</template>

<script setup lang="ts">
import type { TestcaseEvidence } from '../api/projects'

defineProps<{
  items: TestcaseEvidence[]
}>()

const emit = defineEmits<{
  (e: 'open-testcase', value: TestcaseEvidence): void
}>()
</script>
