<template>
  <Teleport to="body">
    <div
      class="pointer-events-none fixed left-1/2 top-4 z-[4000] flex w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 flex-col gap-2 sm:bottom-4 sm:left-auto sm:right-4 sm:top-auto sm:w-full sm:translate-x-0"
      aria-live="polite"
      aria-atomic="false"
    >
      <TransitionGroup name="app-toast">
        <div
          v-for="item in notifications"
          :key="item.id"
          class="pointer-events-auto flex items-start gap-3 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-700 shadow-[0_12px_36px_rgba(0,0,0,0.14)]"
          role="status"
        >
          <span
            class="mt-1 h-2 w-2 shrink-0 rounded-full"
            :class="notificationDotClass(item.tone)"
          ></span>
          <div class="min-w-0 flex-1">
            <p v-if="item.title" class="font-semibold text-zinc-950">{{ item.title }}</p>
            <p :class="item.title ? 'mt-0.5' : ''">{{ item.message }}</p>
          </div>
          <button
            type="button"
            class="-mr-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
            aria-label="关闭通知"
            @click="dismissNotification(item.id)"
          >
            ×
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>

  <ConfirmDialog
    v-if="activeConfirm"
    :model-value="true"
    :title="activeConfirm.title"
    :message="activeConfirm.message"
    :confirm-text="activeConfirm.confirmText"
    :cancel-text="activeConfirm.cancelText"
    :tone="activeConfirm.tone"
    @confirm="resolveConfirm(true)"
    @cancel="resolveConfirm(false)"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from './ConfirmDialog.vue'
import { useAppFeedback, type AppNotificationTone } from '../composables/useAppFeedback'

const { notifications, activeConfirm, dismissNotification, resolveConfirm } = useAppFeedback()

const notificationDotClass = (tone: AppNotificationTone) => {
  if (tone === 'success') return 'bg-emerald-500'
  if (tone === 'error') return 'bg-red-500'
  return 'bg-zinc-400'
}
</script>

<style scoped>
.app-toast-enter-active,
.app-toast-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.app-toast-enter-from,
.app-toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
