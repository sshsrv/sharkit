import time
from dataclasses import dataclass

import httpx

from sharkit.exceptions import NetworkError

DEFAULT_USER_AGENT = "sharkit/0.1.0"
DEFAULT_TIMEOUT: float = 10.0
MAX_RESPONSE_BYTES: int = 10 * 1024 * 1024


@dataclass(frozen=True)
class Response:
    status_code: int
    headers: dict[str, str]
    content: bytes
    duration: float
    url: str
    protocol: str


class HttpClient:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            timeout=DEFAULT_TIMEOUT,
        )

    def get(self, url: str, timeout: float = DEFAULT_TIMEOUT) -> Response:
        return self._request("GET", url, timeout)

    def head(self, url: str, timeout: float = DEFAULT_TIMEOUT) -> Response:
        return self._request("HEAD", url, timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        self.close()

    def _request(self, method: str, url: str, timeout: float) -> Response:
        if timeout <= 0 or timeout > 300:
            raise NetworkError(f"Invalid timeout: {timeout}s (must be 0 < timeout <= 300)")

        start = time.monotonic()
        try:
            response = self._client.request(
                method,
                url,
                timeout=timeout,
            )
            duration = time.monotonic() - start

            if len(response.content) > MAX_RESPONSE_BYTES:
                raise NetworkError(
                    f"Response too large: {len(response.content)} bytes "
                    f"(limit: {MAX_RESPONSE_BYTES})"
                )

            protocol = f"HTTP/{response.http_version}"

            return Response(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=response.content,
                duration=round(duration, 3),
                url=str(response.url),
                protocol=protocol,
            )
        except httpx.TimeoutException as exc:
            duration = time.monotonic() - start
            raise NetworkError(f"Request timed out after {duration:.1f}s") from exc
        except httpx.ConnectError as exc:
            raise NetworkError(f"Connection failed: {exc}") from exc
        except httpx.RequestError as exc:
            raise NetworkError(f"Request failed: {exc}") from exc
