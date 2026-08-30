from __future__ import annotations

import json

import httpx

from sharkit import __version__
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

URLHAUS_API = "https://urlhaus-api.abuse.ch/v1"
USER_AGENT = f"sharkit/{__version__}"


class URLhausCheckTool(Tool):
    metadata = ToolMetadata(
        name="urlhaus_check",
        description="Check URLs, hosts, or tags against URLhaus threat database",
        category="osint.recon.domain",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E74C3C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "query": OptionDefinition(
                name="query",
                description="URL, domain, or tag to search",
                required=True,
            ),
            "mode": OptionDefinition(
                name="mode",
                description="Search mode: url, host, or tag",
                required=False,
                default="url",
                choices=["url", "host", "tag"],
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        query = context.options.get("query") or ""
        if not query:
            return Result(success=False, error="Option 'query' is required.")

        mode = context.options.get("mode") or "url"
        endpoints = {
            "url": f"{URLHAUS_API}/url/",
            "host": f"{URLHAUS_API}/host/",
            "tag": f"{URLHAUS_API}/tag/",
        }
        url = endpoints[mode]
        payload = {mode: query}

        client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=30,
        )
        try:
            resp = client.post(url, data=payload)
        except Exception as exc:
            return Result(success=False, error=f"Request failed: {exc}")
        finally:
            client.close()

        try:
            data = json.loads(resp.content)
        except Exception:
            return Result(
                success=False,
                error=f"Failed to parse response (status {resp.status_code})",
            )

        if data.get("query_status") == "no_results":
            return Result(success=True, data={"result": "No results found."})

        if data.get("query_status") == "invalid_url":
            return Result(success=False, error="Invalid URL provided.")

        lines: list[str] = []

        if mode == "url":
            for entry in data.get("urls", []):
                lines.append(f"URL: {entry.get('url', '?')}")
                lines.append(f"  Status: {entry.get('url_status', '?')}")
                lines.append(f"  Threat: {entry.get('threat', '?')}")
                lines.append(f"  Tags: {entry.get('tags', [])}")
                lines.append(f"  Date Added: {entry.get('date_added', '?')}")
                lines.append(f"  Reporter: {entry.get('reporter', '?')}")
                lines.append(f"  Larted: {entry.get('larted', '?')}")
                lines.append("")

        elif mode == "host":
            lines.append(f"Host: {data.get('host', query)}")
            lines.append(f"URLs Online: {data.get('urls_online', '?')}")
            lines.append(f"URLs Total: {data.get('urls_total', '?')}")
            urls = data.get("urls", [])
            if urls:
                lines.append("\nRecent URLs:")
                for entry in urls[:20]:
                    lines.append(f"  {entry.get('url', '?')} — {entry.get('url_status', '?')}")
            lines.append("")

        elif mode == "tag":
            tag = data.get("tag", query)
            count = data.get("urls_online", "?")
            lines.append(f"Tag: {tag}")
            lines.append(f"URLs Online: {count}")
            urls = data.get("urls", [])
            if urls:
                lines.append("\nMatching URLs:")
                for entry in urls[:20]:
                    lines.append(f"  {entry.get('url', '?')} — {entry.get('url_status', '?')}")
            lines.append("")

        result_text = "\n".join(lines) if lines else "No data found."
        return Result(success=True, data={"result": result_text})
