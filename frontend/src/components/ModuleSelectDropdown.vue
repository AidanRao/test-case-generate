<template>
  <div ref="selectContainer" class="min-w-0" style="width: min(22rem, 100%);">
    <p class="text-xs font-medium text-sky-600">{{ projectName }}</p>
    <div class="module-select mt-1" @click.stop="toggleDropdown">
      <div class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 shadow-sm">
        <span class="min-w-0 flex-1 truncate text-lg font-semibold text-slate-800">{{ modelValue }}</span>
        <div class="flex flex-col items-center gap-0.5 text-slate-400">
          <el-icon class="text-xs"><ArrowUp /></el-icon>
          <el-icon class="text-xs"><ArrowDown /></el-icon>
        </div>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div
      v-if="dropdownVisible"
      class="fixed inset-0 z-50"
      @click="closeDropdown"
    >
      <div class="absolute inset-0 bg-black/20"></div>
      <div
        class="absolute z-50 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl"
        :style="{
          top: dropdownPosition.top + 'px',
          left: dropdownPosition.left + 'px',
          width: Math.min(dropdownPosition.width, 560) + 'px'
        }"
        @click.stop
      >
        <div class="flex items-center border-b border-slate-100 px-4 py-3">
          <div class="relative flex-1">
            <el-icon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400">
              <Search />
            </el-icon>
            <input
              ref="searchInput"
              v-model="searchQuery"
              type="text"
              placeholder="Find Module..."
              class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-10 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
              @keydown.esc="closeDropdown"
            />
          </div>
          <button
            class="ml-2 rounded-lg px-2 py-1 text-xs font-medium text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            type="button"
            @click.stop="closeDropdown"
          >
            Esc
          </button>
        </div>

        <div class="max-h-64 overflow-y-auto">
          <button
            v-for="module in filteredModules"
            :key="module"
            class="group flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-slate-50"
            type="button"
            @click.stop="selectModule(module)"
          >
            <span class="min-w-0 flex-1 truncate text-sm font-medium text-slate-700">{{ module }}</span>
            <span v-if="module === modelValue" class="ml-3 flex h-4 w-4 items-center justify-center text-sky-600">
              <el-icon class="h-4 w-4 group-hover:hidden">
                <Check />
              </el-icon>
              <el-icon class="hidden h-4 w-4 group-hover:block">
                <Close />
              </el-icon>
            </span>
          </button>
          <div v-if="filteredModules.length === 0" class="px-4 py-8 text-center text-sm text-slate-400">
            未找到匹配的模块
          </div>
        </div>

        <div v-if="canCreate" class="border-t border-slate-100">
          <button
            class="flex w-full items-center gap-3 px-4 py-3.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            type="button"
            @click.stop="openCreateModule"
          >
            <el-icon class="h-4 w-4"><Plus /></el-icon>
            新增模块
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ArrowDown, ArrowUp, Check, Close, Plus, Search } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
  projectName: string
  modules: string[]
  canCreate: boolean
}>()

const emit = defineEmits<{
  (event: 'select', value: string): void
  (event: 'create'): void
}>()

const dropdownVisible = ref(false)
const searchQuery = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const selectContainer = ref<HTMLElement | null>(null)
const dropdownPosition = ref({ top: 0, left: 0, width: 0 })

const filteredModules = computed(() => {
  if (!searchQuery.value) {
    return props.modules
  }
  const query = searchQuery.value.toLowerCase()
  return props.modules.filter((module) => module.toLowerCase().includes(query))
})

const updateDropdownPosition = () => {
  if (!selectContainer.value) {
    return
  }
  const rect = selectContainer.value.getBoundingClientRect()
  dropdownPosition.value = {
    top: rect.bottom + 8,
    left: rect.left,
    width: rect.width
  }
}

const openDropdown = async () => {
  updateDropdownPosition()
  dropdownVisible.value = true
  await nextTick()
  searchInput.value?.focus()
}

const closeDropdown = () => {
  dropdownVisible.value = false
  searchQuery.value = ''
}

const toggleDropdown = () => {
  if (dropdownVisible.value) {
    closeDropdown()
    return
  }
  openDropdown()
}

const selectModule = (nextModuleName: string) => {
  closeDropdown()
  if (nextModuleName && nextModuleName !== props.modelValue) {
    emit('select', nextModuleName)
  }
}

const openCreateModule = () => {
  closeDropdown()
  emit('create')
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && dropdownVisible.value) {
    closeDropdown()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', updateDropdownPosition)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', updateDropdownPosition)
})
</script>

<style scoped>
.module-select {
  width: min(22rem, 100%);
  cursor: pointer;
}
</style>
