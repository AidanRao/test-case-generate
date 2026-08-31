---
title: MCP 使用
description: 通过 AI 客户端查询项目、生成测试用例和分析覆盖率。
---

# MCP 使用

通过 MCP，可以让 AI 客户端直接查询项目和需求、生成测试用例，以及计算覆盖率。

## 连接服务

在支持 **Streamable HTTP** 的 AI 客户端中添加 MCP 服务：

| 配置项 | 填写内容 |
| --- | --- |
| 名称 | `test-case-generate`（可自定义） |
| 传输方式 | Streamable HTTP |
| 地址 | `https://你的域名/mcp` |

例如，网站地址是 `https://test.example.com`，MCP 地址就是 `https://test.example.com/mcp`，不加 `/api/v1` 或 `/docs` 前缀。

使用 `start.sh` 本地启动时，地址为 `http://localhost:5050/mcp`。

支持 `mcpServers` / `url` 格式的客户端可参考以下 `mcp.json`：

```json
{
  "mcpServers": {
    "test-case-generate": {
      "url": "https://test.example.com/mcp"
    }
  }
}
```

[下载示例 JSON 文件](/examples/mcp.json)，将 `url` 替换为实际地址。配置文件的存放位置以客户端要求为准。

## 开始使用

连接成功后，客户端会自动发现可用工具。可以直接对 AI 说：

- “列出当前项目，查看登录模块的需求。”
- “为这个项目的登录需求生成测试用例，保留已有用例。”
- “查询生成任务进度，完成后计算覆盖率并告诉我结果。”

生成和覆盖率计算在后台执行，提交后需要继续查询任务状态，再读取结果。生成默认追加用例，只有明确选择替换时才会覆盖对应需求的已有用例。

## 使用前注意

- 先在网页中准备项目和需求，并配置好服务器使用的 AI 服务。
- MCP 不提供项目、需求的增删改或文件导出，这些操作仍在网页完成。
- 服务默认允许所有 Host 和 Origin，不额外要求访问令牌；请使用现有网络或网关控制访问。
