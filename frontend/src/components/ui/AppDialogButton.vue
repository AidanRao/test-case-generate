<template>
  <button
    :type="type"
    :disabled="disabled"
    class="inline-flex min-h-9 items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium leading-none transition focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:border-zinc-200 disabled:bg-zinc-100 disabled:text-zinc-400 disabled:shadow-none disabled:hover:border-zinc-200 disabled:hover:bg-zinc-100 disabled:hover:text-zinc-400"
    :class="variantClasses"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type AppDialogButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'

const props = withDefaults(
  defineProps<{
    variant?: AppDialogButtonVariant
    disabled?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'secondary',
    disabled: false,
    type: 'button'
  }
)

const variantClasses = computed(() => {
  const variants: Record<AppDialogButtonVariant, string> = {
    primary: 'border-zinc-950 bg-zinc-950 text-white shadow-sm hover:border-zinc-800 hover:bg-zinc-800',
    secondary: 'border-zinc-200 bg-white text-zinc-800 shadow-sm hover:border-zinc-300 hover:bg-zinc-50',
    danger: 'border-red-600 bg-red-600 text-white shadow-sm hover:border-red-700 hover:bg-red-700',
    ghost: 'border-transparent bg-transparent text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950'
  }
  return variants[props.variant]
})
</script>
