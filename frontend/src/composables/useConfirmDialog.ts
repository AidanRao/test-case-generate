import { ref } from 'vue'

type ConfirmOptions = {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void | Promise<void>
}

const useConfirmDialog = () => {
  const confirmVisible = ref(false)
  const confirmTitle = ref('确认操作')
  const confirmMessage = ref('')
  const confirmConfirmText = ref('确定')
  const confirmCancelText = ref('取消')
  const confirmAction = ref<null | (() => void | Promise<void>)>(null)

  const openConfirm = (options: ConfirmOptions) => {
    confirmTitle.value = options.title ?? '确认操作'
    confirmMessage.value = options.message
    confirmConfirmText.value = options.confirmText ?? '确定'
    confirmCancelText.value = options.cancelText ?? '取消'
    confirmAction.value = options.onConfirm
    confirmVisible.value = true
  }

  const handleConfirm = async () => {
    const action = confirmAction.value
    confirmAction.value = null
    if (action) {
      await action()
    }
  }

  const handleCancel = () => {
    confirmAction.value = null
  }

  return {
    confirmVisible,
    confirmTitle,
    confirmMessage,
    confirmConfirmText,
    confirmCancelText,
    openConfirm,
    handleConfirm,
    handleCancel
  }
}

export { useConfirmDialog }
