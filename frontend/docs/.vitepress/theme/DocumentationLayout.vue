<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'

const { Layout } = DefaultTheme

const returnToApp = () => {
  const appUrl = new URL('/projects', window.location.origin)

  if (import.meta.env.DEV && window.location.port === '5174') {
    appUrl.port = '5173'
  }

  window.location.assign(appUrl.toString())
}
</script>

<template>
  <Layout>
    <template #nav-bar-content-after>
      <button class="app-return-link" type="button" @click="returnToApp">
        返回应用
      </button>
    </template>
  </Layout>
</template>
