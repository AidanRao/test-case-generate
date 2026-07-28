import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import DocumentationLayout from './DocumentationLayout.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout: DocumentationLayout,
} satisfies Theme
