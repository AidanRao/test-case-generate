# Vue 3 + TypeScript + Vite

This template should help get you started developing with Vue 3 and TypeScript in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about the recommended Project Setup and IDE Support in the [Vue Docs TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup).

## 知识库显示设置

- 知识库默认隐藏，仅通过设置页底部的“界面显示 → 显示知识库”开关控制，不读取环境变量或构建时配置。
- 开关即时生效，保存到当前浏览器 `localStorage` 的 `knowledge-base-visible`，刷新后保留，不调用后端接口。
- 已有的本地选择继续生效；没有保存值、保存值无效或无法读取本地存储时，默认隐藏。
- 隐藏会同时移除首页的创建按钮、概览、管理标签及面板，不删除 `knowledge-base` 中的本地知识条目，也不改变现有的知识库数据实现。
