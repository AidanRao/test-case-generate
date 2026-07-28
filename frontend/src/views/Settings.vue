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
                  两端连接成功
                </span>
                <span v-else-if="testResult === 'partial'" class="flex items-center gap-2">
                  <el-icon class="h-4 w-4 text-amber-500"><Warning /></el-icon>
                  部分连接失败
                </span>
                <span v-else-if="testResult === 'error'" class="flex items-center gap-2">
                  <el-icon class="h-4 w-4 text-rose-500"><CircleClose /></el-icon>
                  两端连接失败
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

      <AppDialog
        :model-value="resultDialogVisible"
        title="LLM API 测试结果"
        description="前端测试由浏览器直连 LLM，后端测试由应用服务器发起请求。"
        size="lg"
        :close-on-click-outside="!testing"
        @update:model-value="resultDialogVisible = $event"
      >
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-slate-200 bg-slate-50/70 p-5">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-100">
                  <el-icon class="text-zinc-700"><Monitor /></el-icon>
                </div>
                <div>
                  <h3 class="text-sm font-semibold text-slate-900">前端测试</h3>
                  <p class="text-xs text-slate-500">浏览器 → LLM API</p>
                </div>
              </div>
              <span :class="resultBadgeClass(frontendTestResult)">
                {{ resultStatusText(frontendTestResult) }}
              </span>
            </div>
            <div v-if="!frontendTestResult" class="flex items-center gap-2 py-6 text-sm text-slate-500">
              <el-spinner class="h-4 w-4" /> 正在测试前端连接...
            </div>
            <div v-else class="space-y-3 text-sm">
              <div class="grid grid-cols-2 gap-3">
                <div class="rounded-xl bg-white p-3">
                  <p class="text-xs text-slate-400">HTTP 状态</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ frontendTestResult.status_code ?? '—' }}</p>
                </div>
                <div class="rounded-xl bg-white p-3">
                  <p class="text-xs text-slate-400">耗时</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ frontendTestResult.duration_ms }} ms</p>
                </div>
              </div>
              <p class="font-medium text-slate-700">{{ frontendTestResult.message }}</p>
              <pre v-if="frontendTestResult.detail" class="max-h-36 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-slate-900 p-3 text-xs leading-relaxed text-slate-200">{{ frontendTestResult.detail }}</pre>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50/70 p-5">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-100">
                  <el-icon class="text-zinc-700"><DataLine /></el-icon>
                </div>
                <div>
                  <h3 class="text-sm font-semibold text-slate-900">后端测试</h3>
                  <p class="text-xs text-slate-500">应用服务器 → LLM API</p>
                </div>
              </div>
              <span :class="resultBadgeClass(backendTestResult)">
                {{ resultStatusText(backendTestResult) }}
              </span>
            </div>
            <div v-if="!backendTestResult" class="flex items-center gap-2 py-6 text-sm text-slate-500">
              <el-spinner class="h-4 w-4" /> 正在测试后端连接...
            </div>
            <div v-else class="space-y-3 text-sm">
              <div class="grid grid-cols-2 gap-3">
                <div class="rounded-xl bg-white p-3">
                  <p class="text-xs text-slate-400">HTTP 状态</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ backendTestResult.status_code ?? '—' }}</p>
                </div>
                <div class="rounded-xl bg-white p-3">
                  <p class="text-xs text-slate-400">耗时</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ backendTestResult.duration_ms }} ms</p>
                </div>
              </div>
              <p class="font-medium text-slate-700">{{ backendTestResult.message }}</p>
              <pre v-if="backendTestResult.detail" class="max-h-36 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-slate-900 p-3 text-xs leading-relaxed text-slate-200">{{ backendTestResult.detail }}</pre>
            </div>
          </div>
        </div>

        <template #footer-end>
          <AppDialogButton
            variant="primary"
            :disabled="testing"
            @click="resultDialogVisible = false"
          >
            {{ testing ? '测试中...' : '关闭' }}
          </AppDialogButton>
        </template>
      </AppDialog>

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
            <div class="overflow-x-auto rounded-xl border border-slate-200">
              <table class="w-full min-w-[980px] table-fixed divide-y divide-slate-200">
                <colgroup>
                  <col class="w-[27%]" />
                  <col class="w-[17%]" />
                  <col class="w-[12%]" />
                  <col class="w-[26%]" />
                  <col class="w-[18%]" />
                </colgroup>
                <thead class="bg-slate-50">
                  <tr>
                    <th class="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">任务</th>
                    <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">执行间隔（秒）</th>
                    <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">启用</th>
                    <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">kwargs</th>
                    <th class="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-for="task in tasks" :key="task.id" class="hover:bg-slate-50">
                    <td class="px-5 py-5">
                      <p class="text-sm font-semibold text-slate-800">{{ task.name }}</p>
                      <p class="mt-1 text-xs text-slate-500">{{ task.description }}</p>
                    </td>
                    <td class="px-4 py-5">
                      <input
                        v-model.number="task.interval_seconds"
                        type="number"
                        min="5"
                        max="86400"
                        class="h-10 w-32 rounded-lg border border-slate-200 px-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none disabled:bg-slate-50 disabled:text-slate-400"
                        :disabled="!task.enabled || isTaskSaving(task.id)"
                      />
                      <p class="mt-1.5 text-xs text-slate-400">5 - 86400</p>
                    </td>
                    <td class="px-4 py-5">
                      <label class="inline-flex cursor-pointer items-center gap-2 text-sm text-slate-600">
                        <input
                          v-model="task.enabled"
                          type="checkbox"
                          class="h-4 w-4 rounded border-slate-300 text-sky-600"
                          :disabled="isTaskSaving(task.id)"
                        />
                        {{ task.enabled ? '启用' : '停用' }}
                      </label>
                    </td>
                    <td class="px-4 py-5">
                      <textarea
                        v-model="task.kwargsText"
                        rows="4"
                        class="w-full resize-y rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs leading-relaxed text-slate-700 focus:border-sky-400 focus:outline-none disabled:bg-slate-50 disabled:text-slate-400"
                        :disabled="isTaskSaving(task.id)"
                      />
                    </td>
                    <td class="whitespace-nowrap px-5 py-5 text-right">
                      <div class="inline-flex items-center gap-2">
                        <button
                          class="rounded-full border border-sky-200 px-4 py-2 text-sm font-semibold text-sky-700 transition hover:bg-sky-50 disabled:cursor-not-allowed disabled:border-slate-100 disabled:text-slate-300"
                          :disabled="!task.available || isTaskRunning(task.id)"
                          @click="runTaskNow(task)"
                        >
                          {{ isTaskRunning(task.id) ? '执行中' : '立即执行' }}
                        </button>
                        <button
                          class="rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                          :disabled="isTaskSaving(task.id)"
                          @click="saveTaskConfig(task)"
                        >
                          {{ isTaskSaving(task.id) ? '保存中' : '保存' }}
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="tasks.length === 0">
                    <td colspan="5" class="px-6 py-10 text-center text-sm text-slate-400">暂无系统任务</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Setting, CircleCheck, CircleClose, Timer, Warning, Monitor, DataLine } from '@element-plus/icons-vue'
import AppDialog from '../components/ui/AppDialog.vue'
import AppDialogButton from '../components/ui/AppDialogButton.vue'
import { useAppFeedback } from '../composables/useAppFeedback'
import {
  getConfig,
  saveConfig,
  testBackendConnection,
  type ConnectionTestResult
} from '../api/aiConfig'
import { getSystemTasks, runSystemTask, updateSystemTask, type SystemTask } from '../api/systemTasks'

const router = useRouter()
const route = useRoute()
const { notify } = useAppFeedback()

const loading = ref(true)
const saving = ref(false)
const tasksLoading = ref(true)
type SystemTaskEditor = SystemTask & { kwargsText: string }

const tasks = ref<SystemTaskEditor[]>([])
const tasksSaving = reactive<Record<string, boolean>>({})
const tasksRunning = reactive<Record<string, boolean>>({})

const form = reactive({
  baseUrl: '',
  apiKey: '',
  model: ''
})

const testing = ref(false)
const testResult = ref<'success' | 'partial' | 'error' | null>(null)
const resultDialogVisible = ref(false)
const frontendTestResult = ref<ConnectionTestResult | null>(null)
const backendTestResult = ref<ConnectionTestResult | null>(null)

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
    notify({ message: '请输入 Base URL' })
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
    notify({ message: '保存成功', tone: 'success' })
    await loadConfig()
  } catch {
    notify({ message: '保存失败，请稍后重试', tone: 'error' })
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
    tasks.value = (await getSystemTasks()).map(toTaskEditor)
  } catch {
    notify({ message: '定时任务配置加载失败', tone: 'error' })
  } finally {
    tasksLoading.value = false
  }
}

const toTaskEditor = (task: SystemTask): SystemTaskEditor => ({
  ...task,
  kwargsText: JSON.stringify(task.kwargs ?? {}, null, 2)
})

const replaceTask = (updated: SystemTask) => {
  const index = tasks.value.findIndex((task) => task.id === updated.id)
  if (index >= 0) {
    tasks.value[index] = toTaskEditor(updated)
  }
}

const isTaskSaving = (taskId: string) => Boolean(tasksSaving[taskId])
const isTaskRunning = (taskId: string) => Boolean(tasksRunning[taskId])

const saveTaskConfig = async (task: SystemTaskEditor) => {
  const interval = Number(task.interval_seconds)
  if (!Number.isInteger(interval) || interval < 5 || interval > 86400) {
    notify({ message: '执行间隔应为 5 至 86400 秒之间的整数' })
    return
  }
  let kwargs: Record<string, unknown>
  try {
    const parsed = JSON.parse(task.kwargsText || '{}')
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
      throw new Error('kwargs must be an object')
    }
    kwargs = parsed as Record<string, unknown>
  } catch {
    notify({ message: 'kwargs 必须是合法的 JSON 对象' })
    return
  }
  tasksSaving[task.id] = true
  try {
    const updated = await updateSystemTask(task.id, {
      enabled: task.enabled,
      interval_seconds: interval,
      kwargs
    })
    replaceTask(updated)
    notify({ message: '定时任务配置已保存', tone: 'success' })
  } catch {
    notify({ message: '定时任务配置保存失败', tone: 'error' })
  } finally {
    tasksSaving[task.id] = false
  }
}

const runTaskNow = async (task: SystemTaskEditor) => {
  tasksRunning[task.id] = true
  try {
    const updated = await runSystemTask(task.id)
    replaceTask(updated)
    notify({ message: '任务执行完成', tone: 'success' })
  } catch {
    notify({ message: '任务执行失败，请检查数据源状态', tone: 'error' })
  } finally {
    tasksRunning[task.id] = false
  }
}

const goBack = () => {
  const portalProjectId = typeof route.query.portal_project_id === 'string'
    ? route.query.portal_project_id
    : null
  router.push({
    name: 'projects',
    query: portalProjectId ? { portal_project_id: portalProjectId } : {}
  })
}

const resultStatusText = (result: ConnectionTestResult | null) => {
  if (!result) return '检测中'
  return result.success ? '成功' : '失败'
}

const resultBadgeClass = (result: ConnectionTestResult | null) => [
  'rounded-full px-2.5 py-1 text-xs font-semibold',
  !result
    ? 'bg-slate-200 text-slate-500'
    : result.success
      ? 'bg-emerald-100 text-emerald-700'
      : 'bg-rose-100 text-rose-700'
]

const runFrontendTest = async (payload: { api_key: string; base_url: string; model: string }) => {
  const startedAt = performance.now()
  try {
    const response = await fetch(`${payload.base_url.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(payload.api_key && { 'Authorization': `Bearer ${payload.api_key}` })
      },
      body: JSON.stringify({
        model: payload.model,
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1
      }),
      signal: AbortSignal.timeout(10000)
    })
    const responseText = (await response.text()).slice(0, 2000)
    return {
      success: response.ok,
      status_code: response.status,
      duration_ms: Math.round(performance.now() - startedAt),
      message: response.ok ? '前端连接成功' : `LLM API 返回 HTTP ${response.status}`,
      detail: responseText
    } satisfies ConnectionTestResult
  } catch (error) {
    return {
      success: false,
      status_code: null,
      duration_ms: Math.round(performance.now() - startedAt),
      message: '浏览器无法连接 LLM API',
      detail: error instanceof Error ? error.message : String(error)
    } satisfies ConnectionTestResult
  }
}

const runBackendTest = async (payload: { api_key: string; base_url: string; model: string }) => {
  const startedAt = performance.now()
  try {
    return await testBackendConnection(payload)
  } catch (error) {
    return {
      success: false,
      status_code: null,
      duration_ms: Math.round(performance.now() - startedAt),
      message: '无法发起后端测试',
      detail: error instanceof Error ? error.message : String(error)
    } satisfies ConnectionTestResult
  }
}

const testConnection = async () => {
  if (!form.baseUrl.trim()) {
    notify({ message: '请输入 Base URL' })
    return
  }

  const payload = {
    api_key: form.apiKey.trim(),
    base_url: form.baseUrl.trim(),
    model: form.model.trim() || 'qwen3-max'
  }

  testing.value = true
  testResult.value = null
  frontendTestResult.value = null
  backendTestResult.value = null
  resultDialogVisible.value = true

  const frontendPromise = runFrontendTest(payload).then((result) => {
    frontendTestResult.value = result
    return result
  })
  const backendPromise = runBackendTest(payload).then((result) => {
    backendTestResult.value = result
    return result
  })

  const [frontendResult, backendResult] = await Promise.all([frontendPromise, backendPromise])
  const successCount = [frontendResult, backendResult].filter((result) => result.success).length
  testResult.value = successCount === 2 ? 'success' : successCount === 1 ? 'partial' : 'error'
  testing.value = false
}

onMounted(() => {
  loadConfig()
  loadTasks()
})
</script>
