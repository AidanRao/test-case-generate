<template>
  <el-dialog
    :model-value="modelValue"
    width="720px"
    align-center
    title="新增需求"
    @close="closeDialog"
  >
    <div class="space-y-6">
      <div class="grid gap-4 rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-sm">
        <div>
          <p class="text-xs font-medium text-slate-400">需求编号</p>
          <input
            v-model="formData.code"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            placeholder="请输入需求编号"
          />
        </div>
        <div>
          <p class="text-xs font-medium text-slate-400">需求标题</p>
          <input
            v-model="formData.title"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            placeholder="请输入需求标题"
          />
        </div>
        <div>
          <p class="text-xs font-medium text-slate-400">需求类型</p>
          <select
            v-model="formData.type"
            class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
          >
            <option value="功能需求">功能需求</option>
            <option value="可靠性需求">可靠性需求</option>
            <option value="安全性需求">安全性需求</option>
            <option value="强度需求">强度需求</option>
            <option value="性能需求">性能需求</option>  
            <option value="接口需求">接口需求</option>
            <option value="数据处理需求">数据处理需求</option>
            <option value="边界需求">边界需求</option>
            <option value="容量需求">容量需求</option>
            <option value="余量需求">余量需求</option>
          </select>
        </div>
        <div>
          <p class="text-xs font-medium text-slate-400">需求内容</p>
          <textarea
            v-model="formData.content"
            rows="4"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            placeholder="请输入需求内容"
          ></textarea>
        </div>
        <div>
          <p class="text-xs font-medium text-slate-400">所属模块</p>
          <input
            v-model="formData.module"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-sky-400 focus:outline-none"
            placeholder="请输入所属模块"
            readonly
          />
        </div>
      </div>
    </div>
    <template #footer>
      <div class="flex items-center gap-3">
        <button
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          type="button"
          @click="closeDialog"
        >
          取消
        </button>
        <button
          class="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-700"
          type="button"
          @click="submitForm"
        >
          确定
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CreateRequirementPayload } from '../api/projects'

export interface CreateRequirementForm extends CreateRequirementPayload {}

const props = defineProps<{
  modelValue: boolean
  defaultModule: string
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'create', value: CreateRequirementForm): void
}>()

const formData = ref<CreateRequirementForm>({
  code: '',
  title: '',
  type: '功能需求',
  content: '',
  module: props.defaultModule
})

watch(
  () => props.defaultModule,
  (value) => {
    formData.value.module = value
  }
)

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      formData.value = {
        code: '',
        title: '',
        type: '功能需求',
        content: '',
        module: props.defaultModule
      }
    }
  }
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const submitForm = () => {
  if (!formData.value.code || !formData.value.title || !formData.value.content) {
    window.alert('请填写完整的需求信息')
    return
  }
  emit('create', { ...formData.value })
}
</script>