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

ROBTEX_API = "https://freeapi.robtex.com/ipquery"


class RobtexTool(Tool):
    metadata = ToolMetadata(
        name="robtex",
        description="Query Robtex for ASN info, routing and passive DNS for an IP",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E74C3C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "ip": OptionDefinition(
                name="ip",
                description="IP address to query",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        ip = context.options.get("ip") or ""
        if not ip:
            return Result(success=False, error="Option 'ip' is required.")

        url = f"{ROBTEX_API}/{ip}"

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
            return Result(success=False, error=data["error"])

        bgproute = data.get("bgproute", "?")
        asn = data.get("as", "?")
        whoisdesc = data.get("whoisdesc", "")
        name = data.get("name", "?")
        country = data.get("country", "?")
        reverse = data.get("reverse", [])

        lines: list[str] = []
        lines.append(f"Robtex info for {ip}:")

        if whoisdesc:
            lines.append(f"  AS: AS{asn} ({whoisdesc})")
        else:
            lines.append(f"  AS: AS{asn}")

        lines.append(f"  Route: {bgproute}")
        lines.append(f"  Country: {country}")
        lines.append(f"  Name: {name}")

        if reverse:
            lines.append("  Passive DNS:")
            for entry in reverse:
                lines.append(f"    - {entry}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
