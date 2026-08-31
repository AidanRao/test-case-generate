import json
import time
from urllib import error as url_error
from urllib import request as url_request


class AIConfigService:
    def __init__(self, storage):
        self.storage = storage

    def get_config(self):
        return self._public_config(self.storage.get_ai_config())

    @staticmethod
    def _public_config(config):
        config = config or {}
        return {
            "has_api_key": bool(config.get("api_key")),
            "base_url": config.get("base_url", ""),
            "model": config.get("model", ""),
            "updated_at": config.get("updated_at", 0.0),
        }

    def _resolve_api_key(self, payload):
        # An omitted key preserves the stored secret; an explicit empty key clears it.
        if "api_key" in payload:
            return str(payload["api_key"]).strip()
        config = self.storage.get_ai_config() or {}
        return config.get("api_key", "")

    def save_config(self, payload):
        data = {
            "api_key": self._resolve_api_key(payload),
            "base_url": payload.get("base_url", ""),
            "model": payload.get("model", ""),
            "updated_at": time.time(),
        }
        config = self.storage.save_ai_config(data)
        return self._public_config(config) if config else None

    def test_connection(self, payload, timeout=10):
        base_url = str(payload.get("base_url", "")).strip().rstrip("/")
        api_key = self._resolve_api_key(payload)
        model = str(payload.get("model", "")).strip() or "qwen3-max"
        started_at = time.perf_counter()

        if not base_url:
            return self._test_result(False, started_at, None, "Base URL 不能为空")
        if not base_url.startswith(("http://", "https://")):
            return self._test_result(
                False,
                started_at,
                None,
                "Base URL 必须以 http:// 或 https:// 开头",
            )

        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = url_request.Request(
            f"{base_url}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with url_request.urlopen(req, timeout=timeout) as response:
                # Do not expose upstream bodies: even errors may echo credentials.
                status_code = response.getcode()
                return self._test_result(
                    200 <= status_code < 300,
                    started_at,
                    status_code,
                    "后端连接成功" if 200 <= status_code < 300 else "后端连接失败",
                )
        except url_error.HTTPError as exc:
            exc.close()
            return self._test_result(
                False,
                started_at,
                exc.code,
                f"LLM API 返回 HTTP {exc.code}",
            )
        except (url_error.URLError, TimeoutError, OSError):
            return self._test_result(
                False,
                started_at,
                None,
                "后端无法连接 LLM API",
            )

    @staticmethod
    def _test_result(success, started_at, status_code, message, detail=""):
        return {
            "success": success,
            "status_code": status_code,
            "duration_ms": round((time.perf_counter() - started_at) * 1000),
            "message": message,
            "detail": detail[:2000],
        }
