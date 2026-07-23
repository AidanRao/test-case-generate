<template>
  <button
    type="button"
    class="group w-full rounded-xl border bg-white px-4 py-3 text-left transition"
    :class="cardClass"
    :disabled="disabled"
    :aria-current="selected ? 'true' : undefined"
    @click="emit('select')"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0 flex-1">
        <p
          class="truncate text-sm font-semibold transition"
          :class="selected ? 'text-sky-700' : 'text-slate-800 group-hover:text-sky-700'"
          :title="title"
        >
          {{ title }}
        </p>
        <slot name="content" />
      </div>
      <span
        v-if="identifier"
        class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600"
      >
        {{ identifier }}
      </span>
    </div>
    <div v-if="$slots.badges" class="mt-2 flex flex-wrap items-center gap-2 text-xs">
      <slot name="badges" />
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title: string
  identifier?: string
  selected?: boolean
  disabled?: boolean
}>(), {
  identifier: '',
  selected: false,
  disabled: false
})

const emit = defineEmits<{
  (event: 'select'): void
}>()

const cardClass = computed(() => {
  if (props.disabled) return 'cursor-not-allowed border-slate-100 bg-slate-50 opacity-60'
  if (props.selected) return 'border-sky-200 bg-sky-50/60 shadow-sm'
  return 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
})
</script>
