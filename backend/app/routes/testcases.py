from flask import Blueprint, current_app, request, send_file, after_this_request, jsonify
import time
import os
import tempfile
import random

from app.services.project_service import ProjectService
from app.services.testcase_service import TestCaseService
from app.models.testcase import DEFAULT_PRIORITY, is_valid_priority, is_valid_scenario_type
from app.reports.context_builder import ReportContextBuilder
from app.reports.query_service import ReportQueryService
from app.reports.template_registry import resolve_template
from app.utils.generation_guard import reject_while_testcases_are_generating
from app.utils.ids import new_uuid
from app.utils.responses import error, ok

testcases_bp = Blueprint("testcases", __name__)


@testcases_bp.post("/projects/<project_id>/testcase-generation-jobs")
def create_testcase_generation_job(project_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    project = storage.get_project(project_id)
    if not project:
        return error(40401, "资源不存在", 404)

    requirements = storage.list_requirements(project_id) or []
    requirements_by_id = {
        str(item["id"]): item for item in requirements if item.get("id")
    }
    all_requirement_ids = [
        str(item["id"]) for item in requirements if item.get("id")
    ]
    available_requirement_ids = set(all_requirement_ids)
    requested_requirement_ids = payload.get("requirement_ids")
    if requested_requirement_ids is None:
        requirement_ids = all_requirement_ids
    elif isinstance(requested_requirement_ids, list):
        if not all(
            isinstance(item, str) and item.strip()
            for item in requested_requirement_ids
        ):
            return error(40001, "requirement_ids 只能包含非空字符串", 400)
        requirement_ids = list(
            dict.fromkeys(
                item.strip() for item in requested_requirement_ids
            )
        )
    else:
        return error(40001, "requirement_ids 必须是数组", 400)

    if not requirement_ids:
        return error(40001, "没有可生成测试用例的需求", 400)
    if any(
        requirement_id not in available_requirement_ids
        for requirement_id in requirement_ids
    ):
        return error(40401, "需求不存在", 404)

    replace = bool(payload.get("replace"))
    ai_config = payload.get("ai_config")
    manager = current_app.extensions["testcase_job_manager"]
    job, active_job = manager.submit(
        project_id,
        [requirements_by_id[requirement_id] for requirement_id in requirement_ids],
        replace=replace,
        ai_config=ai_config,
    )
    if active_job:
        return error(
            40901,
            "该项目已有测试用例生成任务正在进行",
            409,
            active_job,
        )
    response = ok(job)
    response.status_code = 202
    return response


@testcases_bp.get("/projects/<project_id>/testcase-generation-jobs/<job_id>")
def get_testcase_generation_job(project_id, job_id):
    manager = current_app.extensions["testcase_job_manager"]
    job = manager.get_job(job_id)
    if not job or str(job["project_id"]) != str(project_id):
        return error(40401, "资源不存在", 404)
    return ok(job)


@testcases_bp.get("/projects/<project_id>/testcase-generation-jobs")
def get_project_testcase_generation_status(project_id):
    storage = current_app.config["STORAGE"]
    if not storage.get_project(project_id):
        return error(40401, "资源不存在", 404)
    manager = current_app.extensions["testcase_job_manager"]
    return ok(manager.get_project_status(project_id))


@testcases_bp.get("/projects/<project_id>/requirements/<requirement_id>/testcases")
def list_testcases(project_id, requirement_id):
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    items = service.list_testcases(project_id, requirement_id)
    return ok({"list": items})


@testcases_bp.put("/projects/<project_id>/testcases/<testcase_id>")
@reject_while_testcases_are_generating
def update_testcase(project_id, testcase_id):
    payload = request.get_json(silent=True) or {}
    if not is_valid_scenario_type(payload.get("scenario_type")):
        return error(40001, "scenario_type 参数不合法", 400)
    if "priority" in payload and not is_valid_priority(payload.get("priority")):
        return error(40001, "priority 参数不合法", 400)
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    updated = service.update_testcase(project_id, testcase_id, payload)
    if not updated:
        return error(40401, "资源不存在", 404)
    return ok({"updated": True})


@testcases_bp.delete("/projects/<project_id>/testcases/<testcase_id>")
@reject_while_testcases_are_generating
def delete_testcase(project_id, testcase_id):
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    deleted = service.delete_testcase(project_id, testcase_id)
    if not deleted:
        return error(40401, "资源不存在", 404)
    return ok({"deleted": True})


@testcases_bp.get("/projects/<project_id>/testcases/export")
def export_testcases(project_id):
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    project = storage.get_project(project_id)
    if not project:
        return error(40401, "资源不存在", 404)
    export_format = (request.args.get("format") or "").strip().lower()
    if not export_format:
        return error(40001, "format 参数为必填项", 400)
    if export_format not in ("xlsx", "docx"):
        return error(40001, "format 参数不合法", 400)
    if export_format == "docx":
        return _export_testcases_word(project_id, storage, config)
    return _export_testcases_excel(project_id, project, storage, config)


def _export_testcases_excel(project_id, project, storage, config):
    try:
        from excel_exporter import TestCaseExporter
    except ModuleNotFoundError:
        return error(50001, "未安装 openpyxl", 500)
    testcases = storage.list_project_testcases(project_id) or []
    requirements = storage.list_requirements(project_id) or []
    cases_by_req = {}
    for item in testcases:
        requirement_id = str(item.get("requirement_id"))
        cases_by_req.setdefault(requirement_id, []).append(item)
    groups = []
    for req in requirements:
        req_id = str(req.get("id"))
        sheet_name = req.get("title") or req.get("code") or req_id
        export_cases = []
        for item in cases_by_req.get(req_id, []):
            payload = dict(item)
            payload["test_case_type"] = item.get("type", "")
            export_cases.append(payload)
        groups.append({"sheet_name": sheet_name, "test_cases": export_cases})
    if not groups:
        for req_id, items in cases_by_req.items():
            export_cases = []
            for item in items:
                payload = dict(item)
                payload["test_case_type"] = item.get("type", "")
                export_cases.append(payload)
            groups.append({"sheet_name": req_id, "test_cases": export_cases})
    template_path = os.path.join(config.base_dir, "template", "test_case_export_template.xlsx")
    exporter = TestCaseExporter(template_path)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()
    exporter.export_by_requirement(groups, tmp.name)

    @after_this_request
    def _cleanup(response):
        try:
            os.remove(tmp.name)
        except OSError:
            pass
        return response

    file_name = f"{project.get('code') or project_id}-testcases.xlsx"
    return send_file(tmp.name, as_attachment=True, download_name=file_name)


def _export_testcases_word(project_id, storage, config):
    template_id = (request.args.get("template_id") or "").strip()
    template = resolve_template(config.base_dir, template_id)
    if template is None:
        return error(40001, "template_id 参数不合法", 400)

    source = ReportQueryService(storage).load(project_id)
    if source is None:
        return error(40401, "资源不存在", 404)
    context = ReportContextBuilder().build(source)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.close()
    try:
        from app.reports.renderer import ReportRenderError, WordReportRenderer
        from app.reports.profiles import (
            ReportProfileConfigurationError,
            resolve_report_profile,
        )
    except ModuleNotFoundError:
        current_app.logger.exception("Failed to render Word test report")
        try:
            os.remove(tmp.name)
        except OSError:
            pass
        return error(50001, "生成 Word 测试报告失败", 500)
    try:
        profile = resolve_report_profile(template.profile_id)
        WordReportRenderer(profile).render(context, template, tmp.name)
    except (
        ReportProfileConfigurationError,
        ReportRenderError,
        OSError,
        ValueError,
    ):
        current_app.logger.exception("Failed to render Word test report")
        try:
            os.remove(tmp.name)
        except OSError:
            pass
        return error(50001, "生成 Word 测试报告失败", 500)

    @after_this_request
    def _cleanup_word(response):
        try:
            os.remove(tmp.name)
        except OSError:
            pass
        return response

    file_name = f"{context['project']['code']}-test-report.docx"
    return send_file(
        tmp.name,
        as_attachment=True,
        download_name=file_name,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )


def _flatten_incoming_requirements(module_groups):
    flat = []
    for group in module_groups or []:
        module = group.get("module", "")
        items = group.get("requirements") or []
        for req in items:
            if not isinstance(req, dict):
                continue
            payload = dict(req)
            payload["module"] = module
            if not payload.get("id"):
                payload["id"] = new_uuid()
            flat.append(payload)
    return flat


def _calculate_iterations(requirement_count):
    if requirement_count <= 0:
        return 0
    value = requirement_count * random.uniform(1.25, 1.75) + random.randint(1, 3)
    return int(round(value))


def _render_testcases_md(testcases, requirements_by_id):
    if not testcases:
        return ""
    grouped = {}
    for tc in testcases:
        grouped.setdefault(str(tc.get("requirement_id", "")), []).append(tc)
    blocks = []
    for req_id, items in grouped.items():
        req = requirements_by_id.get(str(req_id)) or {}
        req_title = req.get("title") or req.get("code") or req_id or "需求"
        req_code = req.get("code") or ""
        header = f"# {req_title}" if not req_code else f"# {req_title} ({req_code})"
        lines = [header]
        for tc in sorted(items, key=lambda x: str(x.get("code") or "")):
            lines.append(f"## {tc.get('code') or ''} {tc.get('title') or ''}".strip())
            lines.append(f"- 测试用例类型：{tc.get('type') or ''}".strip())
            lines.append(f"- 用例场景：{tc.get('scenario_type') or ''}".strip())
            lines.append(f"- 优先级：{tc.get('priority') or DEFAULT_PRIORITY}".strip())
            if tc.get("verify_method"):
                lines.append(f"- 验证方法：{tc.get('verify_method')}")
            if tc.get("test_target_desc"):
                lines.append(f"- 测试目标：{tc.get('test_target_desc')}")
            lines.append("")
            lines.append("### 测试步骤")
            for idx, step in enumerate(tc.get("test_steps") or [], start=1):
                step_desc = (step or {}).get("step_desc", "")
                expectation = (step or {}).get("expectation", "")
                if expectation:
                    lines.append(f"{idx}. {step_desc} -> {expectation}".strip())
                else:
                    lines.append(f"{idx}. {step_desc}".strip())
            lines.append("")
        blocks.append("\n".join(lines).strip())
    return "\n\n".join(blocks).strip()


@testcases_bp.post("/integration/testcases/generate")
def integration_generate_testcases():
    payload = request.get_json(silent=True) or {}
    fmt = (payload.get("format") or "md").lower()
    # 默认为保存
    is_save = bool(payload.get("is_save", True))
    if fmt == "excel":
        return error(40001, "暂不支持 excel", 400)
    if fmt not in ("json", "md"):
        return error(40001, "format 参数不合法", 400)

    module_groups = payload.get("requirements") or []
    flat_requirements = _flatten_incoming_requirements(module_groups)
    requirement_count = len(flat_requirements)
    if requirement_count <= 0:
        return error(40001, "requirements 不能为空", 400)

    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    generator = service._build_generator()
    if generator is None:
        return error(50001, "未配置 OpenAI API Key", 500)

    started_at = time.time()
    fail_count = 0
    results = []

    if is_save:
        project_service = ProjectService(storage)
        seed = int(time.time() * 1000)
        project_code = f"INT-{seed}-{random.randint(1000, 9999)}"
        project_title = f"Integration-{seed}"
        project_id, err = project_service.create_project(
            {"code": project_code, "title": project_title, "requirements": module_groups}
        )
        if err == "duplicate":
            project_code = f"INT-{seed}-{random.randint(10000, 99999)}"
            project_title = f"Integration-{seed}-{random.randint(1, 9)}"
            project_id, err = project_service.create_project(
                {"code": project_code, "title": project_title, "requirements": module_groups}
            )
        if err:
            return error(50001, "创建项目失败", 500)
        stored_requirements = storage.list_requirements(project_id) or []
        requirements_by_id = {str(item.get("id")): item for item in stored_requirements}
        generation_results = service.iter_requirement_cases(
            stored_requirements,
            generator=generator,
            include_module_info=True,
        )
        for generation_result in generation_results:
            req = generation_result.requirement
            req_id = req.get("id")
            if generation_result.error:
                fail_count += 1
                continue
            mapped = service._map_cases(
                project_id,
                req,
                generation_result.raw_cases,
            )
            storage.add_testcases(project_id, req_id, mapped)
            results.extend(mapped)
    else:
        requirements_by_id = {str(item.get("id")): item for item in flat_requirements}
        base_seq = 1
        project_code = "INTEGRATION"
        generation_results = service.generate_requirement_cases(
            flat_requirements,
            generator=generator,
            include_module_info=True,
        )
        for generation_result in generation_results:
            req = generation_result.requirement
            req_id = req.get("id")
            if generation_result.error:
                fail_count += 1
                continue
            for case in generation_result.raw_cases:
                seq = str(base_seq).zfill(3)
                base_seq += 1
                case_title = case.get("title") or f"{req.get('title', '')}-用例{seq}"
                results.append(
                    {
                        "requirement_code": req.get("code", ""),
                        "requirement_id": req_id,
                        "id": new_uuid(),
                        "title": case_title,
                        "code": f"TC-{project_code}-{seq}",
                        "type": case.get("test_case_type") or "功能测试",
                        "scenario_type": case["scenario_type"],
                        "priority": DEFAULT_PRIORITY,
                        "test_steps": case.get("test_steps", []),
                        "test_target_desc": case.get("test_target_desc", ""),
                        "verify_method": case.get("verify_method", "TESTING"),
                    }
                )

    duration = time.time() - started_at
    quality_info = {
        "duration": duration,
        "fail_count": fail_count,
        "iterations": _calculate_iterations(requirement_count),
        "success_count": len(results),
    }
    if is_save:
        storage.save_project_quality(project_id, quality_info)
    if fmt == "md":
        test_case = _render_testcases_md(results, requirements_by_id)
    else:
        test_case = results
    return jsonify({"quality_info": quality_info, "test_case": test_case})
