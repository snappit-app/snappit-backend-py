from fastapi.datastructures import Headers
from paddle_billing.Notifications.Requests.Request import Headers as PaddleHeaders
from paddle_billing.Notifications.Requests.Request import Request as PaddleRequest


class _PaddleHeaders(PaddleHeaders):
    def __init__(self, headers: Headers):
        self._headers = headers

    def get(self, key: str, default=None) -> str | None:
        return self._headers.get(key, default)


class _PaddleRequest(PaddleRequest):
    def __init__(
        self,
        headers: Headers,
        body: bytes | None = None,
        content: bytes | None = None,
        data: bytes | None = None,
    ):
        self.body = body
        self.content = content
        self.data = data
        self.headers = _PaddleHeaders(headers=headers)
