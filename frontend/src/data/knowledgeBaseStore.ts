import { loadProjects, type ProjectRecord } from './projectStore'

export type KnowledgeStatus = 'draft' | 'published'

export interface KnowledgeBaseItem {
  id: number
  title: string
  tags: string[]
  projectId: string | null
  status: KnowledgeStatus
  summary: string
  content: string
  updatedAt: string
}

const storageKey = 'knowledge-base'
const canUseStorage = typeof window !== 'undefined' && !!window.localStorage

const getDefaultProjectId = (projects: ProjectRecord[]) => (projects.length > 0 ? projects[0]!.id : null)

const getFallbackItems = (): KnowledgeBaseItem[] => {
  const projects = loadProjects()
  const projectId = getDefaultProjectId(projects)
  const now = new Date().toISOString()
  return [
    {
      id: 1,
      title: '登录流程知识点',
      tags: ['登录', '权限'],
      projectId,
      status: 'published',
      summary: '覆盖登录校验、错误提示与安全策略的关键说明。',
      content: '说明登录校验规则、错误提示策略以及常见异常场景。',
      updatedAt: now
    },
    {
      id: 2,
      title: '支付异常处理',
      tags: ['支付', '回退'],
      projectId,
      status: 'draft',
      summary: '支付链路异常处理要点，包含回退策略与日志采集。',
      content: '支付失败、超时、重复回调的处理策略与校验点。',
      updatedAt: now
    }
  ]
}

const normalizeItem = (item: any, index: number): KnowledgeBaseItem => ({
  id: typeof item?.id === 'number' ? item.id : index + 1,
  title: typeof item?.title === 'string' ? item.title : `知识条目 ${index + 1}`,
  tags: Array.isArray(item?.tags) ? item.tags.filter((tag: unknown) => typeof tag === 'string') : [],
  projectId: typeof item?.projectId === 'string'
    ? item.projectId
    : typeof item?.projectId === 'number'
      ? String(item.projectId)
      : null,
  status: item?.status === 'published' ? 'published' : 'draft',
  summary: typeof item?.summary === 'string' ? item.summary : '',
  content: typeof item?.content === 'string' ? item.content : '',
  updatedAt: typeof item?.updatedAt === 'string' ? item.updatedAt : new Date().toISOString()
})

const loadKnowledgeBase = (): KnowledgeBaseItem[] => {
  if (!canUseStorage) {
    return getFallbackItems()
  }
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) {
      return getFallbackItems()
    }
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return getFallbackItems()
    }
    const normalized = parsed.map((item, index) => normalizeItem(item, index))
    return normalized.length > 0 ? normalized : getFallbackItems()
  } catch {
    return getFallbackItems()
  }
}

const saveKnowledgeBase = (items: KnowledgeBaseItem[]) => {
  if (!canUseStorage) {
    return
  }
  localStorage.setItem(storageKey, JSON.stringify(items))
}

export { loadKnowledgeBase, saveKnowledgeBase }
