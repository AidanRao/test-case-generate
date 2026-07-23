import type { ModuleGroup, Requirement } from '../data/projectStore'
import type { RequirementTestCaseItem } from '../data/testcase'

export type RequirementWithTestcases = Omit<Requirement, 'module'> & {
  module?: string
  id?: string
  project_id?: string
  testcases?: RequirementTestCaseItem[]
  hasRemoteTestcases?: boolean
}

export type RemoteRequirementWithTestcases = Omit<RequirementWithTestcases, 'ID'> & {
  id?: string
  ID?: string
  module?: string
}

export type ModuleGroupWithTestcases = Omit<ModuleGroup, 'requirements'> & {
  requirements: RequirementWithTestcases[]
}

export const getRequirementIdentity = (item: RequirementWithTestcases | null | undefined) =>
  item?.id || item?.ID || item?.code || item?.title || ''

export const isSameRequirement = (
  source: RequirementWithTestcases,
  target: RequirementWithTestcases
) => {
  const sourceIdentity = getRequirementIdentity(source)
  const targetIdentity = getRequirementIdentity(target)
  if (sourceIdentity && targetIdentity) {
    return sourceIdentity === targetIdentity
  }
  return source.title === target.title && source.content === target.content
}

export const normalizeRequirementCode = (requirement: RequirementWithTestcases | null) =>
  requirement?.code || requirement?.ID || ''

export const buildTestcases = (
  requirement: RequirementWithTestcases | null
): RequirementTestCaseItem[] => {
  if (!requirement) return []
  if (requirement.hasRemoteTestcases) {
    return requirement.testcases ?? []
  }
  if (Array.isArray(requirement.testcases) && requirement.testcases.length > 0) {
    return requirement.testcases
  }

  const requirement_code = normalizeRequirementCode(requirement)
  const requirement_id = requirement.ID || requirement.code || requirement.title
  const fragments = (requirement.content || '')
    .split(/[；。]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3)

  return fragments.map((fragment, index) => {
    const baseCode = requirement_code || `REQ-${String(index + 1).padStart(3, '0')}`
    return {
      id: '',
      requirement_code,
      requirement_id,
      title: `${requirement.title}-测试点${index + 1}`,
      code: `TC-${baseCode}-${String(index + 1).padStart(3, '0')}`,
      type: '功能测试',
      scenario_type: '正常流程用例',
      test_steps: [
        {
          step_desc: fragment,
          expectation: '符合预期'
        }
      ],
      test_target_desc: fragment,
      verify_method: 'TESTING'
    }
  })
}

export const mapRemoteModules = (
  remoteRequirements: RemoteRequirementWithTestcases[],
  remoteModuleNames: string[] = []
): ModuleGroupWithTestcases[] => {
  const moduleMap = new Map<string, ModuleGroupWithTestcases>()
  remoteModuleNames.forEach((item) => {
    const moduleName = item || '未命名模块'
    if (!moduleMap.has(moduleName)) {
      moduleMap.set(moduleName, { module: moduleName, requirements: [] })
    }
  })
  remoteRequirements.forEach((item) => {
    const moduleName = item.module || '未命名模块'
    if (!moduleMap.has(moduleName)) {
      moduleMap.set(moduleName, { module: moduleName, requirements: [] })
    }
    moduleMap.get(moduleName)!.requirements.push({
      ...item,
      ID: item.id ?? item.ID,
      module: moduleName,
      testcases: item.testcases ?? [],
      hasRemoteTestcases: true
    })
  })
  return Array.from(moduleMap.values())
}
