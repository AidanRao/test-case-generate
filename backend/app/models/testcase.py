from dataclasses import dataclass, field


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
    test_steps: list[TestStep] = field(default_factory=list)
    test_target_desc: str = ""
    verify_method: str = "TESTING"
    project_id: str = ""

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(data.get("id", "")),
            requirement_id=str(data.get("requirement_id", "")),
            requirement_code=data.get("requirement_code", ""),
            title=data.get("title", ""),
            code=data.get("code", ""),
            type=data.get("type", ""),
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
            "test_steps": [step.to_dict() for step in self.test_steps],
            "test_target_desc": self.test_target_desc,
            "verify_method": self.verify_method,
            "project_id": self.project_id,
        }
