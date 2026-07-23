import {
  buildTestcases,
  getRequirementIdentity,
  isSameRequirement,
  mapRemoteModules,
  type RequirementWithTestcases
} from './useRequirementTestcases'

const localRequirement: RequirementWithTestcases = {
  ID: 'REQ-1',
  code: 'REQ-001',
  title: '登录',
  type: '功能测试',
  module: '认证',
  content: '输入正确账号密码后可以登录。输入错误密码后提示失败。'
}

const fallbackTestcases = buildTestcases(localRequirement)
if (fallbackTestcases.length !== 2) {
  throw new Error('buildTestcases should create fallback cases from requirement content fragments')
}
if (fallbackTestcases[0] && 'priority' in fallbackTestcases[0]) {
  throw new Error('buildTestcases should not assign the backend-owned priority default')
}

const remoteModules = mapRemoteModules([
  {
    id: 'remote-1',
    project_id: 'project-1',
    module: '认证',
    title: '登录',
    type: '功能测试',
    code: 'REQ-001',
    content: '登录内容',
    testcases: [
      {
        requirement_code: 'REQ-001',
        requirement_id: 'remote-1',
        id: 'tc-1',
        title: '登录成功',
        code: 'TC-001',
        type: '功能测试',
        scenario_type: '正常流程用例',
        priority: 'P1',
        test_steps: [],
        test_target_desc: '验证登录',
        verify_method: 'TESTING'
      }
    ]
  }
])

if (remoteModules[0]?.requirements[0]?.ID !== 'remote-1') {
  throw new Error('mapRemoteModules should normalize remote id to ID')
}

const modulesWithEmptyGroup = mapRemoteModules([], ['空模块'])
if (modulesWithEmptyGroup[0]?.module !== '空模块' || modulesWithEmptyGroup[0]?.requirements.length !== 0) {
  throw new Error('mapRemoteModules should preserve empty remote modules')
}

if (!isSameRequirement(localRequirement, { ...localRequirement, title: '登录标题已改' })) {
  throw new Error('isSameRequirement should prefer stable requirement identity')
}

if (getRequirementIdentity(localRequirement) !== 'REQ-1') {
  throw new Error('getRequirementIdentity should prefer ID over code and title')
}
