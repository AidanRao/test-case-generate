import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.reports.template_registry import (
    available_templates,
    resolve_template,
)


class ReportTemplateRegistryTest(unittest.TestCase):
    def test_resolves_default_template_name_code_and_path(self):
        with tempfile.TemporaryDirectory() as base_dir:
            template_dir = os.path.join(base_dir, "template")
            os.makedirs(template_dir)
            template_path = os.path.join(
                template_dir,
                "test_case_report.docx",
            )
            Path(template_path).touch()

            template = resolve_template(base_dir, "default")

            self.assertEqual(template.template_id, "default")
            self.assertEqual(template.name, "标准测试用例文档")
            self.assertEqual(template.path, template_path)
            self.assertEqual(
                available_templates(base_dir),
                (
                    {
                        "template_id": "default",
                        "name": "标准测试用例文档",
                    },
                ),
            )

    def test_catalog_filters_registered_template_with_missing_file(self):
        with tempfile.TemporaryDirectory() as base_dir:
            os.makedirs(os.path.join(base_dir, "template"))

            self.assertEqual(available_templates(base_dir), ())


class ReportTemplateApiTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        environment = patch.dict(
            os.environ,
            {
                "DATA_DIR": self.tmpdir.name,
                "UNIPORTAL_SYNC_ENABLED": "false",
            },
            clear=False,
        )
        environment.start()
        self.addCleanup(environment.stop)

        from app import create_app

        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_lists_available_templates_without_server_path(self):
        response = self.client.get("/v1/testcase-report-templates")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(
            payload["data"]["list"],
            [
                {
                    "template_id": "default",
                    "name": "标准测试用例文档",
                }
            ],
        )
        self.assertNotIn("path", payload["data"]["list"][0])
        self.assertNotIn("filename", payload["data"]["list"][0])


if __name__ == "__main__":
    unittest.main()
