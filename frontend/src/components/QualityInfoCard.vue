<template>
  <div class="shrink-0 rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
      <h2 class="text-base font-semibold text-slate-800">质量信息</h2>
      <GenerationStatusBadge
        v-if="generationStatus"
        class="px-3 py-1"
        :active="generationStatus.active"
        :label="statusText"
        :tone="statusTone"
      />
    </div>
    <div class="flex gap-6 p-5">
      <div class="flex-1 space-y-3">
        <div class="flex justify-between text-sm">
          <span class="text-slate-500">迭代次数</span>
          <span class="font-medium text-slate-700">{{ data.iterations }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-slate-500">耗时</span>
          <span class="font-medium text-slate-700">{{ durationText }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-slate-500">成功处理需求数</span>
          <span class="font-semibold text-emerald-600">{{ data.success_count }}</span>
        </div>
        <div v-if="data.fail_count > 0" class="flex justify-between text-sm">
          <span class="text-slate-500">失败处理需求数</span>
          <span class="font-semibold text-rose-600">{{ data.fail_count }}</span>
        </div>
        <button class="w-full border-t border-slate-100 pt-3 text-left" type="button" @click="openCoverageDialog">
          <div class="flex w-full items-center justify-between gap-2 text-xs font-semibold text-slate-600">
            <span>覆盖率分析</span>
            <span class="text-slate-500">{{ coverageText }}</span>
          </div>
          <div class="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div class="h-full rounded-full bg-emerald-500 transition-all" :style="{ width: coveragePercent }"></div>
          </div>
          <div class="mt-2 flex items-center justify-between text-xs text-slate-500">
            <span>已覆盖 {{ coverage.covered }}</span>
            <span>总需求 {{ coverage.total }}</span>
          </div>
        </button>
      </div>
      <div class="w-px bg-slate-100"></div>
      <div class="flex-1 space-y-2">
        <div class="grid grid-cols-[1fr_auto] items-center gap-2 text-xs font-medium text-slate-400">
          <span>测试用例类型统计</span>
          <span class="whitespace-nowrap text-right">共{{ totalCount }}</span>
        </div>
        <div class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <div
            v-for="item in typeStats"
            :key="item.type"
            class="grid grid-cols-[1fr_auto] items-center gap-2 px-2.5 py-1 text-xs"
          >
            <span class="text-slate-600">{{ item.type }}</span>
            <span class="text-right font-medium text-slate-700">{{ item.count }}</span>
          </div>
          <div
            v-if="typeStats.length === 0"
            class="px-2.5 py-1 text-xs text-slate-500"
          >
            暂无数据
          </div>
        </div>
      </div>
    </div>
  </div>

  <CoverageDetailDialog
    v-model="dialogVisible"
    :coverage-detail="coverageDetail"
    @open-requirement="openRequirement"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import CoverageDetailDialog from './CoverageDetailDialog.vue'
import GenerationStatusBadge from './generation/GenerationStatusBadge.vue'

type QualityInfo = {
  success_count: number
  fail_count: number
  iterations: number
  duration: number
  req_type_stats: Record<string, number>
}

type CoverageInfo = {
  total: number
  covered: number
  rate: number
}

const props = defineProps<{
  data: QualityInfo
  coverage: CoverageInfo
  coverageDetail: {
    moduleId: string
    moduleTitle: string
    coveredCount: number
    totalCount: number
    items: {
      id: string
      title: string
      covered: boolean
      testcaseCount: number
      requirement: {
        ID?: string
        code?: string
        title: string
        type: string
        module: string
        content: string
      }
    }[]
  }[]
  generationStatus?: {
    status: 'idle' | 'pending' | 'running' | 'completed' | 'failed'
    active: boolean
    completed_count: number
    total_count: number
  } | null
}>()

const emit = defineEmits<{
  (e: 'open-requirement', value: { ID?: string; code?: string; title: string; type: string; module: string; content: string }): void
}>()

const durationText = computed(() => {
  const value = props.data?.duration ?? 0
  const text = Number.isInteger(value) ? value.toString() : value.toFixed(1)
  return `${text}s`
})

const typeStats = computed(() => {
  const stats = props.data?.req_type_stats ?? {}
  return Object.entries(stats).map(([type, count]) => ({ type, count }))
})

const totalCount = computed(() => {
  return typeStats.value.reduce((sum, item) => sum + item.count, 0)
})

const coverageRate = computed(() => {
  const value = Number.isFinite(props.coverage?.rate) ? props.coverage.rate : 0
  return Math.min(1, Math.max(0, value))
})

const coveragePercent = computed(() => `${(coverageRate.value * 100).toFixed(0)}%`)

const coverageText = computed(() => `${coveragePercent.value} 覆盖`)

const statusText = computed(() => {
  if (!props.generationStatus) return ''
  if (props.generationStatus.status === 'pending') return '测试用例等待生成'
  if (props.generationStatus.status === 'running') {
    return `测试用例生成中 ${props.generationStatus.completed_count}/${props.generationStatus.total_count}`
  }
  if (props.generationStatus.status === 'completed') return '测试用例生成完成'
  if (props.generationStatus.status === 'failed') return '测试用例生成失败'
  return '暂无生成任务'
})

const statusTone = computed<'warning' | 'success' | 'danger' | 'neutral'>(() => {
  if (!props.generationStatus) return 'neutral'
  if (props.generationStatus.active) return 'warning'
  if (props.generationStatus.status === 'completed') return 'success'
  if (props.generationStatus.status === 'failed') return 'danger'
  return 'neutral'
})

const dialogVisible = ref(false)
const openCoverageDialog = () => {
  dialogVisible.value = true
}

const openRequirement = (requirement: {
  ID?: string
  code?: string
  title: string
  type: string
  module: string
  content: string
}) => {
  emit('open-requirement', requirement)
}
</script>
