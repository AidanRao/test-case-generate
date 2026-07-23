import json
import time
from urllib import error as url_error
from urllib import request as url_request


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

    def test_connection(self, payload, timeout=10):
        base_url = str(payload.get("base_url", "")).strip().rstrip("/")
        api_key = str(payload.get("api_key", "")).strip()
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
                response_body = response.read(4096).decode("utf-8", errors="replace")
                status_code = response.getcode()
                return self._test_result(
                    200 <= status_code < 300,
                    started_at,
                    status_code,
                    "后端连接成功" if 200 <= status_code < 300 else "后端连接失败",
                    response_body,
                )
        except url_error.HTTPError as exc:
            response_body = exc.read(4096).decode("utf-8", errors="replace")
            return self._test_result(
                False,
                started_at,
                exc.code,
                f"LLM API 返回 HTTP {exc.code}",
                response_body,
            )
        except (url_error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            return self._test_result(
                False,
                started_at,
                None,
                "后端无法连接 LLM API",
                str(reason),
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
