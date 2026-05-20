import time


class AIConfigService:
    def __init__(self, storage):
        self.storage = storage

    def get_config(self):
        return self.storage.get_ai_config()

    def save_config(self, payload):
        data = {
            "api_key": payload.get("api_key", ""),
            "base_url": payload.get("base_url", ""),
            "model": payload.get("model", ""),
            "updated_at": time.time(),
        }
        return self.storage.save_ai_config(data)