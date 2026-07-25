import type { WordReportTemplate } from '../api/projects'

export type ExportFormat = 'json' | 'md' | 'word' | 'excel'

export type ExportSelection = {
  format: ExportFormat
  templateId?: string
}

export const selectInitialTemplateId = (
  templates: WordReportTemplate[],
  currentTemplateId: string
) => {
  if (templates.some((item) => item.template_id === currentTemplateId)) {
    return currentTemplateId
  }
  return templates[0]?.template_id ?? ''
}

export const buildExportSelection = (
  format: ExportFormat,
  templateId: string
): ExportSelection | null => {
  if (format === 'word') {
    return templateId
      ? { format, templateId }
      : null
  }
  return { format }
}
