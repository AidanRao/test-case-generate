import os

from app.models.ai_config import AIConfig


class AIConfigStore:
    def __init__(self, io, file_path):
        self.io = io
        self.file_path = file_path
        self._init_store()

    def _init_store(self):
        if not os.path.exists(self.file_path):
            self.io.save(self.file_path, {})

    def get_config(self):
        data = self.io.load(self.file_path, {})
        if not data:
            return None
        return AIConfig.from_dict(data)

    def save_config(self, payload):
        data = {
            "api_key": payload.get("api_key", ""),
            "base_url": payload.get("base_url", ""),
            "model": payload.get("model", ""),
            "updated_at": payload.get("updated_at", 0.0),
        }
        self.io.save(self.file_path, data)
        return AIConfig.from_dict(data)
