from __future__ import annotations

import json
import re

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

OTX_API = "https://otx.alienvault.com/api/v1"
IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)


class OTXQueryTool(Tool):
    metadata = ToolMetadata(
        name="otx_query",
        description="Query AlienVault OTX for threat intelligence on IPs, domains, and URLs",
        category="osint.recon.domain",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#1ABC9C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "indicator": OptionDefinition(
                name="indicator",
                description="IP, domain, hostname, or URL to look up",
                required=True,
            ),
            "type": OptionDefinition(
                name="type",
                description="Indicator type (auto-detect if auto)",
                required=False,
                default="auto",
                choices=["auto", "ip", "domain", "hostname", "url"],
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    @staticmethod
    def _detect_type(indicator: str) -> str:
        if IP_PATTERN.match(indicator):
            return "IPv4"
        if indicator.startswith(("http://", "https://")):
            return "url"
        if "." in indicator:
            return "domain"
        return "hostname"

    def execute(self, context: ExecutionContext) -> Result:
        indicator = context.options.get("indicator") or ""
        if not indicator:
            return Result(success=False, error="Option 'indicator' is required.")

        ind_type = context.options.get("type") or "auto"
        if ind_type == "auto":
            ind_type = self._detect_type(indicator)

        url = f"{OTX_API}/indicators/{ind_type}/{indicator}/general"

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

        lines: list[str] = []
        pulse_count = data.get("pulse_info", {}).get("count", 0)
        reputation = data.get("reputation", 0)
        country = data.get("country_name") or data.get("country_code") or "N/A"
        asn = data.get("asn") or "N/A"
        country_code = data.get("country_code") or "N/A"

        lines.append(f"Indicator: {indicator}")
        lines.append(f"Type: {ind_type}")
        lines.append(f"Pulses: {pulse_count}")
        lines.append(f"Reputation: {reputation}")
        lines.append(f"Country: {country} ({country_code})")
        lines.append(f"ASN: {asn}")

        if data.get("sections"):
            lines.append(f"Sections: {', '.join(data['sections'])}")

        pulse_info = data.get("pulse_info", {})
        pulses = pulse_info.get("pulses", [])
        if pulses:
            lines.append("\nRecent Pulses:")
            for pulse in pulses[:10]:
                name = pulse.get("name", "?")
                created = pulse.get("created", "?")
                tags = pulse.get("tags", [])
                lines.append(f"  - {name}")
                lines.append(f"    Created: {created}")
                if tags:
                    lines.append(f"    Tags: {', '.join(tags[:5])}")

        related = data.get("related", {})
        related_indicators = related.get("indicators", [])
        if related_indicators:
            lines.append("\nRelated Indicators:")
            for ind in related_indicators[:10]:
                val = ind.get("indicator", "?")
                ind_type_rel = ind.get("type", "?")
                lines.append(f"  {ind_type_rel}: {val}")

        result_text = "\n".join(lines) if lines else "No data found."
        return Result(success=True, data={"result": result_text})
