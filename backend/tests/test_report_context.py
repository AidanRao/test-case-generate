from datetime import date
import unittest

from app.reports.context_builder import ReportContextBuilder


SOURCE = {
    "project": {"id": "p-1", "code": "PRJ-01", "title": "示例系统"},
    "requirements": [
        {
            "id": "r-1",
            "code": "REQ-001",
            "title": "用户登录",
            "type": "功能需求",
            "content": "账号密码登录",
            "module": "认证",
        },
        {
            "id": "r-2",
            "code": "REQ-002",
            "title": "用户注册",
            "type": "功能需求",
            "content": "注册新账号",
            "module": "认证",
        },
        {
            "id": "r-3",
            "code": "REQ-003",
            "title": "审计记录",
            "type": "",
            "content": "",
            "module": "审计",
        },
    ],
    "testcases": [
        {
            "id": "tc-1",
            "requirement_id": "r-1",
            "code": "TC-LOGIN-001",
            "title": "登录成功",
            "type": "功能测试",
            "scenario_type": "正常流程用例",
            "priority": "P0",
            "test_steps": [],
        },
        {
            "id": "tc-2",
            "requirement_id": "r-1",
            "code": "TC-LOGIN-002",
            "title": "密码错误",
            "type": "安全性测试",
            "scenario_type": "异常场景用例",
            "priority": "",
            "test_steps": [],
        },
        {
            "id": "tc-3",
            "requirement_id": "r-2",
            "code": "TC-REGISTER-001",
            "title": "注册成功",
            "type": "功能测试",
            "scenario_type": "正常流程用例",
            "priority": "P1",
            "test_steps": [],
        },
    ],
}


class ReportContextBuilderTest(unittest.TestCase):
    def setUp(self):
        self.context = ReportContextBuilder(
            today_provider=lambda: date(2026, 7, 25)
        ).build(SOURCE)

    def test_builds_document_metadata_and_grouped_requirement_summary(self):
        self.assertEqual(
            self.context["metadata"],
            {
                "project_name": "示例系统",
                "version": "V1.0",
                "compiled_date": "2026-07-25",
            },
        )
        self.assertEqual(
            self.context["summary"]["requirement_groups"],
            [
                {
                    "module": "认证",
                    "requirements": [
                        {
                            "code": "REQ-001",
                            "title": "用户登录",
                            "type": "功能需求",
                            "testcase_count": 2,
                        },
                        {
                            "code": "REQ-002",
                            "title": "用户注册",
                            "type": "功能需求",
                            "testcase_count": 1,
                        },
                    ],
                },
                {
                    "module": "审计",
                    "requirements": [
                        {
                            "code": "REQ-003",
                            "title": "审计记录",
                            "type": "未知类型",
                            "testcase_count": 0,
                        }
                    ],
                },
            ],
        )

    def test_calculates_case_type_priority_and_coverage_summaries(self):
        self.assertEqual(
            self.context["summary"]["case_type_stats"],
            [
                {"name": "功能测试", "count": 2, "percentage": "66.67%"},
                {"name": "安全性测试", "count": 1, "percentage": "33.33%"},
            ],
        )
        self.assertEqual(
            self.context["summary"]["priority_stats"],
            [
                {"name": "P0", "count": 1, "percentage": "33.33%"},
                {"name": "P1", "count": 2, "percentage": "66.67%"},
            ],
        )
        self.assertEqual(
            self.context["summary"]["coverage"],
            [
                {
                    "code": "REQ-001",
                    "title": "用户登录",
                    "testcase_codes": "TC-LOGIN-001、TC-LOGIN-002",
                    "testcase_count": 2,
                    "status": "已覆盖",
                },
                {
                    "code": "REQ-002",
                    "title": "用户注册",
                    "testcase_codes": "TC-REGISTER-001",
                    "testcase_count": 1,
                    "status": "已覆盖",
                },
                {
                    "code": "REQ-003",
                    "title": "审计记录",
                    "testcase_codes": "暂无",
                    "testcase_count": 0,
                    "status": "未覆盖",
                },
            ],
        )

    def test_empty_project_has_empty_statistics_without_division_by_zero(self):
        context = ReportContextBuilder(
            today_provider=lambda: date(2026, 7, 25)
        ).build(
            {
                "project": {"id": "p-empty", "code": "EMPTY", "title": ""},
                "requirements": [],
                "testcases": [],
            }
        )

        self.assertNotIn("document_name", context["metadata"])
        self.assertEqual(context["metadata"]["project_name"], "EMPTY")
        self.assertEqual(context["modules"], [])
        self.assertEqual(
            context["summary"],
            {
                "requirement_groups": [],
                "case_type_stats": [],
                "priority_stats": [],
                "coverage": [],
            },
        )


if __name__ == "__main__":
    unittest.main()
