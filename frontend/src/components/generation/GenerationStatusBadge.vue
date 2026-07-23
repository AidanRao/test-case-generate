<template>
  <span
    class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
    :class="toneClass"
  >
    <span
      v-if="active"
      class="h-3 w-3 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600"
    ></span>
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  active?: boolean
  label?: string
  tone?: 'warning' | 'success' | 'danger' | 'neutral'
}>(), {
  active: false,
  label: '生成中',
  tone: 'neutral'
})

const toneClass = computed(() => {
  if (props.active || props.tone === 'warning') return 'bg-amber-50 text-amber-700'
  if (props.tone === 'success') return 'bg-emerald-50 text-emerald-700'
  if (props.tone === 'danger') return 'bg-rose-50 text-rose-700'
  return 'bg-slate-100 text-slate-600'
})
</script>
