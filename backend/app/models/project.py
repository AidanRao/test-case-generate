from dataclasses import dataclass, field


@dataclass
class Project:
    id: str
    code: str
    title: str
    modules: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(data.get("id", "")),
            code=data.get("code", ""),
            title=data.get("title", ""),
            modules=[
                str(item)
                for item in data.get("modules", [])
                if str(item).strip()
            ],
        )

    def to_dict(self, include_modules=True):
        data = {
            "id": self.id,
            "code": self.code,
            "title": self.title,
        }
        if include_modules:
            data["modules"] = self.modules
        return data
