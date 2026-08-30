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

HASH_DECRYPT_API = "https://api.hash-decrypt.io/v1"

VALID_TYPES = ("md5", "sha1", "sha256", "sha512")


class HashDecryptTool(Tool):
    metadata = ToolMetadata(
        name="hash_decrypt",
        description="Look up hash decryption results via hash-decrypt.io",
        category="osint.util.hash",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E74C3C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "hash": OptionDefinition(
                name="hash",
                description="The hash to look up",
                required=True,
            ),
            "type": OptionDefinition(
                name="type",
                description="Hash algorithm type",
                required=True,
                choices=list(VALID_TYPES),
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        file_hash = context.options.get("hash") or ""
        if not file_hash:
            return Result(success=False, error="Option 'hash' is required.")

        hash_type = (context.options.get("type") or "").strip().lower()
        if hash_type not in VALID_TYPES:
            choices = ", ".join(sorted(VALID_TYPES))
            return Result(
                success=False,
                error=f"Invalid type '{hash_type}'. Choose from: {choices}",
            )

        url = f"{HASH_DECRYPT_API}/{hash_type}/{file_hash}"
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

        if data.get("found"):
            lines: list[str] = [
                f"Hash decryption for {file_hash} ({hash_type}):",
                "  Status: Found",
                f"  Plaintext: {data.get('plaintext', 'N/A')}",
                f"  Algorithm: {data.get('algorithm', 'N/A')}",
            ]
        else:
            lines = [
                f"Hash decryption for {file_hash} ({hash_type}):",
                "  Status: Not found",
            ]

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
