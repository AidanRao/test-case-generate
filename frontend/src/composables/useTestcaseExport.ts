import { ref, type ComputedRef } from 'vue'
import type { ModuleGroup, Requirement } from '../data/projectStore'
import type { RequirementTestCaseItem } from '../components/RequirementDetailDialog.vue'
import { exportTestcasesExcel } from '../api/projects'

export type ExportFormat = 'json' | 'md' | 'excel'

type RequirementWithCases = Requirement & {
  testcases?: RequirementTestCaseItem[]
  hasRemoteTestcases?: boolean
  ID?: string
}

type BuildTestcases = (requirement: RequirementWithCases | null) => RequirementTestCaseItem[]

type UseTestcaseExportOptions = {
  moduleGroups: ComputedRef<ModuleGroup[]>
  projectName: ComputedRef<string>
  projectId: ComputedRef<string>
  buildTestcases: BuildTestcases
}

export const useTestcaseExport = ({
  moduleGroups,
  projectName,
  projectId,
  buildTestcases
}: UseTestcaseExportOptions) => {
  const exportDialogVisible = ref(false)

  const openExportDialog = () => {
    exportDialogVisible.value = true
  }

  const sanitizeFilename = (name: string) => name.replace(/[\\/:*?"<>|]+/g, '-')

  const buildExportModules = () =>
    moduleGroups.value.map((group) => {
      const requirements = group.requirements.map((req) => {
        const requirement = { ...req, module: group.module } as RequirementWithCases
        return {
          id: req.ID || req.code || req.title,
          title: req.title,
          code: req.code,
          type: req.type,
          content: req.content,
          testcases: buildTestcases(requirement)
        }
      })
      return {
        module: group.module,
        requirements
      }
    })

  const triggerDownload = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  const buildMarkdown = (modules: ReturnType<typeof buildExportModules>) => {
    const lines: string[] = [`# ${projectName.value} 测试用例导出`]
    modules.forEach((group) => {
      lines.push(`\n## 模块：${group.module}`)
      group.requirements.forEach((req) => {
        lines.push(`\n### 需求：${req.title}`)
        lines.push(`- 需求编号：${req.code || req.id || '暂无'}`)
        lines.push(`- 需求类型：${req.type || '未知类型'}`)
        lines.push(`- 需求内容：${req.content || '暂无'}`)
        if (req.testcases.length === 0) {
          lines.push('- 测试用例：暂无')
          return
        }
        lines.push('#### 测试用例')
        req.testcases.forEach((tc, index) => {
          lines.push(`${index + 1}. ${tc.title || '未命名测试用例'}`)
          lines.push(`   - 编号：${tc.code || tc.id || '暂无'}`)
          lines.push(`   - 类型：${tc.type || '未知类型'}`)
          lines.push(`   - 目标：${tc.test_target_desc || '暂无'}`)
          if (tc.test_steps.length > 0) {
            lines.push('   - 步骤：')
            tc.test_steps.forEach((step, stepIndex) => {
              lines.push(`     ${stepIndex + 1}) ${step.step_desc} -> ${step.expectation}`)
            })
          } else {
            lines.push('   - 步骤：暂无')
          }
        })
      })
    })
    return lines.join('\n')
  }

  const handleExport = async (format: ExportFormat) => {
    const modules = buildExportModules()
    const baseName = sanitizeFilename(projectName.value || '测试用例')
    if (format === 'json') {
      const content = JSON.stringify({ project: { id: projectId.value, name: projectName.value }, modules }, null, 2)
      triggerDownload(content, `${baseName}-测试用例.json`, 'application/json;charset=utf-8')
      return
    }
    if (format === 'md') {
      const content = buildMarkdown(modules)
      triggerDownload(content, `${baseName}-测试用例.md`, 'text/markdown;charset=utf-8')
      return
    }
    const { blob, headers } = await exportTestcasesExcel(projectId.value)
    const disposition = headers.get('content-disposition') || headers.get('Content-Disposition') || ''
    const filenameMatch = /filename\*=UTF-8''([^;]+)|filename="?([^"]+)"?/i.exec(disposition)
    const rawName = filenameMatch?.[1] || filenameMatch?.[2]
    const filename = rawName ? decodeURIComponent(rawName) : `${baseName}-测试用例.xlsx`
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  return {
    exportDialogVisible,
    openExportDialog,
    handleExport
  }
}
