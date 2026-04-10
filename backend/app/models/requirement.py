from dataclasses import dataclass


@dataclass
class Requirement:
    id: str
    title: str
    type: str
    code: str
    content: str
    project_id: str
    module: str

    @classmethod
    def from_dict(cls, data, module=None, project_id=None):
        project_id_value = data.get("project_id", "")
        if project_id is not None:
            project_id_value = project_id
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            type=data.get("type", ""),
            code=data.get("code", ""),
            content=data.get("content", ""),
            project_id=str(project_id_value),
            module=module or data.get("module", ""),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "code": self.code,
            "content": self.content,
            "project_id": self.project_id,
            "module": self.module,
        }
