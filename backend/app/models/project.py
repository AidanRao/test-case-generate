from dataclasses import dataclass


@dataclass
class Project:
    id: str
    code: str
    title: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(data.get("id", "")),
            code=data.get("code", ""),
            title=data.get("title", ""),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
        }
