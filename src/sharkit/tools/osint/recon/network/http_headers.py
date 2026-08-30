from __future__ import annotations

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

SECURITY_HEADERS = {
    "Strict-Transport-Security": "HSTS (forces HTTPS)",
    "X-Frame-Options": "Clickjacking protection",
    "X-Content-Type-Options": "MIME sniffing protection",
    "Content-Security-Policy": "XSS & injection protection",
    "X-XSS-Protection": "Legacy XSS filter",
}


class HTTPHeadersTool(Tool):
    metadata = ToolMetadata(
        name="http_headers",
        description="HTTP response header analysis with security checks",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#1ABC9C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "url": OptionDefinition(
                name="url",
                description="Target URL (must start with http:// or https://)",
                required=True,
            ),
            "method": OptionDefinition(
                name="method",
                description="HTTP method (HEAD or GET)",
                required=False,
                default="HEAD",
                choices=["HEAD", "GET"],
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        url = context.options.get("url") or ""
        if not url:
            return Result(success=False, error="Option 'url' is required.")

        if not url.startswith(("http://", "https://")):
            return Result(
                success=False,
                error="URL must start with http:// or https://",
            )

        method = context.options.get("method") or "HEAD"

        with HttpClient() as client:
            try:
                resp = client.head(url) if method == "HEAD" else client.get(url)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        lines: list[str] = [f"HTTP Headers for {url}:"]
        lines.append(f"  Status:   {resp.status_code} ({resp.protocol})")
        lines.append(f"  URL:      {resp.url}")
        lines.append(f"  Duration: {resp.duration}s")
        lines.append("")

        # All headers
        lines.append("Response Headers:")
        for key, value in sorted(resp.headers.items()):
            lines.append(f"  {key}: {value}")

        # Security analysis
        lines.append("")
        lines.append("Security Header Analysis:")
        missing: list[str] = []
        for header, description in SECURITY_HEADERS.items():
            if header.lower() in {k.lower() for k in resp.headers}:
                actual_value = resp.headers.get(header) or next(
                    v for k, v in resp.headers.items() if k.lower() == header.lower()
                )
                lines.append(f"  [+] {header}: {actual_value}")
            else:
                lines.append(f"  [-] {header}: MISSING — {description}")
                missing.append(header)

        if missing:
            lines.append("")
            lines.append(f"  {len(missing)} security header(s) missing.")
        else:
            lines.append("")
            lines.append("  All common security headers present.")

        # Server header info
        server = resp.headers.get("Server") or resp.headers.get("server")
        if server:
            lines.append("")
            lines.append(f"  Server: {server}")

        return Result(success=True, data={"result": "\n".join(lines)})
