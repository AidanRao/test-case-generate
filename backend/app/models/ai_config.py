from dataclasses import dataclass
from typing import Optional


@dataclass
class AIConfig:
    id: str
    api_key: str
    base_url: str
    model: str
    created_at: float
    updated_at: float

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(data.get("id", "")),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            model=data.get("model", ""),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }