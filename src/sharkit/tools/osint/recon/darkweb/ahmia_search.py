from __future__ import annotations

import re

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

ONION_PATTERN = re.compile(r"[a-z2-7]{16,56}\.onion")


class AhmiaSearchTool(Tool):
    metadata = ToolMetadata(
        name="ahmia_search",
        description="Search for .onion hidden services on the Ahmia search engine",
        category="osint.humint.darkweb",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#34495E",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "query": OptionDefinition(
                name="query",
                description="Search query for hidden services",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        query = context.options.get("query") or ""
        if not query:
            return Result(success=False, error="Option 'query' is required.")

        url = f"https://ahmia.fi/search/?q={query}"
        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        html = resp.content.decode("utf-8", errors="replace")

        # Extract .onion addresses from HTML
        matches = ONION_PATTERN.findall(html)
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_onions: list[str] = []
        for onion in matches:
            if onion not in seen:
                seen.add(onion)
                unique_onions.append(onion)

        lines: list[str] = []
        lines.append(f"Query: {query}")
        lines.append(f"Hidden services found: {len(unique_onions)}")

        if unique_onions:
            lines.append("\n--- .onion Addresses ---")
            for onion in unique_onions:
                lines.append(f"  {onion}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
