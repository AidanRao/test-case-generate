<template>
  <EntityCard
    :title="requirement.title"
    :identifier="identifier"
    :selected="selected"
    @select="emit('select')"
  >
    <template #badges>
      <span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600">
        {{ requirement.type || '未分类' }}
      </span>
      <GenerationStatusBadge v-if="isGenerating" active />
      <span v-else class="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
        测试用例数 {{ testcaseCount }}
      </span>
    </template>
  </EntityCard>
</template>

<script setup lang="ts">
import EntityCard from '../entity/EntityCard.vue'
import GenerationStatusBadge from '../generation/GenerationStatusBadge.vue'

export type RequirementCardItem = {
  title: string
  type: string
  id?: string
  ID?: string
  code?: string
}

withDefaults(defineProps<{
  requirement: RequirementCardItem
  identifier: string
  testcaseCount?: number
  isGenerating?: boolean
  selected?: boolean
}>(), {
  testcaseCount: 0,
  isGenerating: false,
  selected: false
})

const emit = defineEmits<{
  (event: 'select'): void
}>()
</script>
