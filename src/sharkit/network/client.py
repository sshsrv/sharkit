from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from sharkit import __version__
from sharkit.exceptions import NetworkError

DEFAULT_USER_AGENT = f"sharkit/{__version__}"
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
    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        headers: dict[str, str] | None = None,
    ) -> None:
        default_headers: dict[str, str] = {"User-Agent": user_agent}
        if headers:
            default_headers.update(headers)
        self._client = httpx.Client(
            headers=default_headers,
            follow_redirects=True,
            timeout=DEFAULT_TIMEOUT,
        )

    def get(self, url: str, timeout: float = DEFAULT_TIMEOUT) -> Response:
        return self._request("GET", url, timeout)

    def head(self, url: str, timeout: float = DEFAULT_TIMEOUT) -> Response:
        return self._request("HEAD", url, timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        self.close()

    def _request(self, method: str, url: str, timeout: float) -> Response:
        if timeout <= 0 or timeout > 300:
            raise NetworkError(
                f"Timeout must be 0 < timeout <= 300, got {timeout}"
            )

        start = time.monotonic()
        try:
            with self._client.stream(method, url, timeout=timeout) as response:
                response.raise_for_status()
                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > MAX_RESPONSE_BYTES:
                        raise NetworkError(
                            f"Response exceeded maximum size"
                            f" ({MAX_RESPONSE_BYTES} bytes)"
                        )
                    chunks.append(chunk)

                duration = time.monotonic() - start
                protocol = f"HTTP/{response.http_version}"

                return Response(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=b"".join(chunks),
                    duration=round(duration, 3),
                    url=str(response.url),
                    protocol=protocol,
                )
        except httpx.TimeoutException:
            raise NetworkError(
                f"Request timed out after {timeout}s"
            ) from None
        except httpx.ConnectError:
            raise NetworkError(f"Connection failed: {url}") from None
        except httpx.RequestError:
            raise NetworkError(f"Request failed: {url}") from None
