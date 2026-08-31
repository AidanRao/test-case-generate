# Vue 3 + TypeScript + Vite

This template should help get you started developing with Vue 3 and TypeScript in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about the recommended Project Setup and IDE Support in the [Vue Docs TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup).

## 知识库显示配置

在 `.env.development` / `.env.production`（或对应的 `.local` 覆盖文件）中配置：

```dotenv
VITE_KNOWLEDGE_BASE_VISIBLE=false
```

- `true` 默认显示，`false` 默认隐藏；未配置时显示，保持现有行为。
- 优先级：系统设置中保存的浏览器本地选择 > 环境变量 > 默认显示。
- 此变量只提供默认值，不是禁用功能的权限开关；设置页始终允许用户重新选择。
- 开发环境修改后重启 Vite；生产环境需重新构建部署，不读取后端运行时环境变量。
- “系统设置 → 界面显示 → 显示知识库”即时生效，保存到 `localStorage` 的 `knowledge-base-visible`，不调用后端接口。清除此项可恢复环境默认值。
- 隐藏会同时移除首页的创建按钮、概览、管理标签及面板，不删除 `knowledge-base` 中的本地知识条目，也不改变现有的知识库数据实现。

显示偏好测试（Node.js 22.18+）：

```sh
node src/composables/useKnowledgeBaseVisibility.test.ts
```
