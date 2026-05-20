<template>
  <div class="relative h-full w-full">
    <div ref="containerRef" class="h-full w-full"></div>
    <div class="absolute bottom-4 right-4 flex items-center gap-2 rounded-lg bg-white/90 px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm backdrop-blur-sm">
      <button
        class="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 text-slate-600 transition hover:bg-slate-100"
        @click="zoomOut"
      >
        -
      </button>
      <span class="min-w-[52px] text-center text-slate-700">{{ zoomPercent }}</span>
      <button
        class="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 text-slate-600 transition hover:bg-slate-100"
        @click="zoomIn"
      >
        +
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { Graph, type Cell } from '@antv/x6'
import Hierarchy from '@antv/hierarchy'
import type { Requirement } from '../data/projectStore'
import type { TestCaseDetailItem } from './TestCaseDetailDialog.vue'

export type BoardNode = {
  id: string
  type: 'root' | 'feature' | 'subfeature' | 'testcase'
  label: string
  width: number
  height: number
  children?: BoardNode[]
  requirement?: Requirement
  testcase?: TestCaseDetailItem
}

const props = defineProps<{
  data: BoardNode
}>()
const emit = defineEmits<{
  (event: 'open-requirement', requirement: Requirement): void
  (event: 'open-testcase', testcase: TestCaseDetailItem): void
  (event: 'create-requirement', module: string): void
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const zoomValue = ref(1)
const minScale = 0.4
const maxScale = 1.8
const zoomPercent = computed(() => `${Math.round(zoomValue.value * 100)}%`)
let graph: Graph | null = null

/**
 * 根据节点类型和标签返回节点样式属性
 * @param type - 节点类型
 * @param label - 节点标签
 */
const truncateLabel = (label: string, maxLength: number) => {
  if (label.length <= maxLength) {
    return label
  }
  return `${label.slice(0, Math.max(0, maxLength - 1))}…`
}

const getLabelLimit = (type: BoardNode['type']) => {
  if (type === 'root') return 10
  if (type === 'feature') return 12
  if (type === 'subfeature') return 16
  return 14
}

const getNodeAttrs = (type: BoardNode['type'], label: string) => {
  const displayLabel = truncateLabel(label, getLabelLimit(type))
  if (type === 'root') {
    return {
      body: { fill: '#0ea5e9', stroke: '#0284c7', rx: 6, ry: 6 },
      label: { text: displayLabel, fill: '#fff', fontSize: 24, fontWeight: 'bold' }
    }
  }
  if (type === 'feature') {
    return {
      body: { fill: '#10b981', stroke: '#059669', rx: 6, ry: 6 },
      label: { text: displayLabel, fill: '#fff', fontSize: 22, fontWeight: 'bold' }
    }
  }
  if (type === 'subfeature') {
    return {
      body: { fill: '#f59e0b', stroke: '#d97706', rx: 6, ry: 6 },
      label: { text: displayLabel, fill: '#fff', fontSize: 20, fontWeight: 'bold' }
    }
  }
  return {
    body: { fill: '#f8fafc', stroke: '#e2e8f0', rx: 6, ry: 6 },
    label: { text: displayLabel, fill: '#475569', fontSize: 18, fontWeight: 500 }
  }
}

/**
 * 渲染图形
 */
const renderGraph = () => {
  if (!graph) return

  // 1. 使用 @antv/hierarchy 进行 mindmap 布局
  const result = Hierarchy.mindmap(props.data, {
    direction: 'H',
    getHeight: (d: BoardNode) => d.height,
    getWidth: (d: BoardNode) => d.width,
    getHGap: () => 70,
    getVGap: () => 28,
    getSide: () => 'right'
  })

  const cells: Cell[] = []

  const scaleX = 1.25
  const scaleY = 1.25

  const traverse = (node: any) => {
    if (!node) return
    const { id, x, y, width, height, children, data } = node

    const resolvedLabel = data?.label ?? data?.name ?? '未命名'
    const resolvedType = data?.type ?? 'testcase'
    
    cells.push(graph!.createNode({
      id,
      shape: 'rect', // 显式指定形状
      x: x * scaleX,
      y: y * scaleY,
      width: width,
      height: height,
      label: resolvedLabel,
      data: {
        type: resolvedType,
        label: resolvedLabel,
        requirement: data?.requirement ?? null,
        testcase: data?.testcase ?? null
      },
      attrs: getNodeAttrs(resolvedType, resolvedLabel)
    }))

    if (children) {
      children.forEach((item: any) => {
        traverse(item)
        cells.push(graph!.createEdge({
          source: { cell: id, anchor: 'right' },
          target: { cell: item.id, anchor: 'left' },
          router: { name: 'normal' },
          connector: { name: 'smooth' },
          attrs: {
            line: {
              stroke: '#cbd5e1',
              strokeWidth: 1.5,
              targetMarker: {
                name: 'block',
                width: 10,
                height: 10
              }
            }
          }
        }))
      })
    }
  }

  traverse(result)

  graph.resetCells(cells)
  graph.centerContent()
  graph.zoomToFit({ maxScale: 1.2 })
  zoomValue.value = graph.zoom()
}

const initGraph = () => {
  if (!containerRef.value) return

  graph = new Graph({
    container: containerRef.value,
    autoResize: true,
    background: { color: '#ffffff' },
    grid: {
      size: 15,
      visible: true,
      type: 'dot',
      args: { color: '#f1f5f9', thickness: 1 }
    },
    panning: {
      enabled: true,
      eventTypes: ['leftMouseDown', 'mouseWheel']
    },
    mousewheel: {
      enabled: true,
      zoomAtMousePosition: true,
      factor: 1.1,
      minScale,
      maxScale,
    },
    connecting: {
      router: 'normal',
      connector: {
        name: 'rounded',
        args: { radius: 8 },
      },
      anchor: 'center',
      connectionPoint: 'boundary',
      allowBlank: false,
      snap: true,
    },
  })

  graph.on('scale', ({ sx }) => {
    zoomValue.value = sx
  })

  graph.on('node:click', ({ node }) => {
    const data = node.getData() as {
      type?: BoardNode['type']
      requirement?: Requirement | null
      testcase?: TestCaseDetailItem | null
      label?: string
    }
    if (data?.type === 'subfeature' && data.requirement) {
      emit('open-requirement', data.requirement)
      return
    }
    if (data?.type === 'testcase' && data.testcase) {
      emit('open-testcase', data.testcase)
      return
    }
    if (data?.type === 'feature') {
      // 点击一级需求（模块）时，触发新增需求事件
      emit('create-requirement', data.label || '')
    }
  })
}

const handleResize = () => {
  if (!graph || !containerRef.value) return
  graph.resize(containerRef.value.clientWidth, containerRef.value.clientHeight)
}

const clampZoom = (value: number) => Math.min(maxScale, Math.max(minScale, value))

const zoomIn = () => {
  if (!graph) return
  const next = clampZoom(graph.zoom() + 0.1)
  graph.zoomTo(next)
}

const zoomOut = () => {
  if (!graph) return
  const next = clampZoom(graph.zoom() - 0.1)
  graph.zoomTo(next)
}

onMounted(() => {
  initGraph()
  renderGraph()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  graph?.dispose()
  graph = null
})

watch(
  () => props.data,
  () => {
    if (graph) {
      renderGraph()
    }
  },
  { deep: true, immediate: true }
)
</script>
