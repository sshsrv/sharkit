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

HASHLOOKUP_API = "https://hashlookup.circl.lu/lookup"


class CIRCLHashlookupTool(Tool):
    metadata = ToolMetadata(
        name="circl_hashlookup",
        description="Look up file hashes (MD5/SHA1) against CIRCL's hashlookup database",
        category="osint.util.hash",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#3498DB",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "hash": OptionDefinition(
                name="hash",
                description="File hash to look up (MD5 or SHA1)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        file_hash = context.options.get("hash") or ""
        if not file_hash:
            return Result(success=False, error="Option 'hash' is required.")

        url = f"{HASHLOOKUP_API}/{file_hash}"
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

        if data.get("known") is False or data.get("response") == "unknown":
            lines: list[str] = [
                f"Hash lookup for {file_hash}:",
                "  Status: Unknown",
            ]
        else:
            lines = [
                f"Hash lookup for {file_hash}:",
                "  Status: Known",
                f"  Filename: {data.get('Representation', 'N/A')}",
                f"  Source: {data.get('source', 'N/A')}",
                f"  File size: {data.get('fileSize', 'N/A')} bytes",
                f"  MD5: {data.get('MD5', 'N/A')}",
                f"  SHA-1: {data.get('SHA-1', 'N/A')}",
            ]

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
