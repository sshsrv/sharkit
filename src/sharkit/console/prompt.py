from __future__ import annotations

PROMPT_STYLE = "class:prompt"
MODULE_STYLE = "class:tool"


class PromptRenderer:
    def default_prompt(self) -> str:
        return "shark > "

    def tool_prompt(self, tool_name: str) -> str:
        if "/" in tool_name:
            parts = tool_name.split("/", 1)
            formatted = f"{parts[0]}({parts[1]})"
        else:
            formatted = tool_name
        return f"shark {formatted} > "

    def render(self, prompt: str, tool_name: str | None = None) -> list[tuple[str, str]]:
        if tool_name is not None and "/" in tool_name:
            cat, rest = tool_name.split("/", 1)
            before = "shark "
            after = " > "
            return [
                (PROMPT_STYLE, before),
                (MODULE_STYLE, cat),
                ("", "("),
                (MODULE_STYLE, rest),
                ("", ")"),
                ("", after),
            ]
        if "(" in prompt and ")" in prompt:
            before, rest = prompt.split("(", 1)
            tool_path, after = rest.split(")", 1)
            return [
                (PROMPT_STYLE, before),
                ("", "("),
                (MODULE_STYLE, tool_path),
                ("", ")"),
                (PROMPT_STYLE, after),
            ]
        return [(PROMPT_STYLE, prompt)]
