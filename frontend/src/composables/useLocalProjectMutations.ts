import type { ComputedRef, Ref } from 'vue'
import type { CreateRequirementPayload } from '../api/projects'
import { loadProjects, saveProjects, type ProjectRecord } from '../data/projectStore'
import { isSameRequirement, type RequirementWithTestcases } from './useRequirementTestcases'

type LocalRequirementUpdate = {
  title: string
  type: string
  content: string
  code?: string
  ID?: string
}

type LocalRequirementTarget = RequirementWithTestcases & { module: string }

type UseLocalProjectMutationsOptions = {
  projectId: ComputedRef<string>
  localProjects: Ref<ProjectRecord[]>
}

export const useLocalProjectMutations = ({
  projectId,
  localProjects
}: UseLocalProjectMutationsOptions) => {
  const commitProjectModules = (targetProject: ProjectRecord, modules: ProjectRecord['modules']) => {
    const projects = loadProjects()
    const updatedProjects = projects.map((item) =>
      item.id === targetProject.id
        ? {
            ...item,
            modules,
            moduleCount: modules.length,
            requirementCount: modules.reduce(
              (sum, group) => sum + group.requirements.length,
              0
            )
          }
        : item
    )
    saveProjects(updatedProjects)
    localProjects.value = updatedProjects
  }

  const findProject = () =>
    loadProjects().find((item) => item.id === projectId.value) ?? null

  const createLocalRequirement = (payload: CreateRequirementPayload) => {
    const targetProject = findProject()
    if (!targetProject) return false

    const nextRequirement = {
      ID: `local-req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
      code: payload.code,
      title: payload.title,
      type: payload.type,
      content: payload.content
    }
    const nextModules = targetProject.modules.map((item) => ({
      ...item,
      requirements: [...item.requirements]
    }))
    const targetModule = nextModules.find((item) => item.module === payload.module)
    if (targetModule) {
      targetModule.requirements.push(nextRequirement)
    } else {
      nextModules.push({ module: payload.module, requirements: [nextRequirement] })
    }
    commitProjectModules(targetProject, nextModules)
    return true
  }

  const createLocalModule = (name: string) => {
    const targetProject = findProject()
    if (!targetProject) return false
    if (targetProject.modules.some((item) => item.module === name)) return false

    commitProjectModules(targetProject, [
      ...targetProject.modules.map((item) => ({
        ...item,
        requirements: [...item.requirements]
      })),
      { module: name, requirements: [] }
    ])
    return true
  }

  const deleteLocalRequirement = (moduleName: string, target: LocalRequirementTarget) => {
    const targetProject = findProject()
    if (!targetProject) return false

    let deleted = false
    const nextModules = targetProject.modules.map((group) => {
      if (group.module !== moduleName) {
        return { ...group, requirements: [...group.requirements] }
      }
      const requirements = group.requirements.filter((item) => {
        const matches = isSameRequirement({ ...item, module: group.module }, target)
        deleted ||= matches
        return !matches
      })
      return { ...group, requirements }
    })
    if (!deleted) return false

    commitProjectModules(targetProject, nextModules)
    return true
  }

  const updateLocalRequirement = (
    moduleName: string,
    target: LocalRequirementTarget,
    payload: LocalRequirementUpdate
  ) => {
    const targetProject = findProject()
    if (!targetProject) return false

    let updated = false
    const nextModules = targetProject.modules.map((group) => {
      if (group.module !== moduleName) {
        return { ...group, requirements: [...group.requirements] }
      }
      const requirements = group.requirements.map((item) => {
        if (!isSameRequirement({ ...item, module: group.module }, target)) return item
        updated = true
        return {
          ...item,
          title: payload.title,
          type: payload.type,
          content: payload.content,
          code: payload.code ?? item.code,
          ID: payload.ID ?? item.ID
        }
      })
      return { ...group, requirements }
    })
    if (!updated) return false

    commitProjectModules(targetProject, nextModules)
    return true
  }

  return {
    createLocalRequirement,
    createLocalModule,
    deleteLocalRequirement,
    updateLocalRequirement
  }
}
