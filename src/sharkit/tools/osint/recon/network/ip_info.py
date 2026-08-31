from __future__ import annotations

import json

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

IPINFO_API = "https://ipinfo.io"


class IPInfoTool(Tool):
    metadata = ToolMetadata(
        name="ip_info",
        description="Look up IP address geolocation and network info via ipinfo.io",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#3498DB",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "ip": OptionDefinition(
                name="ip",
                description="IP address to look up (use 'me' for your own IP)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        ip = context.options.get("ip") or ""
        if not ip:
            return Result(success=False, error="Option 'ip' is required.")

        url = f"{IPINFO_API}/{ip}/json"

        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(resp.content)
        except Exception:
            return Result(
                success=False,
                error=f"Failed to parse response (status {resp.status_code})",
            )

        if "error" in data:
            return Result(success=False, error=data["error"].get("message", "Unknown error"))

        lines: list[str] = []
        lines.append(f"IP: {data.get('ip', '?')}")
        lines.append(f"City: {data.get('city', '?')}")
        lines.append(f"Region: {data.get('region', '?')}")
        lines.append(f"Country: {data.get('country', '?')}")
        lines.append(f"Location: {data.get('loc', '?')}")
        lines.append(f"Organization: {data.get('org', '?')}")
        lines.append(f"Timezone: {data.get('timezone', '?')}")
        lines.append(f"Postal Code: {data.get('postal', '?')}")
        lines.append(f"Hostname: {data.get('hostname', '?')}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
