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


class LeakCheckTool(Tool):
    metadata = ToolMetadata(
        name="leak_check",
        description="Check if an email, username, or hash has been exposed in data breaches",
        category="osint.humint.leaks",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E67E22",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "query": OptionDefinition(
                name="query",
                description="Email, SHA256 hash (truncated 24 chars), or username (min 3 chars)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        query = context.options.get("query") or ""
        if not query:
            return Result(success=False, error="Option 'query' is required.")

        if len(query) < 3:
            return Result(
                success=False,
                error="Query must be at least 3 characters long.",
            )

        url = f"https://leakcheck.io/api/public?check={query}"
        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            return Result(success=False, error="Invalid JSON response from API.")

        success = data.get("success")
        if success is False or data.get("error"):
            error_msg = data.get("error", "Unknown error")
            return Result(success=False, error=f"API error: {error_msg}")

        found = data.get("found", 0)
        breaches = data.get("breaches", [])

        lines: list[str] = []
        lines.append(f"Query: {query}")
        lines.append(f"Breaches found: {found}")

        if breaches:
            lines.append("\n--- Breaches ---")
            for breach in breaches:
                name = breach.get("name", "Unknown")
                date = breach.get("date", "Unknown")
                fields = breach.get("fields", [])
                date_display = date if date else "Unknown date"
                lines.append(f"  [{date_display}] {name}")
                if fields:
                    lines.append(f"    Data exposed: {', '.join(fields)}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
