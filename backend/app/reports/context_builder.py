from collections import Counter
from datetime import date

from app.models.testcase import DEFAULT_PRIORITY


UNKNOWN_MODULE = "未命名模块"
UNKNOWN_TYPE = "未知类型"
EMPTY_VALUE = "暂无"


def _display(value, fallback=EMPTY_VALUE):
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _build_case(item):
    steps = []
    for step in item.get("test_steps") or []:
        step = step if isinstance(step, dict) else {}
        steps.append(
            {
                "step_desc": _display(step.get("step_desc")),
                "expectation": _display(step.get("expectation")),
            }
        )
    return {
        "id": str(item.get("id") or ""),
        "code": _display(item.get("code")),
        "title": _display(item.get("title"), "未命名测试用例"),
        "type": _display(item.get("type"), UNKNOWN_TYPE),
        "scenario_type": _display(item.get("scenario_type")),
        "priority": _display(item.get("priority"), DEFAULT_PRIORITY),
        "test_target_desc": _display(item.get("test_target_desc")),
        "verify_method": _display(item.get("verify_method")),
        "steps": steps,
    }


class ReportContextBuilder:
    def __init__(self, today_provider=None):
        self._today_provider = today_provider or date.today

    def build(self, source):
        project = source["project"]
        modules = self._build_modules(
            source.get("requirements") or [],
            source.get("testcases") or [],
        )
        project_name = self._project_name(project)
        return {
            "metadata": {
                "project_name": project_name,
                "version": "V1.0",
                "compiled_date": self._today_provider().isoformat(),
            },
            "project": {
                "id": str(project.get("id") or ""),
                "code": _display(
                    project.get("code"),
                    str(project.get("id") or "project"),
                ),
                "title": project_name,
            },
            "modules": modules,
            "summary": self._build_summary(modules),
        }

    @staticmethod
    def _project_name(project):
        return _display(
            project.get("title"),
            _display(project.get("code"), str(project.get("id") or "测试项目")),
        )

    @staticmethod
    def _build_modules(requirements, testcases):
        cases_by_requirement = {}
        for testcase in testcases:
            requirement_id = str(testcase.get("requirement_id") or "")
            cases_by_requirement.setdefault(requirement_id, []).append(testcase)

        modules = []
        modules_by_name = {}
        known_requirement_ids = set()
        for requirement in requirements:
            requirement_id = str(requirement.get("id") or "")
            known_requirement_ids.add(requirement_id)
            module_name = _display(requirement.get("module"), UNKNOWN_MODULE)
            module = modules_by_name.get(module_name)
            if module is None:
                module = {"name": module_name, "requirements": []}
                modules_by_name[module_name] = module
                modules.append(module)
            module["requirements"].append(
                {
                    "id": requirement_id,
                    "code": _display(requirement.get("code")),
                    "title": _display(requirement.get("title"), "未命名需求"),
                    "type": _display(requirement.get("type"), UNKNOWN_TYPE),
                    "content": _display(requirement.get("content")),
                    "testcases": [
                        _build_case(item)
                        for item in cases_by_requirement.get(requirement_id, [])
                    ],
                }
            )

        orphan_requirement_ids = [
            requirement_id
            for requirement_id in cases_by_requirement
            if requirement_id not in known_requirement_ids
        ]
        if orphan_requirement_ids:
            orphan_module = modules_by_name.get(UNKNOWN_MODULE)
            if orphan_module is None:
                orphan_module = {"name": UNKNOWN_MODULE, "requirements": []}
                modules.append(orphan_module)
            for requirement_id in orphan_requirement_ids:
                orphan_module["requirements"].append(
                    {
                        "id": requirement_id,
                        "code": _display(requirement_id),
                        "title": "未关联需求",
                        "type": UNKNOWN_TYPE,
                        "content": EMPTY_VALUE,
                        "testcases": [
                            _build_case(item)
                            for item in cases_by_requirement[requirement_id]
                        ],
                    }
                )

        return modules

    @classmethod
    def _build_summary(cls, modules):
        requirements = [
            requirement
            for module in modules
            for requirement in module["requirements"]
        ]
        testcases = [
            testcase
            for requirement in requirements
            for testcase in requirement["testcases"]
        ]
        return {
            "requirement_groups": [
                {
                    "module": module["name"],
                    "requirements": [
                        {
                            "code": requirement["code"],
                            "title": requirement["title"],
                            "type": requirement["type"],
                            "testcase_count": len(requirement["testcases"]),
                        }
                        for requirement in module["requirements"]
                    ],
                }
                for module in modules
            ],
            "case_type_stats": cls._statistics(
                testcase["type"] for testcase in testcases
            ),
            "priority_stats": cls._statistics(
                testcase["priority"] for testcase in testcases
            ),
            "coverage": [
                {
                    "code": requirement["code"],
                    "title": requirement["title"],
                    "testcase_codes": "、".join(
                        testcase["code"]
                        for testcase in requirement["testcases"]
                    )
                    or EMPTY_VALUE,
                    "testcase_count": len(requirement["testcases"]),
                    "status": "已覆盖" if requirement["testcases"] else "未覆盖",
                }
                for requirement in requirements
            ],
        }

    @staticmethod
    def _statistics(values):
        counts = Counter(values)
        total = sum(counts.values())
        return [
            {
                "name": name,
                "count": count,
                "percentage": f"{count / total:.2%}",
            }
            for name, count in counts.items()
        ]
