<template>
  <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-6 py-4 text-sm text-slate-500">
    <span>
      共 {{ totalItems }} 条，当前显示 {{ displayStart }}-{{ displayEnd }} 条
    </span>
    <div class="flex items-center gap-2">
      <button
        class="rounded-full border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        :disabled="currentPage <= 1"
        @click="goPrev"
      >
        上一页
      </button>
      <span class="text-sm text-slate-500">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button
        class="rounded-full border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        :disabled="currentPage >= totalPages"
        @click="goNext"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  totalItems: number
  currentPage: number
  pageSize: number
}>()

const emit = defineEmits<{
  (e: 'update:currentPage', value: number): void
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalItems / props.pageSize)))

const displayStart = computed(() => {
  if (props.totalItems === 0) {
    return 0
  }
  return (props.currentPage - 1) * props.pageSize + 1
})

const displayEnd = computed(() => {
  if (props.totalItems === 0) {
    return 0
  }
  return Math.min(props.totalItems, (props.currentPage - 1) * props.pageSize + props.pageSize)
})

const goPrev = () => {
  emit('update:currentPage', Math.max(1, props.currentPage - 1))
}

const goNext = () => {
  emit('update:currentPage', Math.min(totalPages.value, props.currentPage + 1))
}
</script>
