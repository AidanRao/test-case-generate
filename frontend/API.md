# 后端接口文档设计

本文档面向当前前端项目的真实业务诉求，设计与之匹配的后端接口。接口以 REST 为主，返回统一结构，字段定义与前端展示保持一致，可直接替换现有本地存储与伪生成逻辑。

## 基本约定

- Base URL：`/api/v1`
- Content-Type：`application/json; charset=utf-8`
- 时间格式：ISO8601（例如 `2026-02-05T10:00:00Z`）

### 统一响应结构

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 错误码建议

- `0`：成功
- `40001`：参数不合法
- `40401`：资源不存在
- `40901`：资源冲突（如项目编号重复）
- `50001`：服务器内部错误

## 数据模型

### Project

```json
{
  "id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34",
  "code": "PRJ-001",
  "title": "项目需求"
}
```

### ModuleGroup

```json
{
  "module": "风显示有效性判断",
  "requirements": []
}
```

### Requirement

```json
{
  "id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
  "title": "风向有效性判断",
  "type": "功能需求",
  "code": "SwRD_001",
  "content": "当真实风向和真实航向均有效时，风向有效；当真实风向或真实航向之一为无效时，风向无效。",
  "project_id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34"
}
```

### TestCase

```json
{
  "requirement_code": "REG-3",
  "requirement_id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
  "id": "e0f4a2de-0eab-4b36-8b7a-f5c2d5f6a123",
  "title": "风向有效条件判定",
  "code": "TC-3-006",
  "type": "功能测试",
  "test_steps": [
    {
      "expectation": "加载成功",
      "step_desc": "加载输入接口默认值"
    }
  ],
  "test_target_desc": "验证当真实风向或真实航向任一无效时，风向显示有效性标识 ValidWindMode 被正确置为 0，且在 MFD 模式下显示无效",
  "verify_method": "TESTING"
}
```

### QualityInfo

```json
{
  "success_count": 124,
  "fail_count": 6,
  "iterations": 3,
  "duration": "2m34s",
  "req_type_stats": {
    "功能需求": 12,
    "性能需求": 3
  }
}
```

## 接口清单

### 1. 项目管理

#### 1.1 获取项目列表

`GET /projects`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [
      {
        "id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34",
        "code": "PRJ-001",
        "title": "项目需求",
        "module_count": 3,
        "requirement_count": 18
      }
    ]
  }
}
```

#### 1.2 新建项目

`POST /projects`

**Body**

```json
{
  "code": "PRJ-001",
  "title": "项目需求",
  "requirements": [
    {
      "module": "风显示有效性判断",
      "requirements": [
        {
          "title": "风向有效性判断",
          "type": "功能需求",
          "code": "SwRD_001",
          "content": "..."
        }
      ]
    }
  ]
}
```

**说明**

- 支持在创建项目时携带 `requirements`，后端会自动写入需求

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34"
  }
}
```

#### 1.3 获取项目详情

`GET /projects/{projectId}`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34",
    "code": "PRJ-001",
    "title": "项目需求",
    "requirements": [
      {
        "id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
        "title": "风向有效性判断",
        "type": "功能需求",
        "code": "SwRD_001",
        "content": "...",
        "project_id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34",
        "module": "风显示有效性判断",
        "testcases": [
          {
            "requirement_code": "REG-3",
            "requirement_id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
            "id": "e0f4a2de-0eab-4b36-8b7a-f5c2d5f6a123",
            "title": "风向有效条件判定",
            "code": "TC-3-006",
            "type": "功能测试",
            "test_steps": [
              {
                "expectation": "加载成功",
                "step_desc": "加载输入接口默认值"
              }
            ],
            "test_target_desc": "验证当真实风向或真实航向任一无效时，风向显示有效性标识 ValidWindMode 被正确置为 0，且在 MFD 模式下显示无效",
            "verify_method": "TESTING"
          }
        ]
      }
    ]
  }
}
```

#### 1.4 更新项目

`PUT /projects/{projectId}`

**Body**

```json
{
  "code": "PRJ-001",
  "title": "项目需求"
}
```

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "updated": true
  }
}
```

#### 1.5 删除项目

`DELETE /projects/{projectId}`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "deleted": true
  }
}
```

### 2. 需求管理

#### 2.1 获取需求列表

`GET /projects/{projectId}/requirements`

**Query**

- `module`：可选，按模块名过滤
- `type`：可选，按需求类型过滤
- `keyword`：可选，按标题或内容搜索

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [
      {
        "id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
        "title": "风向有效性判断",
        "type": "功能需求",
        "code": "SwRD_001",
        "content": "...",
        "project_id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34"
      }
    ]
  }
}
```

#### 2.2 获取需求详情

`GET /projects/{projectId}/requirements/{requirementId}`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
    "title": "风向有效性判断",
    "type": "功能需求",
    "code": "SwRD_001",
    "content": "...",
    "project_id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34"
  }
}
```

#### 2.3 更新需求

`PUT /projects/{projectId}/requirements/{requirementId}`

**Body**

```json
{
  "title": "风向有效性判断",
  "type": "功能需求",
  "code": "SwRD_001",
  "content": "...",
  "module": "风显示有效性判断"
}
```

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "updated": true
  }
}
```

#### 2.4 需求补全

`POST /projects/{projectId}/requirements/complete`

**Body**

```json
{
  "requirements": [
    {
      "module": "风显示有效性判断",
      "requirements": [
        {
          "title": "风向有效性判断",
          "type": "功能需求",
          "content": "..."
        }
      ]
    }
  ],
  "scope": "project"
}
```

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "completedRequirements": [
      {
        "module": "风显示有效性判断",
        "requirements": [
          {
            "id": "b2c1d0e9-1234-4abc-9def-0123456789ab",
            "title": "风向无效性判断",
            "type": "功能需求",
            "code": "SwRD_099",
            "content": "...",
            "project_id": "6a1d4f26-7b5b-4f2b-9b0c-0c9f2e2f2f34"
          }
        ]
      }
    ],
    "diff": {
      "addedCount": 1,
      "moduleAdded": ["风显示有效性判断"]
    }
  }
}
```

### 3. 测试用例

#### 3.1 同步生成测试用例

`POST /projects/{projectId}/testcases/generate`

**Body**

可选参数：如果不传 `requirement_ids`，默认生成该项目下所有需求的测试用例
可选参数：`replace` 为 true 时，先删除该需求下已有用例再重新生成（删除后才返回）

```json
{
  "requirement_ids": [
    "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
    "b2c1d0e9-1234-4abc-9def-0123456789ab"
  ],
  "replace": true
}
```

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [
      {
        "requirement_code": "REG-3",
        "requirement_id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
        "id": "e0f4a2de-0eab-4b36-8b7a-f5c2d5f6a123",
        "title": "风向有效条件判定",
        "code": "TC-3-006",
        "type": "功能测试",
        "test_steps": [
          {
            "expectation": "加载成功",
            "step_desc": "加载输入接口默认值"
          }
        ],
        "test_target_desc": "验证当真实风向或真实航向任一无效时，风向显示有效性标识 ValidWindMode 被正确置为 0，且在 MFD 模式下显示无效",
        "verify_method": "TESTING"
      }
    ]
  }
}
```

#### 3.2 异步生成测试用例

`POST /projects/{projectId}/testcases/generate/async`

**Body**

可选参数：如果不传 `requirement_ids`，默认生成该项目下所有需求的测试用例
可选参数：`replace` 为 true 时，先删除该需求下已有用例再重新生成（删除后才返回）

```json
{
  "requirement_ids": [
    "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
    "b2c1d0e9-1234-4abc-9def-0123456789ab"
  ],
  "replace": true
}
```

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "7d2a1a5f-9b2c-4c08-8f67-0a7a1e4c9d10"
  }
}
```

#### 3.3 查询项目异步生成状态

`GET /projects/{projectId}/testcases/generate/async`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "idle"
  }
}
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "7d2a1a5f-9b2c-4c08-8f67-0a7a1e4c9d10",
    "status": "running"
  }
}
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "7d2a1a5f-9b2c-4c08-8f67-0a7a1e4c9d10",
    "status": "done"
  }
}
```

#### 3.4 查询异步生成结果

`GET /projects/{projectId}/testcases/generate/async/{jobId}`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "7d2a1a5f-9b2c-4c08-8f67-0a7a1e4c9d10",
    "status": "pending"
  }
}
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "7d2a1a5f-9b2c-4c08-8f67-0a7a1e4c9d10",
    "status": "done"
  }
}
```

#### 3.5 获取需求下的测试用例

`GET /projects/{projectId}/requirements/{requirementId}/testcases`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [
      {
        "requirement_code": "REG-3",
        "requirement_id": "a3c9e8b6-3c58-4e2d-9e1b-9d9b0e0c0a11",
        "id": "e0f4a2de-0eab-4b36-8b7a-f5c2d5f6a123",
        "title": "风向有效条件判定",
        "code": "TC-3-006",
        "type": "功能测试",
        "test_steps": [
          {
            "expectation": "加载成功",
            "step_desc": "加载输入接口默认值"
          }
        ],
        "test_target_desc": "验证当真实风向或真实航向任一无效时，风向显示有效性标识 ValidWindMode 被正确置为 0，且在 MFD 模式下显示无效",
        "verify_method": "TESTING"
      }
    ]
  }
}
```

#### 3.6 更新测试用例

`PUT /projects/{projectId}/testcases/{testcaseId}`

**Body**

```json
{
  "title": "风向有效条件判定",
  "code": "TC-3-006",
  "type": "功能测试",
  "test_steps": [
    {
      "expectation": "加载成功",
      "step_desc": "加载输入接口默认值"
    }
  ],
  "test_target_desc": "验证当真实风向或真实航向任一无效时，风向显示有效性标识 ValidWindMode 被正确置为 0，且在 MFD 模式下显示无效",
  "verify_method": "TESTING"
}
```

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "updated": true
  }
}
```

#### 3.7 删除测试用例

`DELETE /projects/{projectId}/testcases/{testcaseId}`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "deleted": true
  }
}
```

#### 3.8 导出项目测试用例

`GET /projects/{projectId}/testcases/export`

**Response**

- 文件下载（Excel）
- 按需求分 sheet，每个需求的测试用例在独立 sheet 中

### 4. 质量信息

#### 4.1 获取项目质量信息

`GET /projects/{projectId}/quality`

**Response**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "success_count": 124,
    "fail_count": 6,
    "iterations": 3,
    "duration": "2m34s",
    "req_type_stats": {
      "功能需求": 12,
      "性能需求": 3
    }
  }
}
```
