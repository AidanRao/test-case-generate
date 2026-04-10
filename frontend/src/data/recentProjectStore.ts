export interface RecentProjectEntry {
  projectId: string
  visitedAt: string
}

const recentStorageKey = 'recent-projects'
const canUseStorage = typeof window !== 'undefined' && !!window.localStorage

const loadRecentProjects = (): RecentProjectEntry[] => {
  if (!canUseStorage) {
    return []
  }
  try {
    const raw = localStorage.getItem(recentStorageKey)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return []
    }
    return parsed
      .map((item) => ({
        projectId: typeof item?.projectId === 'string'
          ? item.projectId
          : typeof item?.projectId === 'number'
            ? String(item.projectId)
            : '',
        visitedAt: typeof item?.visitedAt === 'string' ? item.visitedAt : ''
      }))
      .filter((item) => item.projectId && item.visitedAt)
  } catch {
    return []
  }
}

const saveRecentProjects = (entries: RecentProjectEntry[]) => {
  if (!canUseStorage) {
    return
  }
  localStorage.setItem(recentStorageKey, JSON.stringify(entries))
}

const recordProjectVisit = (projectId: string, maxItems = 3): RecentProjectEntry[] => {
  const now = new Date().toISOString()
  const existing = loadRecentProjects().filter((item) => item.projectId !== projectId)
  const updated = [{ projectId, visitedAt: now }, ...existing].slice(0, Math.max(1, maxItems))
  saveRecentProjects(updated)
  return updated
}

export { loadRecentProjects, recordProjectVisit, saveRecentProjects }
