from app.utils.ids import new_uuid
import time


class AIConfigService:
    def __init__(self, storage):
        self.storage = storage

    def get_config(self, config_id):
        return self.storage.get_ai_config(config_id)

    def list_configs(self):
        return self.storage.list_ai_configs()

    def create_config(self, payload):
        now = time.time()
        config_id = new_uuid()
        data = {
            "id": config_id,
            "api_key": payload.get("api_key", ""),
            "base_url": payload.get("base_url", ""),
            "model": payload.get("model", ""),
            "created_at": now,
            "updated_at": now,
        }
        return self.storage.create_ai_config(data)

    def update_config(self, config_id, payload):
        data = {k: v for k, v in payload.items() if k in ("api_key", "base_url", "model")}
        data["updated_at"] = time.time()
        return self.storage.update_ai_config(config_id, data)

    def delete_config(self, config_id):
        return self.storage.delete_ai_config(config_id)

    def get_default_config(self):
        return self.storage.get_default_ai_config()