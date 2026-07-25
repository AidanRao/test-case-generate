type ProjectCodeEntry = {
  id: string
  code: string
}

const normalizeProjectCode = (code: string) => code.trim().toLowerCase()

const getOccupiedProjectCodes = (
  projects: ProjectCodeEntry[],
  excludedProjectId?: string | null
) =>
  projects
    .filter((project) => project.id !== excludedProjectId)
    .map((project) => project.code)

const isProjectCodeDuplicate = (code: string, occupiedCodes: string[]) => {
  const normalizedCode = normalizeProjectCode(code)
  return occupiedCodes.some(
    (occupiedCode) => normalizeProjectCode(occupiedCode) === normalizedCode
  )
}

export { getOccupiedProjectCodes, isProjectCodeDuplicate }
