from dataclasses import dataclass, field


SCENARIO_TYPES = (
    "正常流程用例",
    "边界条件用例",
    "异常场景用例",
    "组合场景用例",
    "回归测试用例",
)

PRIORITY_LEVELS = ("P0", "P1", "P2", "P3")
DEFAULT_PRIORITY = "P1"


def is_valid_scenario_type(value):
    return value in SCENARIO_TYPES


def is_valid_priority(value):
    return value in PRIORITY_LEVELS


@dataclass
class TestStep:
    step_desc: str
    expectation: str

    @classmethod
    def from_dict(cls, data):
        return cls(step_desc=data.get("step_desc", ""), expectation=data.get("expectation", ""))

    def to_dict(self):
        return {"step_desc": self.step_desc, "expectation": self.expectation}


@dataclass
class TestCase:
    id: str
    requirement_id: str
    requirement_code: str
    title: str
    code: str
    type: str
    scenario_type: str
    priority: str = DEFAULT_PRIORITY
    test_steps: list[TestStep] = field(default_factory=list)
    test_target_desc: str = ""
    verify_method: str = "TESTING"
    project_id: str = ""

    def __post_init__(self):
        if not is_valid_scenario_type(self.scenario_type):
            raise ValueError("scenario_type 参数不合法")
        if not is_valid_priority(self.priority):
            raise ValueError("priority 参数不合法")

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(data.get("id", "")),
            requirement_id=str(data.get("requirement_id", "")),
            requirement_code=data.get("requirement_code", ""),
            title=data.get("title", ""),
            code=data.get("code", ""),
            type=data.get("type", ""),
            scenario_type=data["scenario_type"],
            priority=data.get("priority", DEFAULT_PRIORITY),
            test_steps=[TestStep.from_dict(item) for item in data.get("test_steps", [])],
            test_target_desc=data.get("test_target_desc", ""),
            verify_method=data.get("verify_method", "TESTING"),
            project_id=str(data.get("project_id", "")),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "requirement_id": self.requirement_id,
            "requirement_code": self.requirement_code,
            "title": self.title,
            "code": self.code,
            "type": self.type,
            "scenario_type": self.scenario_type,
            "priority": self.priority,
            "test_steps": [step.to_dict() for step in self.test_steps],
            "test_target_desc": self.test_target_desc,
            "verify_method": self.verify_method,
            "project_id": self.project_id,
        }
