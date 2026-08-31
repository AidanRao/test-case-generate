import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/mcp': {
        target: 'http://localhost:5050',
      },
      '/docs': {
        target: 'http://localhost:5174',
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('element-plus')) {
              return 'element-plus'
            }
            if (id.includes('@antv')) {
              return 'antv'
            }
            return 'vendor'
          }
        },
      },
    },
  },
})
