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

BGPVIEW_API = "https://api.bgpview.io/ip"


class BGPv6Tool(Tool):
    metadata = ToolMetadata(
        name="bgpv6",
        description="Look up BGP origin ASN, prefixes and network info for an IP via bgpview.io",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#2ECC71",
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

        url = f"{BGPVIEW_API}/{ip}"

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

        if data.get("status") != "ok":
            msg = data.get("error", {}).get("message", "Unknown error")
            return Result(success=False, error=f"API error: {msg}")

        ip_data = data.get("data", {})
        asns = ip_data.get("asns", [])
        prefixes = ip_data.get("prefixes", [])

        lines: list[str] = []
        lines.append(f"BGP info for {ip}:")

        if asns:
            first = asns[0]
            asn = first.get("asn", "?")
            name = first.get("name", "?")
            country = first.get("country_code", "?")
            lines.append(f"  ASN: AS{asn} ({name})")
            lines.append(f"  Country: {country}")
        else:
            lines.append("  ASN: not found")

        if prefixes:
            prefix_strs = [f"{p.get('prefix', '?')}" for p in prefixes]
            lines.append(f"  Prefixes: {', '.join(prefix_strs)}")
        else:
            lines.append("  Prefixes: none")

        if asns:
            description = asns[0].get("description", "")
            if description:
                lines.append(f"  Name: {description}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
