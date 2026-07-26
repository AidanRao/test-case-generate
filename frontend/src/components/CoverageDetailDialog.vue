<template>
  <AppDialog
    :model-value="modelValue"
    title="覆盖率明细"
    description="按模块或需求查看覆盖项与测试用例证据"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template v-if="canCalculateCoverage" #header-actions>
      <AppDialogButton
        class="!min-h-7 !px-3 !py-1 text-xs"
        :disabled="coverageCalculating"
        @click="emit('calculate-coverage')"
      >
        <svg
          v-if="coverageCalculating"
          class="mr-1.5 h-3 w-3 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle class="opacity-25" cx="12" cy="12" r="9" stroke="currentColor" stroke-width="3" />
          <path class="opacity-75" d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
        </svg>
        {{ calculationButtonText }}
      </AppDialogButton>
    </template>

    <div class="mb-4 flex rounded-xl bg-zinc-100 p-1" role="tablist" aria-label="覆盖率类型">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition"
        :class="activeTab === tab.value
          ? 'bg-white text-zinc-900 shadow-sm'
          : 'text-zinc-500 hover:text-zinc-700'"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab.value"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="activeTab === 'requirement'" class="overflow-hidden rounded-xl border border-zinc-200">
      <div class="grid grid-cols-[1fr_auto] items-center gap-2 bg-zinc-50 px-4 py-3 text-xs font-semibold text-zinc-500">
        <span>一级需求（模块）</span>
        <span class="text-right">覆盖情况</span>
      </div>
      <div class="divide-y divide-zinc-100">
        <div v-for="module in coverageDetail" :key="module.moduleId" class="px-4">
          <button
            class="flex w-full items-center justify-between py-3 text-left text-sm text-zinc-700 transition hover:text-zinc-950"
            type="button"
            @click="toggleExpanded(`requirement:${module.moduleId}`)"
          >
            <span class="font-semibold">{{ module.moduleTitle }}</span>
            <span class="text-xs font-semibold text-zinc-500">
              {{ module.coveredCount }}/{{ module.totalCount }}
            </span>
          </button>
          <div v-if="isExpanded(`requirement:${module.moduleId}`)" class="space-y-1 pb-3 text-xs">
            <button
              v-for="item in module.items"
              :key="item.id"
              class="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left transition"
              :class="item.covered ? 'bg-emerald-50/70 text-emerald-700' : 'bg-rose-50/70 text-rose-700'"
              type="button"
              @click="openRequirement(item)"
            >
              <span class="flex min-w-0 items-center gap-2">
                <StatusDot :covered="item.covered" />
                <span class="truncate">{{ item.title }}</span>
              </span>
              <span class="text-[11px] font-semibold">
                {{ item.covered ? `已覆盖 (${item.testcaseCount})` : '未覆盖' }}
              </span>
            </button>
            <div v-if="module.items.length === 0" class="px-2 py-2 text-zinc-400">暂无二级需求</div>
          </div>
        </div>
        <div v-if="coverageDetail.length === 0" class="px-4 py-8 text-center text-sm text-zinc-400">
          暂无需求覆盖数据
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'feature'" class="overflow-hidden rounded-xl border border-zinc-200">
      <CoverageDialogHeader label="需求" :metric="coverageAnalysis?.feature_point_coverage" />
      <div class="divide-y divide-zinc-100">
        <div v-for="detail in featureDetails" :key="detail.requirement_id" class="px-4">
          <button
            class="flex w-full items-center justify-between gap-4 py-3 text-left text-sm text-zinc-700 transition hover:text-zinc-950"
            type="button"
            @click="toggleExpanded(`feature:${detail.requirement_id}`)"
          >
            <RequirementTitle :detail="detail" />
            <span class="shrink-0 text-xs font-semibold text-zinc-500">
              {{ detail.coverage.covered }}/{{ detail.coverage.total }}
            </span>
          </button>
          <div v-if="isExpanded(`feature:${detail.requirement_id}`)" class="space-y-1 pb-3">
            <div
              v-for="point in detail.points"
              :key="point.name"
              class="rounded-lg px-3 py-2"
              :class="point.covered ? 'bg-sky-50/80' : 'bg-rose-50/70'"
            >
              <div class="flex items-center justify-between gap-3 text-xs">
                <span class="flex min-w-0 items-center gap-2 font-medium" :class="point.covered ? 'text-sky-700' : 'text-rose-700'">
                  <StatusDot :covered="point.covered" />
                  <span>{{ point.name }}</span>
                </span>
                <span class="shrink-0 text-[11px] font-semibold" :class="point.covered ? 'text-sky-600' : 'text-rose-600'">
                  {{ point.covered ? '已覆盖' : '未覆盖' }}
                </span>
              </div>
              <TestcaseEvidenceList
                :items="point.evidence_testcases"
                @open-testcase="openEvidenceTestcase"
              />
            </div>
            <div v-if="detail.points.length === 0" class="px-2 py-3 text-xs text-zinc-400">
              该需求未识别到功能点
            </div>
          </div>
        </div>
        <div v-if="featureDetails.length === 0" class="px-4 py-8 text-center text-sm text-zinc-400">
          尚未生成可展示的功能点明细
        </div>
      </div>
    </div>

    <div v-else class="overflow-hidden rounded-xl border border-zinc-200">
      <CoverageDialogHeader label="含接口的需求" :metric="coverageAnalysis?.interface_coverage" />
      <div class="divide-y divide-zinc-100">
        <div v-for="detail in interfaceDetails" :key="detail.requirement_id" class="px-4">
          <button
            class="flex w-full items-center justify-between gap-4 py-3 text-left text-sm text-zinc-700 transition hover:text-zinc-950"
            type="button"
            @click="toggleExpanded(`interface:${detail.requirement_id}`)"
          >
            <RequirementTitle :detail="detail" />
            <span class="shrink-0 text-xs font-semibold text-zinc-500">
              {{ detail.coverage.covered }}/{{ detail.coverage.total }}
            </span>
          </button>
          <div v-if="isExpanded(`interface:${detail.requirement_id}`)" class="space-y-2 pb-3">
            <div
              v-for="interfaceItem in detail.interfaces"
              :key="interfaceItem.interface_name"
              class="overflow-hidden rounded-lg border border-violet-100"
            >
              <div class="flex items-center justify-between bg-violet-50/70 px-3 py-2 text-xs font-semibold text-violet-700">
                <span>{{ interfaceItem.interface_name || '未命名接口' }}</span>
                <span>{{ interfaceItem.coverage.covered }}/{{ interfaceItem.coverage.total }}</span>
              </div>
              <div class="divide-y divide-violet-50">
                <div
                  v-for="parameter in interfaceItem.parameters"
                  :key="parameter.name"
                  class="px-3 py-2 text-xs"
                >
                  <div class="flex items-center justify-between gap-3">
                    <span class="flex min-w-0 items-center gap-2 font-medium" :class="parameter.covered ? 'text-violet-700' : 'text-rose-700'">
                      <StatusDot :covered="parameter.covered" />
                      <span>{{ parameter.name }}</span>
                    </span>
                    <span class="shrink-0 text-[11px] text-zinc-500">
                      {{ parameter.tested_conditions.length ? parameter.tested_conditions.join('、') : '未测试合法/非法/边界值' }}
                    </span>
                  </div>
                  <TestcaseEvidenceList
                    :items="parameter.evidence_testcases"
                    @open-testcase="openEvidenceTestcase"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="interfaceDetails.length === 0" class="px-4 py-10 text-center">
          <p class="text-sm font-medium text-zinc-500">未识别到接口或接口参数</p>
          <p class="mt-1 text-xs text-zinc-400">当前项目需求中暂无可统计的接口覆盖项</p>
        </div>
      </div>
    </div>
  </AppDialog>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, ref, watch, type PropType } from 'vue'
import type {
  CoverageAnalysisResponse,
  CoverageCalculationStatus,
  CoverageMetric,
  FeaturePointCoverageDetail,
  InterfaceCoverageDetail,
  TestcaseEvidence
} from '../api/projects'
import TestcaseEvidenceList from './TestcaseEvidenceList.vue'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

type CoverageTab = 'requirement' | 'feature' | 'interface'

type CoverageDetailItem = {
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
}

type CoverageDetail = {
  moduleId: string
  moduleTitle: string
  coveredCount: number
  totalCount: number
  items: CoverageDetailItem[]
}

type RequirementIdentity = Pick<
  FeaturePointCoverageDetail,
  'requirement_code' | 'requirement_title' | 'module'
>

const StatusDot = defineComponent({
  props: { covered: { type: Boolean, required: true } },
  setup: (props) => () => h(
    'span',
    {
      class: [
        'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold',
        props.covered
          ? 'bg-emerald-100 text-emerald-600'
          : 'bg-rose-100 text-rose-600'
      ]
    },
    props.covered ? '✓' : '!'
  )
})

const RequirementTitle = defineComponent({
  props: {
    detail: {
      type: Object as PropType<RequirementIdentity>,
      required: true
    }
  },
  setup: (props) => () => h('div', { class: 'min-w-0' }, [
    h('p', { class: 'truncate font-semibold' }, props.detail.requirement_title || '未命名需求'),
    h(
      'p',
      { class: 'mt-0.5 truncate text-[11px] font-normal text-zinc-400' },
      [props.detail.module, props.detail.requirement_code].filter(Boolean).join(' · ')
    )
  ])
})

const CoverageDialogHeader = defineComponent({
  props: {
    label: { type: String, required: true },
    metric: { type: Object as PropType<CoverageMetric | undefined>, default: undefined }
  },
  setup: (props) => () => h(
    'div',
    { class: 'grid grid-cols-[1fr_auto] items-center gap-2 bg-zinc-50 px-4 py-3 text-xs font-semibold text-zinc-500' },
    [
      h('span', props.label),
      h('span', { class: 'text-right' }, `项目汇总 ${props.metric?.covered ?? 0}/${props.metric?.total ?? 0}`)
    ]
  )
})

const props = defineProps<{
  modelValue: boolean
  initialTab: CoverageTab
  coverageDetail: CoverageDetail[]
  coverageAnalysis?: CoverageAnalysisResponse | null
  coverageCalculating?: boolean
  coverageCalculationStatus?: CoverageCalculationStatus | null
  canCalculateCoverage?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'calculate-coverage'): void
  (e: 'open-requirement', value: CoverageDetailItem['requirement']): void
  (e: 'open-testcase', value: TestcaseEvidence): void
}>()

const tabs: Array<{ value: CoverageTab; label: string }> = [
  { value: 'requirement', label: '需求覆盖率' },
  { value: 'feature', label: '功能点覆盖率' },
  { value: 'interface', label: '接口覆盖率' }
]

const activeTab = ref<CoverageTab>(props.initialTab)
const expandedItems = ref<string[]>([])
const featureDetails = computed(() => props.coverageAnalysis?.feature_point_details ?? [])
const calculationButtonText = computed(() => {
  if (!props.coverageCalculating) {
    return props.coverageAnalysis ? '重新计算' : '计算覆盖率'
  }
  const completed = props.coverageCalculationStatus?.completed_count ?? 0
  const total = props.coverageCalculationStatus?.total_count ?? 0
  return total > 0 ? `计算中 ${completed}/${total}` : '计算中'
})
const interfaceDetails = computed<InterfaceCoverageDetail[]>(() =>
  (props.coverageAnalysis?.interface_details ?? []).filter((item) => item.interfaces.length > 0)
)

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      activeTab.value = props.initialTab
    } else {
      expandedItems.value = []
    }
  }
)

const isExpanded = (id: string) => expandedItems.value.includes(id)
const toggleExpanded = (id: string) => {
  expandedItems.value = isExpanded(id)
    ? expandedItems.value.filter((item) => item !== id)
    : [...expandedItems.value, id]
}

const openRequirement = (item: CoverageDetailItem) => {
  emit('open-requirement', item.requirement)
}

const openEvidenceTestcase = (testcase: TestcaseEvidence) => {
  emit('open-testcase', testcase)
}
</script>
