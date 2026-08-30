from __future__ import annotations

PROMPT_STYLE = "class:prompt"
MODULE_STYLE = "class:tool"


class PromptRenderer:
    def default_prompt(self) -> str:
        return "shark > "

    def tool_prompt(self, tool_name: str) -> str:
        return f"shark ({tool_name}) > "

    def render(self, prompt: str) -> list[tuple[str, str]]:
        if "(" in prompt and ")" in prompt:
            before, rest = prompt.split("(", 1)
            tool_name, after = rest.split(")", 1)
            return [
                (PROMPT_STYLE, before),
                ("", "("),
                (MODULE_STYLE, tool_name),
                ("", ")"),
                ("", after),
            ]
        return [(PROMPT_STYLE, prompt)]
