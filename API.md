# API 文档

## 约定

- Base URL：`/api/v1`
- 请求体：`application/json; charset=utf-8`
- 成功响应：`{"code":0,"message":"ok","data":...}`
- 错误响应：`{"code":40001,"message":"参数不合法","data":{}}`

常见错误码：`40001` 参数不合法，`40301` 只读资源不可修改，`40401` 资源不存在，`40901` 资源冲突，`50001` 服务端错误。

测试用例生成相关环境变量：

- `TESTCASE_REQUIREMENT_WORKERS`：单个项目生成任务或集成请求内同时生成的需求数，必须为正整数，默认为 `2`。
- `TESTCASE_JOB_WORKERS`：同时运行的项目生成任务数，默认为 `4`。两个并发配置相互独立。

## 数据结构

### Project

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 项目 ID |
| `code` | string | 项目编号 |
| `title` | string | 项目名称 |
| `source` | `local \| uniportal` | 项目来源 |
| `module_count` | number | 一级功能数，仅列表返回 |
| `requirement_count` | number | 需求数，仅列表返回 |

### Requirement

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 需求 ID |
| `title` | string | 需求标题 |
| `type` | string | 需求类型 |
| `code` | string | 需求编号 |
| `content` | string | 需求内容 |
| `module` | string | 所属模块 |
| `project_id` | string | 项目 ID |
| `testcases` | TestCase[] | 项目详情中返回 |

### TestCase

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 测试用例 ID |
| `requirement_id` | string | 需求 ID |
| `requirement_code` | string | 需求编号 |
| `title` | string | 用例标题 |
| `code` | string | 用例编号 |
| `type` | string | 用例类型 |
| `scenario_type` | string | 用例场景，固定为 `正常流程用例`、`边界条件用例`、`异常场景用例`、`组合场景用例`、`回归测试用例` 之一 |
| `priority` | `P0 \| P1 \| P2 \| P3` | 用例优先级，`P0` 最高，默认为 `P1` |
| `test_steps` | `{step_desc:string, expectation:string}[]` | 测试步骤 |
| `test_target_desc` | string | 测试目标 |
| `verify_method` | string | 验证方法 |

### QualityInfo

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `success_count` | number | 成功处理需求数 |
| `fail_count` | number | 失败处理需求数 |
| `iterations` | number | 生成迭代次数 |
| `duration` | number | 耗时，单位秒 |

### SystemTask

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 任务 ID |
| `name` | string | 任务名称 |
| `description` | string | 任务说明 |
| `enabled` | boolean | 是否启用 |
| `interval_seconds` | number | 执行间隔，5 到 86400 秒 |
| `available` | boolean | 当前是否可执行 |
| `running` | boolean | 定时任务是否运行中 |

## 项目

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/projects?portal_project_id={id}` | 获取项目列表；`portal_project_id` 可选 |
| `POST` | `/projects` | 新建项目 |
| `GET` | `/projects/{projectId}` | 获取项目详情，包含需求和测试用例 |
| `PUT` | `/projects/{projectId}` | 更新项目 `code/title` |
| `DELETE` | `/projects/{projectId}` | 删除项目 |

`POST /projects` body：

```json
{
  "code": "PRJ-001",
  "title": "项目名称",
  "requirements": [
    {
      "module": "模块名称",
      "requirements": [
        {"title": "需求标题", "type": "功能需求", "code": "REQ-001", "content": "需求内容"}
      ]
    }
  ]
}
```

## 需求

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/projects/{projectId}/requirements?module=&type=&keyword=` | 查询需求 |
| `GET` | `/projects/{projectId}/requirements/{requirementId}` | 获取需求详情 |
| `POST` | `/projects/{projectId}/requirements` | 新建需求 |
| `PUT` | `/projects/{projectId}/requirements/{requirementId}` | 更新需求 |
| `DELETE` | `/projects/{projectId}/requirements/{requirementId}` | 删除需求，并删除其测试用例 |
| `POST` | `/projects/{projectId}/requirements/complete` | 需求补全 |

新建/更新需求 body：

```json
{"title":"需求标题","type":"功能需求","code":"REQ-001","content":"需求内容","module":"模块名称"}
```

需求补全 body：

```json
{"scope":"project","requirements":[{"id":"req-id","content":"需求内容"}]}
```

## 测试用例

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/projects/{projectId}/requirements/{requirementId}/testcases` | 查询需求下的测试用例 |
| `POST` | `/projects/{projectId}/testcase-generation-jobs` | 创建测试用例生成任务 |
| `GET` | `/projects/{projectId}/testcase-generation-jobs` | 获取项目当前活动任务或最近一次任务状态 |
| `GET` | `/projects/{projectId}/testcase-generation-jobs/{jobId}` | 获取指定生成任务状态 |
| `PUT` | `/projects/{projectId}/testcases/{testcaseId}` | 更新测试用例 |
| `DELETE` | `/projects/{projectId}/testcases/{testcaseId}` | 删除测试用例 |
| `GET` | `/projects/{projectId}/testcases/export` | 导出 Excel 或 Word 测试报告 |

导出查询参数：

- `format`：必填，支持 `xlsx` 和 `docx`。
- `template_id`：Word 模板标识，缺省为 `default`；仅在 `format=docx` 时使用。

生成 body：

```json
{"requirement_ids":["req-id"],"replace":true,"ai_config":{"api_key":"","base_url":"","model":""}}
```

提交成功返回 HTTP 202 和完整任务状态。同一项目只能有一个活动任务，重复提交返回 HTTP 409。任务状态为 `idle`、`pending`、`running`、`completed` 或 `failed`。

```json
{
  "job_id": "job-id",
  "project_id": "project-id",
  "requirement_ids": ["req-id"],
  "active_requirement_ids": ["req-id"],
  "status": "running",
  "active": true,
  "processing_requirement_ids": ["req-id"],
  "completed_requirement_ids": [],
  "failed_requirement_ids": [],
  "completed_count": 0,
  "failed_count": 0,
  "processed_count": 0,
  "total_count": 1,
  "error": null
}
```

需求级 AI 请求按 `TESTCASE_REQUIREMENT_WORKERS` 并发执行；任一需求生成完成后
会立即映射并保存，用例编号按实际完成和落库顺序分配。单条需求失败不会中断同批次
的其他需求；存在失败时任务最终状态为 `failed`，成功结果仍会保存。

任务状态仅保存在当前后端进程内，服务重启后不会恢复历史任务。

更新测试用例时 `scenario_type` 为必填字段，且必须使用上述五个固定值之一：
`priority` 可设置为 `P0`、`P1`、`P2` 或 `P3`；新生成及未设置优先级的用例默认为 `P1`。

```json
{
  "title": "验证登录成功",
  "code": "TC-PRJ-001",
  "type": "功能测试",
  "scenario_type": "正常流程用例",
  "priority": "P1",
  "test_steps": [{"step_desc": "输入正确账号密码", "expectation": "登录成功"}],
  "test_target_desc": "验证正常登录流程",
  "verify_method": "TESTING"
}
```

### Word 报告模板

`GET /v1/testcase-report-templates`

返回当前注册且模板文件存在的 Word 报告模板：

```json
{"code":0,"message":"ok","data":{"list":[{"template_id":"default","name":"标准测试用例文档"}]}}
```

响应不包含服务器模板路径。Word 导出时把 `template_id` 作为现有
`GET /projects/{projectId}/testcases/export` 的查询参数。

## 质量信息

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/projects/{projectId}/quality` | 获取项目质量信息 |
| `GET` | `/projects/{projectId}/coverage` | 获取最近一次 AI 覆盖率分析结果，尚未计算时 `data` 为 `null` |
| `POST` | `/projects/{projectId}/coverage/calculate` | 提交功能点和接口覆盖率异步计算任务，返回 `202` |
| `GET` | `/projects/{projectId}/coverage/calculation-jobs` | 查询项目最近一次或正在执行的覆盖率计算任务 |
| `GET` | `/projects/{projectId}/coverage/calculation-jobs/{jobId}` | 查询指定覆盖率计算任务 |

返回 `QualityInfo`。测试用例类型统计由前端根据项目详情中的测试用例计算，不由后端返回。

`POST /coverage/calculate` 返回任务状态，前端可轮询
`GET /coverage/calculation-jobs`。状态字段包括 `job_id`、`status`
（`pending`、`running`、`completed` 或 `failed`）、`active`、
`completed_count`、`total_count`、时间字段和 `error`。同一项目同时只允许
一个覆盖率任务，重复提交返回 `409`。服务重启后不会恢复内存中的任务状态，
但已经完整计算并持久化的覆盖率结果不受影响。

AI 会逐条需求分析，项目结果在所有需求均成功后一次性保存。任务失败时保留
上一次结果。结果包含
`feature_point_coverage`、`interface_coverage`、按需求组织的对应明细、
`calculated_at`、`duration` 与 `model`。两类汇总字段均包含 `total`、
`covered` 和 0～1 的 `rate`。

“接口覆盖率”仍按接口参数计数：测试用例明确覆盖参数的合法值、非法值或
边界值至少一种情况时，该参数计为已覆盖。功能点和参数明细中的
`evidence_testcases` 为测试用例引用数组，每项包含 `id`、`code` 和
`title`；接口不保留旧字段或旧证据结构兼容。

## AI 配置

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/ai/config` | 获取 AI 配置 |
| `PUT` | `/ai/config` | 保存 AI 配置 |

`PUT /ai/config` body：

```json
{"api_key":"sk-...","base_url":"https://api.example.com/v1","model":"gpt-4o-mini"}
```

返回字段：`api_key`、`base_url`、`model`、`updated_at`。

## 系统任务

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/system/tasks` | 获取系统任务列表 |
| `PUT` | `/system/tasks/{taskId}` | 更新任务配置 |
| `POST` | `/system/tasks/{taskId}/run` | 立即执行任务 |

更新任务 body：

```json
{"enabled":true,"interval_seconds":30}
```

## 集成生成

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/integration/testcases/generate` | 基于传入需求直接生成测试用例 |

Body：

```json
{
  "format": "json",
  "is_save": true,
  "requirements": [
    {
      "module": "模块名称",
      "requirements": [
        {"id": "req-id", "title": "需求标题", "type": "功能需求", "code": "REQ-001", "content": "需求内容"}
      ]
    }
  ]
}
```

说明：`format` 支持 `json` 和 `md`；`excel` 暂不支持。`is_save` 默认为 `true`，为 `true` 时会创建项目、保存需求、测试用例和质量信息。返回字段为 `quality_info` 与 `test_case`；JSON 用例对象包含 `scenario_type`，Markdown 输出包含“用例场景”。
