<template>
  <AppDialog
    :model-value="modelValue"
    title="新增需求"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="space-y-6">
      <div class="grid gap-4 rounded-xl border border-zinc-200 bg-zinc-50/70 p-4 text-sm">
        <div>
          <p class="text-xs font-medium text-zinc-500">需求编号</p>
          <input
            v-model="formData.code"
            class="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            placeholder="请输入需求编号"
          />
        </div>
        <div>
          <p class="text-xs font-medium text-zinc-500">需求标题</p>
          <input
            v-model="formData.title"
            class="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            placeholder="请输入需求标题"
          />
        </div>
        <div>
          <p class="text-xs font-medium text-zinc-500">需求类型</p>
          <select
            v-model="formData.type"
            class="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
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
          <p class="text-xs font-medium text-zinc-500">需求内容</p>
          <textarea
            v-model="formData.content"
            rows="4"
            class="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-800 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-950/5"
            placeholder="请输入需求内容"
          ></textarea>
        </div>
        <div>
          <p class="text-xs font-medium text-zinc-500">所属模块</p>
          <input
            v-model="formData.module"
            class="mt-1 w-full rounded-lg border border-zinc-200 bg-zinc-100 px-3 py-1.5 text-sm text-zinc-600 outline-none"
            placeholder="请输入所属模块"
            readonly
          />
        </div>
      </div>
    </div>
    <template #footer-start>
      <AppDialogButton @click="closeDialog">取消</AppDialogButton>
    </template>
    <template #footer-end>
      <AppDialogButton variant="primary" :disabled="submitDisabled" @click="submitForm">
        确定
      </AppDialogButton>
    </template>
  </AppDialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CreateRequirementPayload } from '../api/projects'
import AppDialog from './ui/AppDialog.vue'
import AppDialogButton from './ui/AppDialogButton.vue'

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

const submitDisabled = computed(
  () => !formData.value.code.trim() || !formData.value.title.trim() || !formData.value.content.trim()
)

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
  if (submitDisabled.value) return
  emit('create', { ...formData.value })
}
</script>
