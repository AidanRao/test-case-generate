import json
import logging
import os


logger = logging.getLogger(__name__)


class AppConfig:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.data_dir = os.environ.get("DATA_DIR", os.path.join(base_dir, "data"))
        self.uniportal_storage_path = os.environ.get("UNIPORTAL_STORAGE_PATH", "uniportal")
        self.ai_model = ""
        self.ai_base_url = ""
        self.ai_api_key = ""
        config_path = os.path.join(base_dir, "config.json")
        config = self._load_config(config_path)
        self.ai_model = config.get("model_name", "")
        self.ai_base_url = config.get("url", "")
        self.ai_api_key = config.get("api_key", "")
        if not self.ai_model:
            self.ai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        if not self.ai_api_key:
            self.ai_api_key = os.environ.get("OPENAI_API_KEY", "")

    @staticmethod
    def _load_config(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            return {}
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            logger.warning(
                "Unable to read config file %s; using environment variables and "
                "defaults instead: %s",
                config_path,
                error,
            )
            return {}

        if not isinstance(config, dict):
            logger.warning(
                "Config file %s must contain a JSON object; using environment "
                "variables and defaults instead",
                config_path,
            )
            return {}

        return config
