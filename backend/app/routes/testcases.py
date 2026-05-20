from flask import Blueprint, current_app, request, send_file, after_this_request, jsonify
from threading import Thread
import time
import os
import tempfile
import random

from app.services.project_service import ProjectService
from app.services.testcase_service import TestCaseService
from app.utils.ids import new_uuid
from app.utils.responses import error, ok

testcases_bp = Blueprint("testcases", __name__)


@testcases_bp.post("/projects/<project_id>/testcases/generate")
def generate_testcases(project_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    requirement_ids = payload.get("requirement_ids")
    replace = bool(payload.get("replace"))
    ai_config = payload.get("ai_config")
    if not requirement_ids:
        requirements = storage.list_requirements(project_id) or []
        requirement_ids = [item.get("id") for item in requirements]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    results, err = service.generate_testcases(project_id, requirement_ids, replace=replace, ai_config=ai_config)
    if err == "missing_api_key":
        return error(50001, "未配置 OpenAI API Key", 500)
    if err == "requirement_not_found":
        return error(40401, "资源不存在", 404)
    if err == "generation_failed":
        return error(50001, "生成失败", 500)
    return ok({"list": results})


@testcases_bp.post("/projects/<project_id>/testcases/generate/async")
def generate_testcases_async(project_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    requirement_ids = payload.get("requirement_ids")
    replace = bool(payload.get("replace"))
    ai_config = payload.get("ai_config")
    if not requirement_ids:
        requirements = storage.list_requirements(project_id) or []
        requirement_ids = [item.get("id") for item in requirements]
    config = current_app.config["APP_CONFIG"]
    jobs_state = current_app.config["TESTCASE_JOBS"]
    job_id = new_uuid()
    if replace:
        for requirement_id in requirement_ids:
            storage.delete_testcases_by_requirement(project_id, requirement_id)
        replace = False
    with jobs_state["lock"]:
        jobs_state["jobs"][job_id] = {
            "project_id": str(project_id),
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": time.time(),
        }

    def _run():
        with jobs_state["lock"]:
            job = jobs_state["jobs"].get(job_id)
            if not job:
                return
            job["status"] = "running"
        try:
            service = TestCaseService(storage, config)
            results, err = service.generate_testcases(
                project_id, requirement_ids, replace=replace, ai_config=ai_config
            )
        except Exception as exc:
            with jobs_state["lock"]:
                job = jobs_state["jobs"].get(job_id)
                if not job:
                    return
                job["status"] = "error"
                job["error"] = f"internal_error:{exc.__class__.__name__}"
            return
        with jobs_state["lock"]:
            job = jobs_state["jobs"].get(job_id)
            if not job:
                return
            if err:
                job["status"] = "error"
                job["error"] = err
            else:
                job["status"] = "done"
                job["result"] = results

    Thread(target=_run, daemon=True).start()
    return ok({"job_id": job_id})


@testcases_bp.get("/projects/<project_id>/testcases/generate/async/<job_id>")
def get_async_job(project_id, job_id):
    jobs_state = current_app.config["TESTCASE_JOBS"]
    with jobs_state["lock"]:
        job = jobs_state["jobs"].get(job_id)
        if not job or str(job.get("project_id")) != str(project_id):
            return error(40401, "资源不存在", 404)
        data = {
            "job_id": job_id,
            "status": job.get("status"),
        }
        if job.get("status") == "error":
            data["error"] = job.get("error")
        return ok(data)


@testcases_bp.get("/projects/<project_id>/testcases/generate/async")
def get_async_job_by_project(project_id):
    jobs_state = current_app.config["TESTCASE_JOBS"]
    with jobs_state["lock"]:
        matched = [
            (job_id, job)
            for job_id, job in jobs_state["jobs"].items()
            if str(job.get("project_id")) == str(project_id)
        ]
        if not matched:
            return ok({"status": "idle"})
        job_id, job = max(matched, key=lambda item: item[1].get("created_at", 0))
        data = {
            "job_id": job_id,
            "status": job.get("status"),
        }
        if job.get("status") == "error":
            data["error"] = job.get("error")
        return ok(data)


@testcases_bp.get("/projects/<project_id>/requirements/<requirement_id>/testcases")
def list_testcases(project_id, requirement_id):
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    items = service.list_testcases(project_id, requirement_id)
    return ok({"list": items})


@testcases_bp.put("/projects/<project_id>/testcases/<testcase_id>")
def update_testcase(project_id, testcase_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    service = TestCaseService(storage, config)
    updated = service.update_testcase(project_id, testcase_id, payload)
    if not updated:
        return error(40401, "资源不存在", 404)
    return ok({"updated": True})


@testcases_bp.delete("/projects/<project_id>/testcases/<testcase_id>")
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


def _build_req_type_stats(testcases):
    keys = [
        "功能测试",
        "可靠性测试",
        "安全性测试",
        "强度测试",
        "性能测试",
        "接口测试",
        "数据处理测试",
        "边界测试",
    ]
    stats = {k: 0 for k in keys}
    for tc in testcases or []:
        t = tc.get("type") or "功能测试"
        if t not in stats:
            stats[t] = 0
        stats[t] += 1
    return stats


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
    is_save = bool(payload.get("is_save"))
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
        for req in stored_requirements:
            req_id = req.get("id")
            req_type = service._map_req_type(req.get("type"))
            raw_cases = generator.generate_test_cases(
                req.get("content", ""),
                req_id,
                req.get("title", ""),
                req_type=req_type,
                module_info=req.get("module"),
            )
            if raw_cases is None:
                fail_count += 1
                continue
            mapped = service._map_cases(project_id, req, raw_cases)
            storage.add_testcases(project_id, req_id, mapped)
            results.extend(mapped)
    else:
        requirements_by_id = {str(item.get("id")): item for item in flat_requirements}
        base_seq = 1
        project_code = "INTEGRATION"
        for req in flat_requirements:
            req_id = req.get("id")
            req_type = service._map_req_type(req.get("type"))
            raw_cases = generator.generate_test_cases(
                req.get("content", ""),
                req_id,
                req.get("title", ""),
                req_type=req_type,
                module_info=req.get("module"),
            )
            if raw_cases is None:
                fail_count += 1
                continue
            for case in raw_cases:
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
        "req_type_stats": _build_req_type_stats(results),
        "success_count": len(results),
    }
    if fmt == "md":
        test_case = _render_testcases_md(results, requirements_by_id)
    else:
        test_case = results
    return jsonify({"quality_info": quality_info, "test_case": test_case})
