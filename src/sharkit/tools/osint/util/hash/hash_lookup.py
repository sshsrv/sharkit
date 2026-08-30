from __future__ import annotations

import hashlib

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)


class HashLookupTool(Tool):
    metadata = ToolMetadata(
        name="hash_lookup",
        description="Generate cryptographic hashes from text",
        category="osint.util.hash",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#FF4444",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "text": OptionDefinition(
                name="text",
                description="Input text to hash",
                required=True,
            ),
            "algorithm": OptionDefinition(
                name="algorithm",
                description="Hash algorithm",
                required=False,
                default="sha256",
                choices=["md5", "sha1", "sha256"],
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        text = context.options.get("text") or ""
        if not text:
            return Result(success=False, error="Option 'text' is required.")

        algorithm = context.options.get("algorithm") or "sha256"
        valid_algorithms = {"md5", "sha1", "sha256"}
        if algorithm not in valid_algorithms:
            choices = ", ".join(sorted(valid_algorithms))
            return Result(
                success=False,
                error=f"Invalid algorithm '{algorithm}'. Choose from: {choices}",
            )

        h = hashlib.new(algorithm)
        h.update(text.encode("utf-8"))
        hash_value = h.hexdigest()

        output = (
            f"Algorithm:  {algorithm}\n"
            f"Input:      {text}\n"
            f"Hash:       {hash_value}"
        )

        return Result(
            success=True,
            data={"result": output},
        )
