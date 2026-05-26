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
                @click="saveConfigHandler"
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

      <div class="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-100 px-6 py-4">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100">
              <el-icon class="text-lg text-sky-600"><Timer /></el-icon>
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900">系统定时任务</h2>
              <p class="text-xs text-slate-500">管理后台数据同步任务的运行状态和执行间隔</p>
            </div>
          </div>
        </div>

        <div class="p-6">
          <div v-if="tasksLoading" class="flex justify-center py-8">
            <el-spinner class="text-sky-600" />
          </div>

          <template v-else>
            <div class="rounded-xl border border-slate-200 p-5">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ syncTask.name }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ syncTask.description }}</p>
                </div>
                <label class="inline-flex cursor-pointer items-center gap-2 text-sm text-slate-600">
                  <input
                    v-model="syncTask.enabled"
                    type="checkbox"
                    class="h-4 w-4 rounded border-slate-300 text-sky-600"
                  />
                  启用
                </label>
              </div>

              <div class="mt-5 max-w-xs">
                <label class="mb-2 block text-sm font-medium text-slate-700">执行间隔（秒）</label>
                <input
                  v-model.number="syncTask.interval_seconds"
                  type="number"
                  min="5"
                  max="86400"
                  class="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none disabled:bg-slate-50 disabled:text-slate-400"
                  :disabled="!syncTask.enabled"
                />
                <p class="mt-2 text-xs text-slate-400">允许范围：5 - 86400 秒</p>
              </div>

              <p v-if="!syncTask.available" class="mt-4 text-xs text-amber-600">
                当前未检测到 UniPortal 数据目录，启用后将在数据目录可用时执行。
              </p>

              <div class="mt-6 flex justify-end">
                <button
                  class="rounded-xl bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  :disabled="tasksSaving"
                  @click="saveTaskConfig"
                >
                  <span v-if="tasksSaving">保存中</span>
                  <span v-else>保存任务配置</span>
                </button>
              </div>
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
import { ArrowLeft, Setting, CircleCheck, CircleClose, Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig } from '../api/aiConfig'
import { getSystemTasks, updateSystemTask } from '../api/systemTasks'

const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const tasksLoading = ref(true)
const tasksSaving = ref(false)

const form = reactive({
  baseUrl: '',
  apiKey: '',
  model: ''
})

const testing = ref(false)
const testResult = ref<'success' | 'error' | null>(null)
const syncTask = reactive({
  id: 'uniportal_sync',
  name: 'UniPortal 项目同步',
  description: '定期从 UniPortal 同步项目和需求数据',
  enabled: false,
  interval_seconds: 300,
  available: false,
  running: false
})

const loadConfig = async () => {
  loading.value = true
  try {
    const config = await getConfig()
    if (config && typeof config === 'object') {
      form.apiKey = config.api_key || ''
      form.baseUrl = config.base_url || ''
      form.model = config.model || ''
    }
  } catch {
    form.apiKey = ''
    form.baseUrl = ''
    form.model = ''
  } finally {
    loading.value = false
  }
}

const saveConfigHandler = async () => {
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

    await saveConfig(payload)
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

const loadTasks = async () => {
  tasksLoading.value = true
  try {
    const tasks = await getSystemTasks()
    const task = tasks.find((item) => item.id === syncTask.id)
    if (task) {
      Object.assign(syncTask, task)
    }
  } catch {
    ElMessage.error('定时任务配置加载失败')
  } finally {
    tasksLoading.value = false
  }
}

const saveTaskConfig = async () => {
  const interval = Number(syncTask.interval_seconds)
  if (!Number.isInteger(interval) || interval < 5 || interval > 86400) {
    ElMessage.warning('执行间隔应为 5 至 86400 秒之间的整数')
    return
  }
  tasksSaving.value = true
  try {
    const task = await updateSystemTask(syncTask.id, {
      enabled: syncTask.enabled,
      interval_seconds: interval
    })
    Object.assign(syncTask, task)
    ElMessage.success('定时任务配置已保存')
  } catch {
    ElMessage.error('定时任务配置保存失败')
  } finally {
    tasksSaving.value = false
  }
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
  loadTasks()
})
</script>
