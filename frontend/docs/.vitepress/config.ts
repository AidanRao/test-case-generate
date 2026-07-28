import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-CN',
  title: '测试用例智能生成工具',
  description: '测试用例智能生成工具使用文档',
  base: '/docs/',
  cleanUrls: true,
  // Docker 构建镜像中不包含 Git，关闭基于提交记录的更新时间计算。
  lastUpdated: false,
  outDir: '../dist/docs',

  head: [
    ['meta', { name: 'theme-color', content: '#0284c7' }],
  ],

  themeConfig: {
    siteTitle: '使用文档',
    nav: [
      { text: '指南', link: '/guide/getting-started' },
      { text: '项目管理', link: '/guide/project-management' },
      { text: '需求与用例', link: '/guide/requirements-and-testcases' },
    ],
    sidebar: [
      {
        text: '开始使用',
        items: [
          { text: '快速开始', link: '/guide/getting-started' },
          { text: '项目管理', link: '/guide/project-management' },
        ],
      },
      {
        text: '功能指南',
        items: [
          { text: '需求与测试用例', link: '/guide/requirements-and-testcases' },
          { text: '系统设置', link: '/guide/settings' },
        ],
      },
    ],
    outline: {
      level: [2, 3],
      label: '本页目录',
    },
    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档',
          },
          modal: {
            noResultsText: '未找到相关内容',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
      },
    },
    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '返回顶部',
    langMenuLabel: '切换语言',
  },
})
