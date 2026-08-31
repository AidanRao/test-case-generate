import json
import os
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from starlette.testclient import TestClient

from app.asgi import create_asgi_app
from app.services.testcase_service import TestCaseService
from app.services.coverage_service import CoverageService


TOOL_NAMES = {
    "list_projects", "get_project", "list_requirements", "get_requirement",
    "list_testcases", "create_testcase_generation_job", "get_testcase_generation_job",
    "get_project_testcase_generation_status", "get_quality", "get_coverage",
    "calculate_coverage", "get_coverage_calculation_job", "get_project_coverage_calculation_status",
}
HEADERS = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"}


class FakeGenerator:
    def __init__(self, fail_ids=(), release=None):
        self.fail_ids = set(fail_ids)
        self.release = release

    def generate_test_cases(self, requirement_content, item_id, item_title, **kwargs):
        if self.release is not None and not self.release.wait(3):
            raise TimeoutError("test generator not released")
        if item_id in self.fail_ids:
            raise RuntimeError("private-upstream-token")
        return [{
            "title": "新生成用例", "test_case_type": "功能测试", "scenario_type": "正常流程用例",
            "test_steps": [{"step_desc": "登录", "expectation": "成功"}],
        }]


class MCPIntegrationTest(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch.dict(os.environ, {
            "DATA_DIR": directory, "UNIPORTAL_SYNC_ENABLED": "false",
        }))
        self.app = create_asgi_app()
        self.flask = self.app.state.flask_app
        self.storage = self.flask.config["STORAGE"]
        self.client = self.enterContext(TestClient(self.app, base_url="http://localhost"))
        self.project_id = self.create_project("MCP", 2)
        self.requirements = self.storage.list_requirements(self.project_id)
        self.ids = [item["id"] for item in self.requirements]

    def create_project(self, code, count):
        response = self.client.post("/v1/projects", json={
            "code": code, "title": code,
            "requirements": [{"module": "登录", "requirements": [
                {"code": f"REQ-{index}", "title": f"需求{index}", "content": "用户可以登录", "type": "功能需求"}
                for index in range(count)
            ]}],
        })
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]["id"]

    def rpc(self, method, params):
        response = self.client.post("/mcp", headers=HEADERS, json={
            "jsonrpc": "2.0", "id": 1, "method": method, "params": params,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("location", response.headers)
        return response.json()

    def call(self, name, **arguments):
        envelope = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.assertNotIn("error", envelope, envelope)
        return envelope["result"]

    def data(self, name, **arguments):
        result = self.call(name, **arguments)
        self.assertFalse(result.get("isError"), result)
        text = json.loads(result["content"][0]["text"])
        self.assertEqual(result.get("structuredContent"), text)
        return text

    def assert_business_error(self, code, name, **arguments):
        result = self.call(name, **arguments)
        self.assertTrue(result["isError"])
        self.assertEqual(result["structuredContent"]["code"], code)
        return result["structuredContent"]

    def wait_job(self, job, coverage=False):
        tool = "get_coverage_calculation_job" if coverage else "get_testcase_generation_job"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            status = self.data(tool, project_id=job["project_id"], job_id=job["job_id"])
            if not status["active"]:
                return status
            time.sleep(0.01)
        self.fail("job did not finish")

    def test_initialize_discovery_and_exact_path(self):
        result = self.rpc("initialize", {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "mcp-test", "version": "1"},
        })["result"]
        self.assertIn("tools", result["capabilities"])
        notification = self.client.post("/mcp", headers=HEADERS, json={
            "jsonrpc": "2.0", "method": "notifications/initialized",
        })
        self.assertEqual(notification.status_code, 202)
        tools = self.rpc("tools/list", {})["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, TOOL_NAMES)
        for tool in tools:
            self.assertTrue(tool["description"])
            if tool["name"] == "create_testcase_generation_job":
                properties = tool["inputSchema"]["properties"]
                self.assertEqual(set(properties), {"project_id", "requirement_ids", "replace"})
                self.assertFalse(properties["replace"]["default"])
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        for path in ("/mcp/mcp", "/api/mcp", "/mcp/"):
            response = self.client.post(path, json={}, follow_redirects=False)
            self.assertEqual(response.status_code, 404)

    def test_query_results_match_rest(self):
        project = self.project_id
        requirement = self.ids[0]
        queries = [
            ("list_projects", {}, "/v1/projects"),
            ("get_project", {"project_id": project}, f"/v1/projects/{project}"),
            ("list_requirements", {"project_id": project, "type": "功能需求", "module": "登录"},
             f"/v1/projects/{project}/requirements?type=功能需求&module=登录"),
            ("get_requirement", {"project_id": project, "requirement_id": requirement},
             f"/v1/projects/{project}/requirements/{requirement}"),
            ("list_testcases", {"project_id": project, "requirement_id": requirement},
             f"/v1/projects/{project}/requirements/{requirement}/testcases"),
            ("get_quality", {"project_id": project}, f"/v1/projects/{project}/quality"),
            ("get_coverage", {"project_id": project}, f"/v1/projects/{project}/coverage"),
            ("get_project_testcase_generation_status", {"project_id": project},
             f"/v1/projects/{project}/testcase-generation-jobs"),
            ("get_project_coverage_calculation_status", {"project_id": project},
             f"/v1/projects/{project}/coverage/calculation-jobs"),
        ]
        for name, arguments, path in queries:
            with self.subTest(tool=name):
                self.assertEqual(self.data(name, **arguments), self.client.get(path).json()["data"])

    def test_invalid_arguments_and_missing_resources_do_not_submit_jobs(self):
        for arguments in ({}, {"project_id": " "}, {"project_id": 12},
                          {"project_id": self.project_id, "replace": "false"},
                          {"project_id": self.project_id, "requirement_ids": [12]}):
            envelope = self.rpc("tools/call", {"name": "create_testcase_generation_job", "arguments": arguments})
            self.assertTrue("error" in envelope or envelope.get("result", {}).get("isError"), envelope)
        self.assert_business_error(40401, "get_project", project_id="missing")
        self.assert_business_error(40401, "create_testcase_generation_job", project_id="missing")
        self.assert_business_error(40001, "create_testcase_generation_job", project_id=self.project_id, requirement_ids=[])
        other = self.create_project("OTHER", 1)
        foreign_id = self.storage.list_requirements(other)[0]["id"]
        self.assert_business_error(40401, "create_testcase_generation_job", project_id=self.project_id, requirement_ids=[foreign_id])
        empty = self.create_project("EMPTY", 0)
        self.assert_business_error(40001, "calculate_coverage", project_id=empty)
        self.assert_business_error(40001, "create_testcase_generation_job", project_id=empty)
        self.assertEqual(self.data("get_project_testcase_generation_status", project_id=self.project_id)["status"], "idle")

    def test_rest_submission_is_visible_and_conflicts_through_mcp(self):
        release = Event()
        with patch.object(TestCaseService, "_build_generator", return_value=FakeGenerator(release=release)):
            try:
                response = self.client.post(f"/v1/projects/{self.project_id}/testcase-generation-jobs", json={})
                self.assertEqual(response.status_code, 202)
                job = response.json()["data"]
                self.assertTrue(self.data("get_testcase_generation_job", project_id=self.project_id, job_id=job["job_id"])["active"])
                conflict = self.assert_business_error(40901, "create_testcase_generation_job", project_id=self.project_id)
                self.assertEqual(conflict["data"]["job_id"], job["job_id"])
                self.assert_business_error(40902, "calculate_coverage", project_id=self.project_id)
                self.assert_business_error(40401, "get_testcase_generation_job", project_id="other", job_id=job["job_id"])
                self.assertEqual(self.client.put(f"/v1/projects/{self.project_id}", json={"title": "blocked"}).status_code, 409)
            finally:
                release.set()
            self.assertEqual(self.wait_job(job)["status"], "completed")

    def test_mcp_generation_appends_and_is_visible_through_rest(self):
        self.storage.add_testcases(self.project_id, self.ids[0], [{"id": "existing", "title": "旧用例", "scenario_type": "正常流程用例"}])
        with patch.object(TestCaseService, "_build_generator", return_value=FakeGenerator()):
            job = self.data("create_testcase_generation_job", project_id=self.project_id,
                            requirement_ids=[self.ids[0], self.ids[0]])
            self.assertEqual(job["requirement_ids"], [self.ids[0]])
            self.assertEqual(self.wait_job(job)["status"], "completed")
        response = self.client.get(f"/v1/projects/{self.project_id}/testcase-generation-jobs/{job['job_id']}")
        self.assertEqual(response.json()["data"]["job_id"], job["job_id"])
        cases = self.data("list_testcases", project_id=self.project_id, requirement_id=self.ids[0])["list"]
        self.assertEqual(len(cases), 2)
        self.assertIn("existing", [case["id"] for case in cases])
        with patch.object(TestCaseService, "_build_generator", return_value=FakeGenerator()):
            job = self.data("create_testcase_generation_job", project_id=self.project_id,
                            requirement_ids=[self.ids[0]], replace=True)
            self.assertEqual(self.wait_job(job)["status"], "completed")
        cases = self.data("list_testcases", project_id=self.project_id, requirement_id=self.ids[0])["list"]
        self.assertEqual(len(cases), 1)
        self.assertNotEqual(cases[0]["id"], "existing")

    def test_partial_failure_keeps_failed_requirement_existing_cases(self):
        self.storage.add_testcases(self.project_id, self.ids[0], [{"id": "existing", "title": "旧用例", "scenario_type": "正常流程用例"}])
        with patch.object(TestCaseService, "_build_generator", return_value=FakeGenerator(fail_ids=[self.ids[0]])):
            job = self.data("create_testcase_generation_job", project_id=self.project_id, replace=True)
            status = self.wait_job(job)
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["completed_count"], 1)
        self.assertEqual(status["failed_requirement_ids"], [self.ids[0]])
        self.assertNotIn("private-upstream-token", json.dumps(status))
        self.assertEqual(self.data("list_testcases", project_id=self.project_id, requirement_id=self.ids[0])["list"][0]["id"], "existing")
        self.assertEqual(len(self.data("list_testcases", project_id=self.project_id, requirement_id=self.ids[1])["list"]), 1)

    def test_missing_ai_configuration_is_reported_as_failed_job(self):
        with patch.object(TestCaseService, "_build_generator", return_value=None):
            job = self.data("create_testcase_generation_job", project_id=self.project_id)
            status = self.wait_job(job)
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["error"], "missing_api_key")

    def test_coverage_jobs_and_results_are_shared(self):
        release = Event()
        saved = {"schema_version": 3, "feature_coverage": 100}

        def calculate(service, project_id, on_requirement_completed=None):
            if not release.wait(3):
                raise TimeoutError("coverage not released")
            for requirement_id in self.ids:
                on_requirement_completed(requirement_id)
            return service.storage.save_project_coverage(project_id, saved)

        with patch.object(CoverageService, "calculate_coverage", calculate):
            try:
                job = self.data("calculate_coverage", project_id=self.project_id)
                path = f"/v1/projects/{self.project_id}/coverage/calculation-jobs/{job['job_id']}"
                self.assertTrue(self.client.get(path).json()["data"]["active"])
                conflict = self.assert_business_error(40903, "calculate_coverage", project_id=self.project_id)
                self.assertEqual(conflict["data"]["job_id"], job["job_id"])
                self.assert_business_error(40401, "get_coverage_calculation_job", project_id="other", job_id=job["job_id"])
                self.assertEqual(self.client.post(f"/v1/projects/{self.project_id}/coverage/calculate").status_code, 409)
            finally:
                release.set()
            self.assertEqual(self.wait_job(job, coverage=True)["status"], "completed")
            response = self.client.post(f"/v1/projects/{self.project_id}/coverage/calculate")
            self.assertEqual(response.status_code, 202)
            self.assertEqual(self.wait_job(response.json()["data"], coverage=True)["status"], "completed")
        self.assertEqual(self.data("get_coverage", project_id=self.project_id), saved)
        self.assertEqual(self.client.get(f"/v1/projects/{self.project_id}/coverage").json()["data"], saved)

    def test_internal_errors_are_sanitized(self):
        with patch.object(self.storage, "get_project", side_effect=RuntimeError("secret-api-key")):
            with self.assertLogs("app.mcp_tools", level="ERROR") as logs:
                result = self.assert_business_error(50001, "get_project", project_id=self.project_id)
        self.assertNotIn("secret-api-key", json.dumps(result) + "".join(logs.output))

    def test_any_host_and_origin_are_allowed_without_configuration(self):
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        for extra_headers in [
            {"Host": "test.example.com", "Origin": "https://test.example.com"},
            {"Host": "another.example:8080", "Origin": "https://client.example"},
            {"Host": "192.0.2.10:9000"},
            {"Origin": "null"},
        ]:
            response = self.client.post("/mcp", headers={**HEADERS, **extra_headers}, json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual({tool["name"] for tool in response.json()["result"]["tools"]}, TOOL_NAMES)
            if "Origin" in extra_headers:
                self.assertEqual(response.headers["access-control-allow-origin"], "*")
        response = self.client.options("/mcp", headers={
            "Origin": "https://client.example", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,mcp-protocol-version,mcp-session-id",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "*")
        self.assertIn("mcp-protocol-version", response.headers["access-control-allow-headers"])

    def test_sync_tool_does_not_block_event_loop(self):
        entered, release = Event(), Event()
        original = self.storage.list_projects

        def slow(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("read not released")
            return original(*args, **kwargs)

        with patch.object(self.storage, "list_projects", side_effect=slow), ThreadPoolExecutor() as executor:
            future = executor.submit(self.data, "list_projects")
            try:
                self.assertTrue(entered.wait(1))
                health = executor.submit(self.client.get, "/health")
                self.assertEqual(health.result(timeout=1).status_code, 200)
            finally:
                release.set()
            self.assertTrue(future.result(timeout=1)["list"])

    def test_shutdown_closes_shared_managers(self):
        self.client.__exit__(None, None, None)
        self.assertFalse(self.flask.extensions["system_task_manager"].scheduler.running)
        for name in ("testcase_job_manager", "coverage_job_manager"):
            self.assertTrue(self.flask.extensions[name]._executor._shutdown)


if __name__ == "__main__":
    unittest.main()
