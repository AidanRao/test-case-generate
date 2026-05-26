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
            <div class="overflow-x-auto rounded-xl border border-slate-200">
              <table class="w-full min-w-[700px] table-fixed divide-y divide-slate-200">
                <colgroup>
                  <col class="w-[36%]" />
                  <col class="w-[22%]" />
                  <col class="w-[14%]" />
                  <col class="w-[28%]" />
                </colgroup>
                <thead class="bg-slate-50">
                  <tr>
                    <th class="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">任务</th>
                    <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">执行间隔（秒）</th>
                    <th class="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">启用</th>
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
                    <td colspan="4" class="px-6 py-10 text-center text-sm text-slate-400">暂无系统任务</td>
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
import { ArrowLeft, Setting, CircleCheck, CircleClose, Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig } from '../api/aiConfig'
import { getSystemTasks, runSystemTask, updateSystemTask, type SystemTask } from '../api/systemTasks'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const saving = ref(false)
const tasksLoading = ref(true)
const tasks = ref<SystemTask[]>([])
const tasksSaving = reactive<Record<string, boolean>>({})
const tasksRunning = reactive<Record<string, boolean>>({})

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
    tasks.value = await getSystemTasks()
  } catch {
    ElMessage.error('定时任务配置加载失败')
  } finally {
    tasksLoading.value = false
  }
}

const replaceTask = (updated: SystemTask) => {
  const index = tasks.value.findIndex((task) => task.id === updated.id)
  if (index >= 0) {
    tasks.value[index] = updated
  }
}

const isTaskSaving = (taskId: string) => Boolean(tasksSaving[taskId])
const isTaskRunning = (taskId: string) => Boolean(tasksRunning[taskId])

const saveTaskConfig = async (task: SystemTask) => {
  const interval = Number(task.interval_seconds)
  if (!Number.isInteger(interval) || interval < 5 || interval > 86400) {
    ElMessage.warning('执行间隔应为 5 至 86400 秒之间的整数')
    return
  }
  tasksSaving[task.id] = true
  try {
    const updated = await updateSystemTask(task.id, {
      enabled: task.enabled,
      interval_seconds: interval
    })
    replaceTask(updated)
    ElMessage.success('定时任务配置已保存')
  } catch {
    ElMessage.error('定时任务配置保存失败')
  } finally {
    tasksSaving[task.id] = false
  }
}

const runTaskNow = async (task: SystemTask) => {
  tasksRunning[task.id] = true
  try {
    const updated = await runSystemTask(task.id)
    replaceTask(updated)
    ElMessage.success('任务执行完成')
  } catch {
    ElMessage.error('任务执行失败，请检查数据源状态')
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
