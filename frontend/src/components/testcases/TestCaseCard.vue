<template>
  <EntityCard
    :title="testcase.title"
    :identifier="testcase.code"
    :disabled="disabled"
    @select="emit('select')"
  >
    <template #badges>
      <span class="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
        {{ testcase.type }}
      </span>
      <span class="rounded-full bg-sky-50 px-2 py-0.5 font-medium text-sky-700">
        {{ testcase.scenario_type }}
      </span>
      <span
        v-if="testcase.priority"
        class="rounded-full bg-slate-100 px-2 py-0.5 font-semibold text-slate-600"
      >
        {{ testcase.priority }}
      </span>
    </template>
  </EntityCard>
</template>

<script setup lang="ts">
import type { RequirementTestCaseItem } from '../../data/testcase'
import EntityCard from '../entity/EntityCard.vue'

withDefaults(defineProps<{
  testcase: RequirementTestCaseItem
  disabled?: boolean
}>(), {
  disabled: false
})

const emit = defineEmits<{
  (event: 'select'): void
}>()
</script>
