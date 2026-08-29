from __future__ import annotations

PROMPT_STYLE = "class:prompt"
MODULE_STYLE = "class:module"


class PromptRenderer:
    def default_prompt(self) -> str:
        return "shark > "

    def module_prompt(self, module_name: str) -> str:
        return f"shark ({module_name}) > "

    def render(self, prompt: str) -> list[tuple[str, str]]:
        if "(" in prompt and ")" in prompt:
            before, rest = prompt.split("(", 1)
            module_name, after = rest.split(")", 1)
            return [
                (PROMPT_STYLE, before),
                ("", "("),
                (MODULE_STYLE, module_name),
                ("", ")"),
                ("", after),
            ]
        return [(PROMPT_STYLE, prompt)]
