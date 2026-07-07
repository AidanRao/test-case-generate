<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
    @click.self="closeDialog"
  >
    <div class="w-full max-w-3xl rounded-2xl bg-white p-6 shadow-xl">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-slate-900">覆盖率明细</h3>
          <p class="mt-1 text-xs text-slate-500">点击模块行展开二级需求覆盖情况</p>
        </div>
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          type="button"
          @click="closeDialog"
        >
          ×
        </button>
      </div>
      <div class="mt-5 overflow-hidden rounded-xl border border-slate-200">
        <div class="grid grid-cols-[1fr_auto] items-center gap-2 bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-500">
          <span>一级需求（模块）</span>
          <span class="text-right">覆盖情况</span>
        </div>
        <div class="divide-y divide-slate-100">
          <div v-for="module in coverageDetail" :key="module.moduleId" class="px-4">
            <button
              class="flex w-full items-center justify-between py-3 text-left text-sm text-slate-700 transition hover:text-slate-900"
              type="button"
              @click="toggleModule(module.moduleId)"
            >
              <div class="flex items-center gap-2">
                <span class="font-semibold">{{ module.moduleTitle }}</span>
              </div>
              <span class="text-xs font-semibold text-slate-500">
                {{ module.coveredCount }}/{{ module.totalCount }}
              </span>
            </button>
            <div v-if="expandedModules.includes(module.moduleId)" class="pb-3 text-xs text-slate-500">
              <button
                v-for="item in module.items"
                :key="item.id"
                class="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left transition"
                :class="item.covered ? 'bg-emerald-50/60 text-emerald-700' : 'bg-rose-50/60 text-rose-700'"
                type="button"
                @click="openRequirement(item)"
              >
                <div class="flex min-w-0 items-center gap-2">
                  <span
                    class="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold"
                    :class="item.covered ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'"
                  >
                    {{ item.covered ? '✓' : '!' }}
                  </span>
                  <span class="truncate">{{ item.title }}</span>
                </div>
                <span class="text-[11px] font-semibold">
                  {{ item.covered ? `已覆盖 (${item.testcaseCount})` : '未覆盖' }}
                </span>
              </button>
              <div v-if="module.items.length === 0" class="px-2 py-2 text-slate-400">暂无二级需求</div>
            </div>
          </div>
          <div v-if="coverageDetail.length === 0" class="px-4 py-4 text-sm text-slate-400">暂无覆盖数据</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

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

const props = defineProps<{
  modelValue: boolean
  coverageDetail: CoverageDetail[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'open-requirement', value: CoverageDetailItem['requirement']): void
}>()

const expandedModules = ref<string[]>([])

watch(
  () => props.modelValue,
  (value) => {
    if (!value) {
      expandedModules.value = []
    }
  }
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const toggleModule = (moduleId: string) => {
  if (expandedModules.value.includes(moduleId)) {
    expandedModules.value = expandedModules.value.filter((id: string) => id !== moduleId)
    return
  }
  expandedModules.value = [...expandedModules.value, moduleId]
}

const openRequirement = (item: CoverageDetailItem) => {
  emit('open-requirement', item.requirement)
}
</script>
