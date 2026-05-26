import { modules as defaultModules, projectName, type ModuleGroup, type Requirement } from './requirements'

export type { ModuleGroup, Requirement }

export interface ProjectRecord {
  id: string
  name: string
  code: string
  modules: ModuleGroup[]
  moduleCount?: number
  requirementCount?: number
  source?: 'local' | 'uniportal'
}

const storageKey = 'project-list'

const canUseStorage = typeof window !== 'undefined' && !!window.localStorage

const buildRequirements = (moduleGroups: ModuleGroup[]): Requirement[] =>
  moduleGroups.flatMap((group) =>
    group.requirements.map((item) => ({
      ...item,
      module: group.module
    }))
  )

const getFallbackProjects = (): ProjectRecord[] => [
  {
    id: 'local-1',
    name: projectName,
    code: 'PRJ-001',
    modules: defaultModules,
    source: 'local'
  }
]

const loadProjects = (): ProjectRecord[] => {
  if (!canUseStorage) {
    return getFallbackProjects()
  }
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) {
      return getFallbackProjects()
    }
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return getFallbackProjects()
    }
    const normalized: ProjectRecord[] = parsed.map((item, index) => ({
      id: typeof item?.id === 'string'
        ? item.id
        : typeof item?.id === 'number'
          ? String(item.id)
          : `local-${index + 1}`,
      name: typeof item?.name === 'string' ? item.name : `项目 ${index + 1}`,
      code: typeof item?.code === 'string' ? item.code : `PRJ-${String(index + 1).padStart(3, '0')}`,
      modules: Array.isArray(item?.modules) ? item.modules : [],
      moduleCount: typeof item?.moduleCount === 'number' ? item.moduleCount : undefined,
      requirementCount: typeof item?.requirementCount === 'number' ? item.requirementCount : undefined,
      source: item?.source === 'uniportal' ? 'uniportal' : 'local'
    }))
    return normalized.length > 0 ? normalized : getFallbackProjects()
  } catch {
    return getFallbackProjects()
  }
}

const saveProjects = (projects: ProjectRecord[]) => {
  if (!canUseStorage) {
    return
  }
  localStorage.setItem(storageKey, JSON.stringify(projects))
}

export { buildRequirements, loadProjects, saveProjects }
