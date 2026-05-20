<template>
  <div class="min-h-screen bg-gradient-to-b from-white to-slate-50">
    <div class="mx-auto max-w-4xl px-6 py-10">
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">系统设置</h1>
        </div>
        <button
          class="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
          @click="goBack"
        >
          <el-icon class="text-base"><ArrowLeft /></el-icon>
          返回
        </button>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-100 px-6 py-4">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100">
              <el-icon class="text-lg text-indigo-600"><Setting /></el-icon>
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900">LLM API 设置</h2>
              <p class="text-xs text-slate-500">配置用于生成测试用例的 AI 服务</p>
            </div>
          </div>
        </div>

        <div class="p-6">
          <div v-if="loading" class="flex justify-center py-8">
            <el-spinner class="text-sky-600" />
          </div>

          <template v-else>
            <div class="space-y-6">
              <div>
                <label class="mb-2 block text-sm font-medium text-slate-700">Base URL</label>
                <input
                  v-model="form.baseUrl"
                  type="text"
                  class="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none"
                  placeholder="例如: https://dashscope.aliyuncs.com/compatible-mode/v1"
                  @input="testResult = null"
                />
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-700">API Key</label>
                <input
                  v-model="form.apiKey"
                  type="password"
                  class="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none"
                  placeholder="可选，API 密钥"
                  @input="testResult = null"
                />
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-700">Model</label>
                <input
                  v-model="form.model"
                  type="text"
                  class="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none"
                  placeholder="可选，如 qwen3-max"
                  @input="testResult = null"
                />
              </div>
            </div>

            <div class="mt-8 flex items-center gap-3">
              <button
                class="rounded-xl border border-slate-200 px-6 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
                :disabled="!form.baseUrl || testing"
                @click="testConnection"
              >
                <span v-if="testing" class="flex items-center gap-2">
                  <el-spinner class="h-4 w-4" />
                  测试中
                </span>
                <span v-else-if="testResult === 'success'" class="flex items-center gap-2">
                  <el-icon class="h-4 w-4 text-emerald-500"><CircleCheck /></el-icon>
                  连接成功
                </span>
                <span v-else-if="testResult === 'error'" class="flex items-center gap-2">
                  <el-icon class="h-4 w-4 text-rose-500"><CircleClose /></el-icon>
                  连接失败
                </span>
                <span v-else>测试连接</span>
              </button>
              <button
                class="rounded-xl border border-slate-200 px-6 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
                @click="resetForm"
              >
                重置
              </button>
              <div class="flex-1"></div>
              <button
                class="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700"
                :disabled="!form.baseUrl || saving"
                @click="saveConfig"
              >
                <span v-if="saving" class="flex items-center gap-2">
                  <el-spinner class="h-4 w-4" />
                  保存中
                </span>
                <span v-else>保存设置</span>
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Setting, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createConfig, updateConfig, getDefaultConfig } from '../api/aiConfig'

const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const existingConfigId = ref<string | null>(null)

const form = reactive({
  baseUrl: '',
  apiKey: '',
  model: ''
})

const testing = ref(false)
const testResult = ref<'success' | 'error' | null>(null)

const loadConfig = async () => {
  loading.value = true
  try {
    const config = await getDefaultConfig()
    if (config && typeof config === 'object' && 'id' in config) {
      existingConfigId.value = (config as any).id
      form.apiKey = (config as any).api_key || ''
      form.baseUrl = (config as any).base_url || ''
      form.model = (config as any).model || ''
    }
  } catch {
    form.apiKey = ''
    form.baseUrl = ''
    form.model = ''
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  if (!form.baseUrl.trim()) {
    ElMessage.warning('请输入 Base URL')
    return
  }

  saving.value = true
  try {
    const payload = {
      api_key: form.apiKey.trim(),
      base_url: form.baseUrl.trim(),
      model: form.model.trim()
    }

    if (existingConfigId.value) {
      await updateConfig(existingConfigId.value, payload)
    } else {
      await createConfig(payload)
    }

    ElMessage.success('保存成功')
    await loadConfig()
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  form.apiKey = ''
  form.baseUrl = ''
  form.model = ''
  testResult.value = null
}

const goBack = () => {
  router.push('/projects')
}

const testConnection = async () => {
  if (!form.baseUrl.trim()) {
    ElMessage.warning('请输入 Base URL')
    return
  }

  testing.value = true
  testResult.value = null

  try {
    const baseUrl = form.baseUrl.trim()
    const apiKey = form.apiKey.trim()
    const model = form.model.trim() || 'qwen3-max'

    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
      },
      body: JSON.stringify({
        model: model,
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1
      }),
      signal: AbortSignal.timeout(10000)
    })

    if (response.ok) {
      testResult.value = 'success'
      ElMessage.success('连接成功！')
    } else {
      testResult.value = 'error'
      const errorText = await response.text()
      ElMessage.error(`连接失败: ${response.status} - ${errorText}`)
    }
  } catch (error) {
    testResult.value = 'error'
    ElMessage.error(`连接失败: ${(error as Error).message}`)
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>
