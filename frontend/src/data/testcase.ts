export const SCENARIO_TYPES = [
  '正常流程用例',
  '边界条件用例',
  '异常场景用例',
  '组合场景用例',
  '回归测试用例'
] as const

export type ScenarioType = (typeof SCENARIO_TYPES)[number]

export const PRIORITY_LEVELS = ['P0', 'P1', 'P2', 'P3'] as const

export type TestCasePriority = (typeof PRIORITY_LEVELS)[number]

export interface TestCaseItem {
  id?: string
  code: string
  title: string
  type: string
  scenario_type: ScenarioType
  priority?: TestCasePriority
  requirement_id?: string
  requirement_code?: string
  test_steps: Array<{ expectation: string; step_desc: string }>
  test_target_desc: string
  verify_method: string
}

export type RequirementTestCaseItem = TestCaseItem
export type TestCaseDetailItem = TestCaseItem
