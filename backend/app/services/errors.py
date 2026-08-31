"""Business failures translated independently by REST and MCP adapters."""


class BusinessError(Exception):
    def __init__(self, code: int, message: str, http_status: int = 400, data=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.data = data if data is not None else {}

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "data": self.data}
