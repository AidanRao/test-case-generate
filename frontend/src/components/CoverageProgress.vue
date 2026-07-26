<template>
  <div>
    <div class="flex items-center justify-between gap-2 text-xs font-semibold leading-4 text-slate-600">
      <span>{{ label }}</span>
      <span class="text-slate-500">{{ percent }} 覆盖</span>
    </div>
    <div class="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
      <div
        class="h-full rounded-full transition-all"
        :class="colorClass"
        :style="{ width: percent }"
      ></div>
    </div>
    <div class="mt-1.5 flex items-center justify-between text-[11px] leading-4 text-slate-500">
      <span>已覆盖 {{ metric.covered }}</span>
      <span>{{ totalLabel }} {{ metric.total }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type CoverageMetric = {
  total: number
  covered: number
  rate: number
}

const props = defineProps<{
  label: string
  metric: CoverageMetric
  colorClass: string
  totalLabel: string
}>()

const percent = computed(() => {
  const rate = Number.isFinite(props.metric?.rate) ? props.metric.rate : 0
  return `${(Math.min(1, Math.max(0, rate)) * 100).toFixed(0)}%`
})
</script>
