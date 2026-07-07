import json
import os


class AppConfig:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.data_dir = os.environ.get("DATA_DIR", os.path.join(base_dir, "data"))
        self.uniportal_storage_path = os.environ.get("UNIPORTAL_STORAGE_PATH", "uniportal")
        self.uniportal_sync_enabled = (
            os.environ.get("UNIPORTAL_SYNC_ENABLED", "true").strip().lower()
            not in {"0", "false", "no", "off"}
        )
        try:
            self.uniportal_sync_interval_seconds = int(
                os.environ.get("UNIPORTAL_SYNC_INTERVAL_SECONDS", "300")
            )
        except ValueError:
            self.uniportal_sync_interval_seconds = 300
        self.uniportal_sync_interval_seconds = max(
            5, self.uniportal_sync_interval_seconds
        )
        self.ai_model = ""
        self.ai_base_url = ""
        self.ai_api_key = ""
        config_path = os.path.join(base_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.ai_model = config.get("model_name", "")
            self.ai_base_url = config.get("url", "")
            self.ai_api_key = config.get("api_key", "")
        if not self.ai_model:
            self.ai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        if not self.ai_api_key:
            self.ai_api_key = os.environ.get("OPENAI_API_KEY", "")
