import { readonly, ref } from 'vue'

export type AppNotificationTone = 'neutral' | 'success' | 'error'
export type AppConfirmTone = 'primary' | 'danger'

export type AppNotification = {
  id: number
  title?: string
  message: string
  tone: AppNotificationTone
}

export type NotifyOptions = {
  title?: string
  message: string
  tone?: AppNotificationTone
  duration?: number
}

export type ConfirmOptions = {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  tone?: AppConfirmTone
}

type ConfirmRequest = Required<Omit<ConfirmOptions, 'title'>> & {
  title: string
  resolve: (value: boolean) => void
}

const notifications = ref<AppNotification[]>([])
const activeConfirm = ref<ConfirmRequest | null>(null)
const confirmQueue: ConfirmRequest[] = []
let notificationId = 0

const dismissNotification = (id: number) => {
  notifications.value = notifications.value.filter((item) => item.id !== id)
}

const notify = (options: NotifyOptions) => {
  const id = ++notificationId
  const duration = options.duration ?? 4000
  notifications.value = [
    ...notifications.value,
    {
      id,
      title: options.title,
      message: options.message,
      tone: options.tone ?? 'neutral'
    }
  ]

  if (duration > 0) {
    window.setTimeout(() => dismissNotification(id), duration)
  }
  return id
}

const showNextConfirm = () => {
  if (activeConfirm.value || confirmQueue.length === 0) {
    return
  }
  activeConfirm.value = confirmQueue.shift() ?? null
}

const confirm = (options: ConfirmOptions) =>
  new Promise<boolean>((resolve) => {
    confirmQueue.push({
      title: options.title ?? '确认操作',
      message: options.message,
      confirmText: options.confirmText ?? '确定',
      cancelText: options.cancelText ?? '取消',
      tone: options.tone ?? 'primary',
      resolve
    })
    showNextConfirm()
  })

const resolveConfirm = (value: boolean) => {
  const current = activeConfirm.value
  if (!current) {
    return
  }
  activeConfirm.value = null
  current.resolve(value)
  window.queueMicrotask(showNextConfirm)
}

const useAppFeedback = () => ({
  notifications: readonly(notifications),
  activeConfirm: readonly(activeConfirm),
  notify,
  dismissNotification,
  confirm,
  resolveConfirm
})

export { useAppFeedback }
