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

DNS_OVER_HTTPS = "https://dns.google/resolve?name={record}&type=TXT"

DKIM_SELECTORS = [
    "default._domainkey",
    "selector1._domainkey",
    "selector2._domainkey",
    "google._domainkey",
    "k1._domainkey",
]


def _dns_query(client: HttpClient, record: str) -> list[str]:
    """Query DNS-over-HTTPS for TXT records. Returns list of TXT strings."""
    url = DNS_OVER_HTTPS.format(record=record)
    try:
        response = client.get(url, timeout=10)
        if response.status_code >= 400:
            return []
    except Exception:
        return []
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        return []
    answers = data.get("Answer") or []
    return [a.get("data", "") for a in answers if a.get("type") == 16]


def _check_spf(client: HttpClient, domain: str) -> tuple[bool, str]:
    records = _dns_query(client, domain)
    for record in records:
        if "v=spf1" in record:
            return True, record
    return False, ""


def _check_dmarc(client: HttpClient, domain: str) -> tuple[bool, str]:
    dmarc_domain = f"_dmarc.{domain}"
    records = _dns_query(client, dmarc_domain)
    for record in records:
        if "v=DMARC1" in record:
            return True, record
    return False, ""


def _check_dkim(client: HttpClient, domain: str) -> tuple[bool, str]:
    for selector in DKIM_SELECTORS:
        record_name = f"{selector}.{domain}"
        records = _dns_query(client, record_name)
        for record in records:
            if "v=DKIM1" in record:
                return True, f"[selector={selector}] {record}"
    return False, ""


class EmailSecurityTool(Tool):
    metadata = ToolMetadata(
        name="email_security",
        description="Email security record checker (SPF, DMARC, DKIM)",
        category="osint.recon.email",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#FFD700",
    )

    def __init__(self) -> None:
        self._options = {
            "domain": OptionDefinition(
                name="domain",
                description="Target domain to check email security records",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        domain = context.options.get("domain") or ""
        if not domain:
            return Result(success=False, error="Option 'domain' is required.")

        lines = [f"  Email Security Records for {domain}", "  " + "-" * 40]

        try:
            with HttpClient() as client:
                spf_found, spf_value = _check_spf(client, domain)
                dmarc_found, dmarc_value = _check_dmarc(client, domain)
                dkim_found, dkim_value = _check_dkim(client, domain)
        except Exception as exc:
            return Result(success=False, error=f"Request failed: {exc}")

        lines.append("")
        lines.append("  SPF Record:")
        if spf_found:
            lines.append("    Status  : Found")
            lines.append(f"    Value   : {spf_value}")
        else:
            lines.append("    Status  : Not Found")

        lines.append("")
        lines.append("  DMARC Record:")
        if dmarc_found:
            lines.append("    Status  : Found")
            lines.append(f"    Value   : {dmarc_value}")
        else:
            lines.append("    Status  : Not Found")

        lines.append("")
        lines.append("  DKIM Record:")
        if dkim_found:
            lines.append("    Status  : Found")
            lines.append(f"    Value   : {dkim_value}")
        else:
            lines.append("    Status  : Not Found")

        return Result(success=True, data={"result": "\n".join(lines)})
