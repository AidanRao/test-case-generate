<template>
  <div class="shrink-0 rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3.5">
      <h2 class="text-base font-semibold text-slate-800">质量信息</h2>
      <GenerationStatusBadge
        v-if="generationStatus"
        class="px-3 py-1"
        :active="generationStatus.active"
        :label="statusText"
        :tone="statusTone"
      />
    </div>
    <div class="flex gap-4 p-4">
      <div class="min-w-0 flex-1 space-y-1.5">
        <div class="flex justify-between text-xs leading-4">
          <span class="text-slate-500">迭代次数</span>
          <span class="font-medium text-slate-700">{{ data.iterations }}</span>
        </div>
        <div class="flex justify-between text-xs leading-4">
          <span class="text-slate-500">耗时</span>
          <span class="font-medium text-slate-700">{{ durationText }}</span>
        </div>
        <div class="flex justify-between text-xs leading-4">
          <span class="text-slate-500">成功处理需求数</span>
          <span class="font-semibold text-emerald-600">{{ data.success_count }}</span>
        </div>
        <div v-if="data.fail_count > 0" class="flex justify-between text-xs leading-4">
          <span class="text-slate-500">失败处理需求数</span>
          <span class="font-semibold text-rose-600">{{ data.fail_count }}</span>
        </div>
        <div class="border-t border-slate-100 pt-2.5">
          <div class="flex items-center gap-1.5">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-semibold text-slate-600">覆盖率分析</span>
              <div v-if="coverageAnalysis" class="group relative">
                <button
                  class="flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] font-bold text-slate-400 transition hover:border-sky-300 hover:text-sky-500 focus:border-sky-300 focus:text-sky-500 focus:outline-none"
                  type="button"
                  aria-label="查看 AI 覆盖率分析信息"
                >
                  ?
                </button>
                <div
                  class="invisible absolute left-1/2 top-full z-30 mt-2 w-52 -translate-x-1/2 rounded-lg bg-slate-800 px-3 py-2 text-[11px] font-normal leading-5 text-white opacity-0 shadow-lg transition group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100"
                  role="tooltip"
                >
                  <p>AI 分析于 {{ calculatedAtText }}</p>
                  <p v-if="coverageAnalysis.model" class="text-slate-300">模型：{{ coverageAnalysis.model }}</p>
                  <p class="text-slate-300">耗时：{{ analysisDurationText }}</p>
                </div>
              </div>
            </div>
          </div>

          <button class="mt-2.5 w-full rounded-lg text-left focus:outline-none focus:ring-2 focus:ring-emerald-100" type="button" @click="openCoverageDialog('requirement')">
            <CoverageProgress
              label="需求覆盖率"
              :metric="coverage"
              color-class="bg-emerald-500"
              total-label="总需求"
            />
          </button>

          <div v-if="coverageAnalysis" class="mt-3 space-y-3">
            <button class="w-full rounded-lg text-left focus:outline-none focus:ring-2 focus:ring-sky-100" type="button" @click="openCoverageDialog('feature')">
              <CoverageProgress
                label="功能点覆盖率"
                :metric="coverageAnalysis.feature_point_coverage"
                color-class="bg-sky-500"
                total-label="总功能点"
              />
            </button>
            <button class="w-full rounded-lg text-left focus:outline-none focus:ring-2 focus:ring-violet-100" type="button" @click="openCoverageDialog('interface')">
              <CoverageProgress
                label="接口覆盖率"
                :metric="coverageAnalysis.interface_coverage"
                color-class="bg-violet-500"
                total-label="总参数"
              />
            </button>
          </div>
        </div>
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
    :initial-tab="dialogInitialTab"
    :coverage-detail="coverageDetail"
    :coverage-analysis="coverageAnalysis"
    :coverage-calculating="coverageCalculating"
    :coverage-calculation-status="coverageCalculationStatus"
    :can-calculate-coverage="canCalculateCoverage"
    @calculate-coverage="emit('calculate-coverage')"
    @open-requirement="openRequirement"
    @open-testcase="emit('open-testcase', $event)"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import CoverageDetailDialog from './CoverageDetailDialog.vue'
import CoverageProgress from './CoverageProgress.vue'
import GenerationStatusBadge from './generation/GenerationStatusBadge.vue'
import type {
  CoverageAnalysisResponse,
  CoverageCalculationStatus,
  TestcaseEvidence
} from '../api/projects'

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
  coverageAnalysis?: CoverageAnalysisResponse | null
  coverageCalculating?: boolean
  coverageCalculationStatus?: CoverageCalculationStatus | null
  canCalculateCoverage?: boolean
}>()

const emit = defineEmits<{
  (e: 'open-requirement', value: { ID?: string; code?: string; title: string; type: string; module: string; content: string }): void
  (e: 'open-testcase', value: TestcaseEvidence): void
  (e: 'calculate-coverage'): void
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

const calculatedAtText = computed(() => {
  const value = props.coverageAnalysis?.calculated_at
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN', { hour12: false })
})

const analysisDurationText = computed(() => {
  const value = props.coverageAnalysis?.duration ?? 0
  return `${Number.isInteger(value) ? value : value.toFixed(1)}s`
})

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
type CoverageTab = 'requirement' | 'feature' | 'interface'
const dialogInitialTab = ref<CoverageTab>('requirement')
const openCoverageDialog = (tab: CoverageTab) => {
  dialogInitialTab.value = tab
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
