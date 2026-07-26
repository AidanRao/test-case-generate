import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from openai import OpenAI


class CoverageAnalysisError(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class CoverageService:
    MAX_WORKERS = 4
    SYSTEM_PROMPT = """你是一名严谨的软件测试覆盖率分析专家。
请根据一条需求和它已有的测试用例，识别并评估两类覆盖率：
1. 功能点覆盖率：从每条需求中拆分出可独立验证的用户能力、业务分支或系统行为。只有测试用例明确验证该功能点时才算覆盖。
2. 接口覆盖率：识别需求中明确出现的接口及其参数。覆盖率仍按参数计数；只有测试用例明确针对某参数的合法值、非法值或边界值至少一种情况进行验证时，该参数才算覆盖。

不得把仅在需求或用例背景中提到、但没有被测试步骤或预期结果验证的内容算作已覆盖。
不存在接口或参数时，interfaces 返回空数组。不要虚构需求中不存在的接口、参数或测试证据。
严格返回一个 JSON 对象，不要返回 Markdown 或解释文字。JSON 结构如下：
{
  "feature_points": [
    {
      "name": "功能点名称",
      "covered": true,
      "evidence_testcase_ids": ["用例ID"]
    }
  ],
  "interfaces": [
    {
      "interface_name": "接口名称",
      "parameters": [
        {
          "name": "参数名称",
          "covered": true,
          "tested_conditions": ["合法值", "非法值", "边界值"],
          "evidence_testcase_ids": ["用例ID"]
        }
      ]
    }
  ]
}"""

    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

    def get_coverage(self, project_id):
        if not self.storage.get_project(project_id):
            return None, "not_found"
        saved = self.storage.get_project_coverage(project_id)
        if saved is None or saved.get("schema_version") != 3:
            return None, None
        return saved, None

    def calculate_coverage(self, project_id, on_requirement_completed=None):
        project = self.storage.get_project(project_id)
        if not project:
            raise CoverageAnalysisError("not_found")
        requirements = self.storage.list_requirements(project_id) or []
        if not requirements:
            raise CoverageAnalysisError("no_requirements")
        testcases = self.storage.list_project_testcases(project_id) or []
        client, model = self._build_client()
        if client is None:
            raise CoverageAnalysisError("missing_api_key")

        started_at = time.perf_counter()
        cases_by_requirement = self._cases_by_requirement(testcases)
        requirement_results = self._analyze_requirements(
            client,
            model,
            project,
            requirements,
            cases_by_requirement,
            on_requirement_completed=on_requirement_completed,
        )
        result = self._aggregate_result(requirement_results)
        result.update(
            {
                "schema_version": 3,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
                "duration": round(time.perf_counter() - started_at, 3),
                "model": model,
            }
        )
        return self.storage.save_project_coverage(project_id, result)

    @staticmethod
    def _cases_by_requirement(testcases):
        grouped = {}
        for testcase in testcases:
            requirement_id = str(testcase.get("requirement_id", ""))
            grouped.setdefault(requirement_id, []).append(testcase)
        return grouped

    def _analyze_requirements(
        self,
        client,
        model,
        project,
        requirements,
        cases_by_requirement,
        on_requirement_completed=None,
    ):
        results = [None] * len(requirements)
        worker_count = min(self.MAX_WORKERS, len(requirements))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {}
            for index, requirement in enumerate(requirements):
                requirement_cases = cases_by_requirement.get(
                    str(requirement.get("id", "")),
                    [],
                )
                future = executor.submit(
                    self._analyze_requirement,
                    client,
                    model,
                    project,
                    requirement,
                    requirement_cases,
                )
                futures[future] = index
            for future in as_completed(futures):
                index = futures[future]
                results[index] = future.result()
                if on_requirement_completed:
                    on_requirement_completed(
                        str(requirements[index].get("id", ""))
                    )
        return results

    def _analyze_requirement(
        self,
        client,
        model,
        project,
        requirement,
        testcases,
    ):
        raw_result = self._request_analysis(
            client,
            model,
            project,
            requirement,
            testcases,
        )
        evidence_map = self._evidence_map(testcases)
        return self._normalize_requirement_result(
            requirement,
            raw_result,
            evidence_map,
        )

    @staticmethod
    def _evidence_map(testcases):
        evidence_map = {}
        for testcase in testcases:
            evidence = {
                "id": str(testcase.get("id", "")),
                "code": str(testcase.get("code", "")),
                "title": str(testcase.get("title", "")),
            }
            for value in (evidence["id"], evidence["code"]):
                if value:
                    evidence_map[value] = evidence
        return evidence_map

    def _build_client(self):
        effective_config = self._get_effective_ai_config()
        if not effective_config.get("api_key"):
            return None, effective_config.get("model", "")
        return (
            OpenAI(
                api_key=effective_config["api_key"],
                base_url=effective_config.get("base_url") or None,
            ),
            effective_config.get("model"),
        )

    def _get_effective_ai_config(self):
        user_config = self.storage.get_ai_config()
        if user_config and user_config.get("api_key"):
            return {
                "api_key": user_config["api_key"],
                "base_url": user_config.get("base_url", ""),
                "model": user_config.get("model", "") or self.config.ai_model,
            }
        return {
            "api_key": self.config.ai_api_key,
            "base_url": self.config.ai_base_url,
            "model": self.config.ai_model,
        }

    def _request_analysis(self, client, model, project, requirement, testcases):
        analysis_input = {
            "project": {
                "id": str(project.get("id", "")),
                "code": project.get("code", ""),
                "title": project.get("title", ""),
            },
            "requirement": {
                "id": str(requirement.get("id", "")),
                "code": requirement.get("code", ""),
                "title": requirement.get("title", ""),
                "type": requirement.get("type", ""),
                "module": requirement.get("module", ""),
                "content": requirement.get("content", ""),
                "testcases": [
                    self._testcase_payload(testcase)
                    for testcase in testcases
                ],
            },
        }
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "请分析以下项目数据：\n"
                    + json.dumps(analysis_input, ensure_ascii=False),
                },
            ],
            temperature=0.1,
            top_p=0.8,
        )
        content = response.choices[0].message.content
        try:
            return json.loads(self._clean_json_content(content))
        except (AttributeError, TypeError, json.JSONDecodeError) as exc:
            raise CoverageAnalysisError("invalid_ai_response") from exc

    @staticmethod
    def _testcase_payload(testcase):
        return {
            "id": str(testcase.get("id", "")),
            "code": testcase.get("code", ""),
            "title": testcase.get("title", ""),
            "type": testcase.get("type", ""),
            "scenario_type": testcase.get("scenario_type", ""),
            "test_target_desc": testcase.get("test_target_desc", ""),
            "test_steps": testcase.get("test_steps", []),
            "verify_method": testcase.get("verify_method", ""),
        }

    @staticmethod
    def _clean_json_content(content):
        cleaned = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            str(content or ""),
            flags=re.DOTALL,
        ).strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _normalize_requirement_result(
        self,
        requirement,
        raw_result,
        evidence_map,
    ):
        if not isinstance(raw_result, dict):
            raise CoverageAnalysisError("invalid_ai_response")
        feature_points = self._normalize_feature_points(
            raw_result.get("feature_points"),
            evidence_map,
        )
        interfaces = self._normalize_interfaces(
            raw_result.get("interfaces"),
            evidence_map,
        )
        return {
            "requirement_id": str(requirement.get("id", "")),
            "requirement_code": str(requirement.get("code", "")),
            "requirement_title": str(requirement.get("title", "")),
            "module": str(requirement.get("module", "")),
            "feature_point_coverage": self._item_summary(feature_points),
            "feature_points": feature_points,
            "interface_coverage": self._interface_summary(interfaces),
            "interfaces": interfaces,
        }

    @staticmethod
    def _normalize_feature_points(items, evidence_map):
        if not isinstance(items, list):
            raise CoverageAnalysisError("invalid_ai_response")
        normalized = []
        for item in items:
            if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                continue
            evidence_testcases = CoverageService._valid_evidence_testcases(
                item.get("evidence_testcase_ids"),
                evidence_map,
            )
            normalized.append(
                {
                    "name": str(item["name"]).strip(),
                    "covered": item.get("covered") is True
                    and bool(evidence_testcases),
                    "evidence_testcases": evidence_testcases,
                }
            )
        return normalized

    @staticmethod
    def _normalize_interfaces(items, evidence_map):
        if not isinstance(items, list):
            raise CoverageAnalysisError("invalid_ai_response")
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            parameters = []
            for parameter in item.get("parameters", []):
                if not isinstance(parameter, dict) or not str(
                    parameter.get("name", "")
                ).strip():
                    continue
                tested_conditions = CoverageService._string_list(
                    parameter.get("tested_conditions")
                )
                evidence_testcases = CoverageService._valid_evidence_testcases(
                    parameter.get("evidence_testcase_ids"),
                    evidence_map,
                )
                parameters.append(
                    {
                        "name": str(parameter["name"]).strip(),
                        "covered": parameter.get("covered") is True
                        and bool(tested_conditions)
                        and bool(evidence_testcases),
                        "tested_conditions": tested_conditions,
                        "evidence_testcases": evidence_testcases,
                    }
                )
            if parameters:
                normalized.append(
                    {
                        "interface_name": str(item.get("interface_name", "")),
                        "coverage": CoverageService._item_summary(parameters),
                        "parameters": parameters,
                    }
                )
        return normalized

    @staticmethod
    def _string_list(value):
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    @staticmethod
    def _valid_evidence_testcases(value, evidence_map):
        evidence_testcases = []
        seen_ids = set()
        for item in CoverageService._string_list(value):
            evidence = evidence_map.get(item)
            if not evidence or evidence["id"] in seen_ids:
                continue
            evidence_testcases.append(dict(evidence))
            seen_ids.add(evidence["id"])
        return evidence_testcases

    @staticmethod
    def _item_summary(items):
        total = len(items)
        covered = sum(1 for item in items if item["covered"])
        return CoverageService._metric(total, covered)

    @staticmethod
    def _interface_summary(interfaces):
        total = sum(len(item["parameters"]) for item in interfaces)
        covered = sum(
            1
            for interface in interfaces
            for parameter in interface["parameters"]
            if parameter["covered"]
        )
        return CoverageService._metric(total, covered)

    @staticmethod
    def _metric(total, covered):
        return {
            "total": int(total),
            "covered": int(covered),
            "rate": round(covered / total, 4) if total else 0,
        }

    def _aggregate_result(self, requirement_results):
        feature_details = []
        interface_details = []
        for item in requirement_results:
            identity = {
                "requirement_id": item["requirement_id"],
                "requirement_code": item["requirement_code"],
                "requirement_title": item["requirement_title"],
                "module": item["module"],
            }
            feature_details.append(
                {
                    **identity,
                    "coverage": item["feature_point_coverage"],
                    "points": item["feature_points"],
                }
            )
            interface_details.append(
                {
                    **identity,
                    "coverage": item["interface_coverage"],
                    "interfaces": item["interfaces"],
                }
            )
        return {
            "feature_point_coverage": self._aggregate_metrics(
                item["coverage"] for item in feature_details
            ),
            "interface_coverage": self._aggregate_metrics(
                item["coverage"] for item in interface_details
            ),
            "feature_point_details": feature_details,
            "interface_details": interface_details,
        }

    @staticmethod
    def _aggregate_metrics(metrics):
        metrics = list(metrics)
        return CoverageService._metric(
            sum(item["total"] for item in metrics),
            sum(item["covered"] for item in metrics),
        )
