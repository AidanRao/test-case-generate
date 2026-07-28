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
      <GenerationStatusBadge
        v-if="generationState === 'processing'"
        active
        label="生成中"
      />
      <GenerationStatusBadge
        v-else-if="generationState === 'waiting'"
        label="等待中"
      />
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
  generationState?: 'processing' | 'waiting'
  selected?: boolean
}>(), {
  testcaseCount: 0,
  selected: false
})

const emit = defineEmits<{
  (event: 'select'): void
}>()
</script>
