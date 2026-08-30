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

SHODAN_API = "https://internetdb.shodan.io"


class ShodanInternetDBTool(Tool):
    metadata = ToolMetadata(
        name="shodan_internetdb",
        description="Query Shodan InternetDB for open ports, hostnames, vulns and CPEs for an IP",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#FF6B35",
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

        url = f"{SHODAN_API}/{ip}"

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

        if resp.status_code != 200:
            msg = data.get("error", "Unknown error")
            return Result(success=False, error=f"API error: {msg}")

        ports = data.get("ports", [])
        hostnames = data.get("hostnames", [])
        cpes = data.get("cpes", [])
        vulns = data.get("vulns", [])
        tags = data.get("tags", [])

        lines: list[str] = []
        lines.append(f"Shodan InternetDB for {ip}:")
        lines.append(f"  Ports: {', '.join(str(p) for p in ports) if ports else 'none'}")
        lines.append(f"  Hostnames: {', '.join(hostnames) if hostnames else 'none'}")
        lines.append(f"  CPEs: {', '.join(cpes) if cpes else 'none'}")
        lines.append(f"  Vulns: {', '.join(vulns) if vulns else 'none'}")
        lines.append(f"  Tags: {', '.join(tags) if tags else 'none'}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
