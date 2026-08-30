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

DNS_TYPES = ("ALL", "A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "SRV", "CAA")
DNS_TYPE_MAP = {"ALL": "255"}
DNS_RECORD_NAMES = {
    1: "A",
    2: "NS",
    5: "CNAME",
    6: "SOA",
    13: "HINFO",
    15: "MX",
    16: "TXT",
    28: "AAAA",
    33: "SRV",
    39: "DNAME",
    43: "DS",
    46: "RRSIG",
    48: "DNSKEY",
    52: "TLSA",
    65: "HTTPS",
    257: "CAA",
}
DNS_RCODE_NAMES = {
    0: "NOERROR",
    1: "FORMERR",
    2: "SERVFAIL",
    3: "NXDOMAIN",
    4: "NOTIMP",
    5: "REFUSED",
    6: "YXDOMAIN",
    7: "YXRRSET",
    8: "NXRRSET",
    9: "NOTAUTH",
    10: "NOTZONE",
}

# Types to query when ALL is requested (for Cloudflare workaround)
ALL_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "SRV", "CAA"]

PROVIDERS = {
    "cloudflare": "https://cloudflare-dns.com/dns-query",
    "google": "https://dns.google/resolve",
}


class DNSLookupTool(Tool):
    metadata = ToolMetadata(
        name="dns_lookup",
        description="DNS record lookup via Cloudflare or Google DNS-over-HTTPS",
        category="osint.recon.dns",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#4A9EFF",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "domain": OptionDefinition(
                name="domain",
                description="Target domain to query",
                required=True,
            ),
            "type": OptionDefinition(
                name="type",
                description="DNS record type (ALL returns every type)",
                required=False,
                default="ALL",
                choices=list(DNS_TYPES),
            ),
            "provider": OptionDefinition(
                name="provider",
                description="DNS-over-HTTPS provider",
                required=False,
                default="cloudflare",
                choices=list(PROVIDERS),
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def _query(
        self, client: HttpClient, base_url: str, domain: str, rtype: str
    ) -> tuple[int, list[dict]]:
        """Query DNS and return (status, answers)."""
        url = f"{base_url}?name={domain}&type={rtype}"
        resp = client.get(url, timeout=30)
        data = json.loads(resp.content)
        status = data.get("Status", 0)
        answers = data.get("Answer") or []
        return status, answers

    def execute(self, context: ExecutionContext) -> Result:
        domain = context.options.get("domain") or ""
        if not domain:
            return Result(success=False, error="Option 'domain' is required.")

        record_type = context.options.get("type") or "ALL"
        provider = context.options.get("provider") or "cloudflare"
        base_url = PROVIDERS.get(provider, PROVIDERS["cloudflare"])

        headers = {"Accept": "application/dns-json"} if provider == "cloudflare" else None
        client = HttpClient(headers=headers)

        try:
            all_answers: list[dict] = []
            worst_status = 0

            if record_type == "ALL" and provider == "cloudflare":
                # Cloudflare doesn't support type=ANY (255) — query each type
                for t in ALL_TYPES:
                    status, answers = self._query(client, base_url, domain, t)
                    if status != 0 and worst_status == 0:
                        worst_status = status
                    all_answers.extend(answers)
            elif record_type == "ALL":
                # Google supports type=255
                status, answers = self._query(client, base_url, domain, "255")
                worst_status = status
                all_answers.extend(answers)
            else:
                api_type = DNS_TYPE_MAP.get(record_type, record_type)
                status, answers = self._query(client, base_url, domain, api_type)
                worst_status = status
                all_answers.extend(answers)

        except Exception as exc:
            return Result(success=False, error=f"Request failed: {exc}")
        finally:
            client.close()

        if worst_status != 0:
            rcode_name = DNS_RCODE_NAMES.get(worst_status, f"UNKNOWN({worst_status})")
            if not all_answers:
                    msg = f"DNS query returned {rcode_name}"
                    msg += f" (status {worst_status}) for {domain}."
                    return Result(
                        success=True,
                        data={"result": msg},
                    )

        if not all_answers:
            return Result(
                success=True,
                data={"result": f"No {record_type} records found for {domain}."},
            )

        # Deduplicate answers (Cloudflare ALL queries may overlap)
        seen: set[tuple] = set()
        unique: list[dict] = []
        for ans in all_answers:
            key = (ans.get("name"), ans.get("type"), ans.get("data"))
            if key not in seen:
                seen.add(key)
                unique.append(ans)

        lines: list[str] = []
        for ans in unique:
            name = ans.get("name", "?").rstrip(".")
            ttl = ans.get("TTL", "?")
            rtype_num = ans.get("type", 0)
            rtype = DNS_RECORD_NAMES.get(rtype_num, str(rtype_num))
            rdata = ans.get("data", "?")
            lines.append(f"  {name}  {rtype:<8}  TTL={ttl}  {rdata}")

        header = f"{record_type} records for {domain} ({provider})"
        result_text = header + "\n" + "\n".join(lines)
        return Result(success=True, data={"result": result_text})
