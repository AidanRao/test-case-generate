<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DefaultTheme from 'vitepress/theme'

const { Layout } = DefaultTheme
const appHomeUrl = ref('/projects')

onMounted(() => {
  if (!import.meta.env.DEV || window.location.port !== '5174') {
    return
  }

  const appUrl = new URL('/projects', window.location.origin)
  appUrl.port = '5173'
  appHomeUrl.value = appUrl.toString()
})
</script>

<template>
  <Layout>
    <template #nav-bar-content-after>
      <a class="app-return-link" :href="appHomeUrl">
        返回应用
      </a>
    </template>
  </Layout>
</template>
