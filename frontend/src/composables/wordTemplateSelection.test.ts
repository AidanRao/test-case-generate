import {
  buildExportSelection,
  selectInitialTemplateId
} from './wordTemplateSelection.ts'

const assertEqual = (actual: unknown, expected: unknown) => {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`
    )
  }
}

const templates = [
  { template_id: 'default', name: '标准测试用例文档' },
  { template_id: 'compact', name: '精简模板' }
]

assertEqual(selectInitialTemplateId(templates, ''), 'default')
assertEqual(
  selectInitialTemplateId(templates, 'compact'),
  'compact'
)
assertEqual(
  selectInitialTemplateId(templates, 'missing'),
  'default'
)
assertEqual(
  buildExportSelection('word', 'default'),
  { format: 'word', templateId: 'default' }
)
assertEqual(buildExportSelection('word', ''), null)
assertEqual(
  buildExportSelection('excel', ''),
  { format: 'excel' }
)
