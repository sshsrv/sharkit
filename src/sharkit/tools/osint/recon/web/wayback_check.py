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

CDX_API = "https://web.archive.org/cdx/search/cdx"


class WaybackCheckTool(Tool):
    metadata = ToolMetadata(
        name="wayback_check",
        description="Check Wayback Machine for historical snapshots of a URL",
        category="osint.recon.web",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E67E22",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "url": OptionDefinition(
                name="url",
                description="Target URL to check in Wayback Machine",
                required=True,
            ),
            "limit": OptionDefinition(
                name="limit",
                description="Max results to show",
                required=False,
                default="20",
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        url = (context.options.get("url") or "").strip()
        if not url:
            return Result(success=False, error="Option 'url' is required.")

        limit_str = (context.options.get("limit") or "20").strip()
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 20

        api_url = (
            f"{CDX_API}?url={url}"
            f"&output=json&limit={limit}"
            f"&fl=timestamp,original,statuscode,mimetype"
        )

        with HttpClient() as client:
            try:
                resp = client.get(api_url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        if resp.status_code != 200:
            return Result(
                success=False,
                error=f"CDX API returned HTTP {resp.status_code}",
            )

        try:
            rows = json.loads(resp.content.decode("utf-8"))
        except Exception:
            return Result(success=False, error="Failed to parse CDX response as JSON.")

        if not rows:
            return Result(
                success=True,
                data={"result": "No snapshots found for this URL."},
            )

        header = rows[0]
        data_rows = rows[1:]

        if not data_rows:
            return Result(
                success=True,
                data={"result": "No snapshots found for this URL."},
            )

        timestamps = [r[header.index("timestamp")] for r in data_rows]
        originals = {r[header.index("original")] for r in data_rows}

        ts_idx = header.index("timestamp")
        url_idx = header.index("original")
        status_idx = header.index("statuscode")
        mime_idx = header.index("mimetype")

        out: list[str] = []
        out.append(f"=== Wayback Machine Snapshots: {url} ===")
        out.append(f"Snapshots found: {len(data_rows)}")
        out.append(f"Unique URLs: {len(originals)}")
        out.append(f"Date range: {timestamps[0]} - {timestamps[-1]}")
        out.append("")

        fmt = "{:<14} {:<50} {:<6} {}"
        out.append(fmt.format("Timestamp", "URL", "Status", "MIME"))
        out.append("-" * 90)

        for row in data_rows:
            ts = row[ts_idx]
            orig = row[url_idx]
            status = row[status_idx]
            mime = row[mime_idx]
            display_url = orig if len(orig) <= 50 else orig[:47] + "..."
            out.append(fmt.format(ts, display_url, status, mime))

        return Result(success=True, data={"result": "\n".join(out)})
