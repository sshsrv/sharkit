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


class PSBDMPTool(Tool):
    metadata = ToolMetadata(
        name="psbdmp",
        description="Search for pastes containing a query on Pastebin DMP",
        category="osint.humint.pastes",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#1ABC9C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "query": OptionDefinition(
                name="query",
                description="Search query (email, domain, username, etc.)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        query = context.options.get("query") or ""
        if not query:
            return Result(success=False, error="Option 'query' is required.")

        url = f"https://psbdmp.ws/api/v3/search/{query}"
        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            return Result(success=False, error="Invalid JSON response from API.")

        error = data.get("error")
        if error:
            return Result(success=False, error=f"API error: {error}")

        pastes = data.get("data", [])

        lines: list[str] = []
        lines.append(f"Query: {query}")
        lines.append(f"Pastes found: {len(pastes)}")

        if pastes:
            lines.append("\n--- Pastes ---")
            for paste in pastes:
                paste_id = paste.get("id", "Unknown")
                title = paste.get("title", "Untitled")
                url_paste = paste.get("url", f"https://psbdmp.ws/{paste_id}")
                lines.append(f"  {title}")
                lines.append(f"    URL: {url_paste}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
