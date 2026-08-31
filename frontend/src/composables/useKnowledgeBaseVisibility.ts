import { readonly, ref } from 'vue'

const storageKey = 'knowledge-base-visible'

const loadVisibility = (): boolean => {
  try {
    return window.localStorage.getItem(storageKey) === 'true'
  } catch {
    // 未保存有效选择或无法读取本地存储时，默认隐藏。
    return false
  }
}

const knowledgeBaseVisible = ref(loadVisibility())

const setKnowledgeBaseVisible = (visible: boolean): boolean => {
  knowledgeBaseVisible.value = visible
  try {
    window.localStorage.setItem(storageKey, String(visible))
    return true
  } catch {
    // 保存失败不影响当前页面，交由设置页提示无法持久保存。
    return false
  }
}

export const useKnowledgeBaseVisibility = () => ({
  knowledgeBaseVisible: readonly(knowledgeBaseVisible),
  setKnowledgeBaseVisible
})
