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

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class CVESearchTool(Tool):
    metadata = ToolMetadata(
        name="cve_search",
        description="Search CVE vulnerabilities via NIST NVD API",
        category="osint.recon.domain",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#C0392B",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "query": OptionDefinition(
                name="query",
                description="CVE ID (e.g. CVE-2024-1234) or keyword search",
                required=True,
            ),
            "limit": OptionDefinition(
                name="limit",
                description="Maximum number of results to return",
                required=False,
                default="10",
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        query = context.options.get("query") or ""
        if not query:
            return Result(success=False, error="Option 'query' is required.")

        limit_str = context.options.get("limit") or "10"
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 10

        params: dict[str, str] = {
            "resultsPerPage": str(min(limit, 50)),
        }

        if query.upper().startswith("CVE-"):
            params["cveId"] = query
        else:
            params["keywordSearch"] = query

        url = NVD_API + "?" + "&".join(f"{k}={v}" for k, v in params.items())
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

        total = data.get("totalResults", 0)
        vulnerabilities = data.get("vulnerabilities", [])

        if not vulnerabilities:
            return Result(success=True, data={"result": f"No CVEs found. Total results: {total}"})

        lines: list[str] = [f"Found {total} CVE(s) (showing {len(vulnerabilities)}):"]

        for vuln in vulnerabilities:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "?")
            descriptions = cve.get("descriptions", [])
            description = "N/A"
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "N/A")
                    break
            else:
                if descriptions:
                    description = descriptions[0].get("value", "N/A")

            published = cve.get("published", "?")
            last_modified = cve.get("lastModified", "?")

            metrics = cve.get("metrics", {})
            cvss_score = "N/A"
            severity = "N/A"
            cvss_v31 = metrics.get("cvssMetricV31", [])
            if cvss_v31:
                cvss_data = cvss_v31[0].get("cvssData", {})
                cvss_score = str(cvss_data.get("baseScore", "N/A"))
                severity = cvss_data.get("baseSeverity", "N/A")
            else:
                cvss_v2 = metrics.get("cvssMetricV2", [])
                if cvss_v2:
                    cvss_data = cvss_v2[0].get("cvssData", {})
                    cvss_score = str(cvss_data.get("baseScore", "N/A"))
                    severity = cvss_v2[0].get("baseSeverity", "N/A")

            lines.append("")
            lines.append(f"{'=' * 60}")
            lines.append(f"CVE: {cve_id}")
            lines.append(f"Severity: {severity} (CVSS: {cvss_score})")
            lines.append(f"Published: {published}")
            lines.append(f"Last Modified: {last_modified}")
            lines.append(f"Description: {description[:300]}")

            weaknesses = cve.get("weaknesses", [])
            if weaknesses:
                cwe_list = []
                for weakness in weaknesses:
                    for desc in weakness.get("description", []):
                        val = desc.get("value", "")
                        if val:
                            cwe_list.append(val)
                if cwe_list:
                    lines.append(f"CWE: {', '.join(cwe_list[:5])}")

            configurations = cve.get("configurations", [])
            if configurations:
                products = []
                for config in configurations:
                    for node in config.get("nodes", []):
                        for cpe_match in node.get("cpeMatch", []):
                            criteria = cpe_match.get("criteria", "")
                            if criteria:
                                parts = criteria.split(":")
                                if len(parts) >= 5:
                                    products.append(parts[4])
                unique_products = list(dict.fromkeys(products))
                if unique_products:
                    lines.append(f"Affected: {', '.join(unique_products[:5])}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
