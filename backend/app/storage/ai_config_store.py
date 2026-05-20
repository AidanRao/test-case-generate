import os

from app.models.ai_config import AIConfig


class AIConfigStore:
    def __init__(self, io, file_path):
        self.io = io
        self.file_path = file_path
        self._init_store()

    def _init_store(self):
        if not os.path.exists(self.file_path):
            self.io.save(self.file_path, {"configs": []})

    def get_config(self, config_id):
        data = self.io.load(self.file_path, {"configs": []})
        for item in data.get("configs", []):
            if str(item.get("id")) == str(config_id):
                return AIConfig.from_dict(item)
        return None

    def list_configs(self):
        data = self.io.load(self.file_path, {"configs": []})
        return [AIConfig.from_dict(item) for item in data.get("configs", [])]

    def create_config(self, payload):
        data = self.io.load(self.file_path, {"configs": []})
        config = AIConfig(
            id=str(payload["id"]),
            api_key=payload.get("api_key", ""),
            base_url=payload.get("base_url", ""),
            model=payload.get("model", ""),
            created_at=payload.get("created_at", 0.0),
            updated_at=payload.get("updated_at", 0.0),
        )
        data["configs"].append(config.to_dict())
        self.io.save(self.file_path, data)
        return config

    def update_config(self, config_id, payload):
        data = self.io.load(self.file_path, {"configs": []})
        for idx, item in enumerate(data.get("configs", [])):
            if str(item.get("id")) == str(config_id):
                item.update(payload)
                self.io.save(self.file_path, data)
                return AIConfig.from_dict(item)
        return None

    def delete_config(self, config_id):
        data = self.io.load(self.file_path, {"configs": []})
        configs = data.get("configs", [])
        filtered = [item for item in configs if str(item.get("id")) != str(config_id)]
        if len(filtered) == len(configs):
            return False
        data["configs"] = filtered
        self.io.save(self.file_path, data)
        return True

    def get_default_config(self):
        data = self.io.load(self.file_path, {"configs": []})
        configs = data.get("configs", [])
        if not configs:
            return None
        return AIConfig.from_dict(configs[0])