from __future__ import annotations

import math
from collections import Counter

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = Counter(text)
    length = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _classify_entropy(entropy: float) -> str:
    if entropy < 2.0:
        return "low"
    if entropy < 3.5:
        return "medium"
    if entropy < 4.5:
        return "high"
    return "very high"


class TextEntropyTool(Tool):
    metadata = ToolMetadata(
        name="text_entropy",
        description="Shannon entropy calculator for text analysis",
        category="osint.util.text",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#9B59B6",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "text": OptionDefinition(
                name="text",
                description="Input text to analyze",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        text = context.options.get("text") or ""
        if not text:
            return Result(success=False, error="Option 'text' is required.")

        unique_chars = len(set(text))
        entropy = _shannon_entropy(text)
        classification = _classify_entropy(entropy)

        output = (
            f"Input:          {text}\n"
            f"Length:         {len(text)}\n"
            f"Unique chars:   {unique_chars}\n"
            f"Entropy:        {entropy:.4f}\n"
            f"Classification: {classification}"
        )

        return Result(
            success=True,
            data={"result": output},
        )
