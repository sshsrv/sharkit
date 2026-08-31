from __future__ import annotations

import base64

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

MODES = ("encode", "decode")


class Base64Tool(Tool):
    metadata = ToolMetadata(
        name="base64_tool",
        description="Base64 encode or decode text",
        category="osint.util.text",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#F39C12",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "text": OptionDefinition(
                name="text",
                description="Input text to encode or decode",
                required=True,
            ),
            "mode": OptionDefinition(
                name="mode",
                description="Operation mode",
                required=False,
                default="decode",
                choices=list(MODES),
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        text = (context.options.get("text") or "").strip()
        if not text:
            return Result(success=False, error="Option 'text' is required.")

        mode = (context.options.get("mode") or "decode").strip().lower()

        if mode == "encode":
            try:
                encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
            except Exception as exc:
                return Result(success=False, error=f"Encoding failed: {exc}")
            output = (
                f"Mode:    encode\n"
                f"Input:   {text}\n"
                f"Output:  {encoded}"
            )
        elif mode == "decode":
            try:
                decoded = base64.b64decode(text).decode("utf-8")
            except Exception as exc:
                return Result(success=False, error=f"Decoding failed: {exc}")
            output = (
                f"Mode:    decode\n"
                f"Input:   {text}\n"
                f"Output:  {decoded}"
            )
        else:
            return Result(
                success=False,
                error=f"Invalid mode '{mode}'. Choose: {', '.join(MODES)}",
            )

        return Result(success=True, data={"result": output})
