"""Explicit MCP surface; no Flask request context or internal HTTP calls."""

import json
import logging
from functools import wraps
from inspect import signature
from typing import Annotated

from mcp.server import MCPServer
from mcp_types import CallToolResult, TextContent, ToolAnnotations
from pydantic import StrictBool, StringConstraints

from app.services.coverage_job_manager import CoverageJobManager
from app.services.coverage_service import CoverageService
from app.services.errors import BusinessError
from app.services.project_service import ProjectService
from app.services.quality_service import QualityService
from app.services.requirement_service import RequirementService
from app.services.testcase_job_manager import TestCaseJobManager
from app.services.testcase_service import TestCaseService


logger = logging.getLogger(__name__)
Identifier = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def tool_result(operation):
    """Translate business return values/errors while retaining the tool's input schema."""
    @wraps(operation)
    def wrapped(*args, **kwargs) -> CallToolResult:
        # The SDK runs synchronous tools in its AnyIO thread pool.
        try:
            data = operation(*args, **kwargs)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(data, ensure_ascii=False))],
                structured_content=data,
            )
        except BusinessError as exc:
            data = exc.to_dict()
        except Exception as exc:
            # Do not log exception text: upstream exceptions may contain API keys.
            logger.error("MCP operation %s failed (%s)", operation.__name__, type(exc).__name__)
            data = {"code": 50001, "message": "服务端错误", "data": {}}
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(data, ensure_ascii=False))],
            structured_content=data,
            is_error=True,
        )

    wrapped.__signature__ = signature(operation).replace(return_annotation=CallToolResult)
    return wrapped


def create_mcp_server(
    storage, config, testcase_jobs: TestCaseJobManager, coverage_jobs: CoverageJobManager,
) -> MCPServer:
    projects = ProjectService(storage)
    requirements = RequirementService(storage)
    testcases = TestCaseService(storage, config)
    quality = QualityService(storage)
    coverage = CoverageService(storage, config)
    mcp = MCPServer(
        "test-case-generate",
        instructions="查询项目和需求后提交生成或覆盖率计算任务，再轮询任务状态并读取结果。生成和计算使用服务器已有 AI 配置。",
    )

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def list_projects(keyword: str | None = None, portal_project_id: str | None = None) -> dict:
        """查询项目列表及模块、需求数量；可按关键词或 UniPortal 项目 ID 筛选。"""
        return {"list": projects.list_project_summaries(keyword, portal_project_id)}

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_project(project_id: Identifier) -> dict:
        """查询项目详情，包含需求及已有测试用例。"""
        project = projects.get_project_detail(project_id)
        if project is None:
            raise BusinessError(40401, "资源不存在", 404)
        return project

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def list_requirements(
        project_id: Identifier, module: str | None = None,
        type: str | None = None, keyword: str | None = None,
    ) -> dict:
        """查询项目需求列表；可按模块、需求类型 type 和关键词筛选。"""
        items = requirements.list_requirements(project_id, module, type, keyword)
        if items is None:
            raise BusinessError(40401, "资源不存在", 404)
        return {"list": items}

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_requirement(project_id: Identifier, requirement_id: Identifier) -> dict:
        """查询指定项目下的一条需求。"""
        item = requirements.get_requirement(project_id, requirement_id)
        if not item:
            raise BusinessError(40401, "资源不存在", 404)
        return item

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def list_testcases(project_id: Identifier, requirement_id: Identifier) -> dict:
        """查询指定项目、需求下已有的测试用例。"""
        return {"list": testcases.list_testcases(project_id, requirement_id)}

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=True))
    @tool_result
    def create_testcase_generation_job(
        project_id: Identifier, requirement_ids: list[Identifier] | None = None,
        replace: StrictBool = False,
    ) -> dict:
        """提交用例生成任务，立即返回 job_id；省略 requirement_ids 时生成全部需求。默认追加，replace=true 会在生成成功后替换所选需求的用例。使用服务器 AI 配置，会产生模型调用。"""
        return testcase_jobs.submit(project_id, requirement_ids=requirement_ids, replace=replace)

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_testcase_generation_job(project_id: Identifier, job_id: Identifier) -> dict:
        """按 job_id 查询用例生成任务的进度、完成或失败状态；任务必须属于指定项目。"""
        return testcase_jobs.get_project_job(project_id, job_id)

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_project_testcase_generation_status(project_id: Identifier) -> dict:
        """查询项目当前或最近一次用例生成任务；尚无任务时返回 idle。"""
        return testcase_jobs.get_project_status(project_id)

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_quality(project_id: Identifier) -> dict:
        """查询项目测试用例生成的质量统计。"""
        data = quality.get_quality(project_id)
        if data is None:
            raise BusinessError(40401, "资源不存在", 404)
        return data

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_coverage(project_id: Identifier) -> dict | None:
        """读取已保存的覆盖率分析；尚无有效结果时返回 null，不触发计算。"""
        data, err = coverage.get_coverage(project_id)
        if err == "not_found":
            raise BusinessError(40401, "资源不存在", 404)
        return data

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=True))
    @tool_result
    def calculate_coverage(project_id: Identifier) -> dict:
        """提交覆盖率计算任务，立即返回 job_id；完成后更新保存的分析结果。生成用例期间不可计算，使用服务器 AI 配置，会产生模型调用。"""
        return coverage_jobs.submit(project_id)

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_coverage_calculation_job(project_id: Identifier, job_id: Identifier) -> dict:
        """按 job_id 查询覆盖率计算任务进度及完成或失败状态；任务必须属于指定项目。"""
        return coverage_jobs.get_project_job(project_id, job_id)

    @mcp.tool(annotations=READ_ONLY)
    @tool_result
    def get_project_coverage_calculation_status(project_id: Identifier) -> dict:
        """查询项目当前或最近一次覆盖率计算任务；尚无任务时返回 idle。"""
        return coverage_jobs.get_project_status(project_id)

    return mcp
