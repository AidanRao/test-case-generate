import { readonly, ref } from 'vue'

const storageKey = 'knowledge-base-visible'
type VisibilityStorage = Pick<Storage, 'getItem' | 'setItem'>

export const createKnowledgeBaseVisibility = (
  environmentDefault?: string,
  getStorage: () => VisibilityStorage = () => window.localStorage
) => {
  // 未配置时保留现有显示行为；本地选择优先于构建时的环境默认值。
  const defaultVisible = environmentDefault?.trim().toLowerCase() !== 'false'
  const loadVisibility = () => {
    try {
      const saved = getStorage().getItem(storageKey)
      if (saved === 'true' || saved === 'false') {
        return saved === 'true'
      }
    } catch {
      // 浏览器禁用本地存储时仍允许使用环境默认值。
    }
    return defaultVisible
  }

  const knowledgeBaseVisible = ref(loadVisibility())

  const setKnowledgeBaseVisible = (visible: boolean): boolean => {
    knowledgeBaseVisible.value = visible
    try {
      getStorage().setItem(storageKey, String(visible))
      return true
    } catch {
      // 保存失败不影响当前页面，交由设置页提示无法持久保存。
      return false
    }
  }

  return { knowledgeBaseVisible: readonly(knowledgeBaseVisible), setKnowledgeBaseVisible }
}

const visibility = createKnowledgeBaseVisibility(import.meta.env?.VITE_KNOWLEDGE_BASE_VISIBLE)

export const useKnowledgeBaseVisibility = () => visibility
