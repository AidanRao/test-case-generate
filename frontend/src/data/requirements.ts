import rawRequirements from '../../requirements.json'

export interface RawRequirement {
  title: string
  type: string
  ID?: string
  code?: string
  content: string
}

export interface ModuleGroup {
  module: string
  requirements: RawRequirement[]
}

export interface Requirement extends RawRequirement {
  module: string
}

const modules = rawRequirements as ModuleGroup[]

const requirements = modules.flatMap((group) =>
  group.requirements.map((item) => ({
    ...item,
    module: group.module
  }))
)

const projectName = '项目需求'

export { modules, requirements, projectName }
