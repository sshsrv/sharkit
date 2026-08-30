from __future__ import annotations

from sharkit.commands.registry import CommandRegistry
from sharkit.tools.base import OptionDefinition
from sharkit.tools.registry import ToolRegistry


class CompletionEngine:
    def __init__(self) -> None:
        self._cached_tool: str | None = None
        self._cached_options: dict[str, OptionDefinition] | None = None

    def _load_options(
        self, tool_registry: ToolRegistry, current_tool: str
    ) -> dict[str, OptionDefinition]:
        if current_tool == self._cached_tool and self._cached_options is not None:
            return self._cached_options
        tool_cls = tool_registry.get_tool(current_tool)
        if tool_cls is None:
            self._cached_tool = None
            self._cached_options = None
            return {}
        instance = tool_cls()
        self._cached_options = instance.get_options()
        self._cached_tool = current_tool
        return self._cached_options

    def get_completions(
        self,
        text: str,
        command_registry: CommandRegistry,
        tool_registry: ToolRegistry,
        current_tool: str | None,
    ) -> list[str]:
        text_lower = text.lower()

        if text_lower.startswith("use "):
            prefix = text_lower[4:]
            return sorted(
                p for p in tool_registry.get_all_tools() if p.lower().startswith(prefix)
            )

        if text_lower.startswith("show "):
            prefix = text_lower[5:]
            return sorted(s for s in ("all", "osint", "humint", "options") if s.startswith(prefix))

        if text_lower.startswith("set ") or text_lower.startswith("unset "):
            if current_tool is None:
                return []
            is_set = text_lower.startswith("set ")
            body = text[4:] if is_set else text[6:]
            parts = body.split(None, 1)

            try:
                options = self._load_options(tool_registry, current_tool)
            except Exception:
                return []

            if len(parts) < 2:
                prefix = parts[0] if parts else ""
                exact = options.get(prefix)
                if exact and exact.choices:
                    return list(exact.choices)
                elif exact and exact.type == "bool":
                    return ["true", "false"]
                return sorted(k for k in options if k.lower().startswith(prefix))

            option_name = parts[0]
            value_prefix = parts[1]
            opt = options.get(option_name)
            if opt is None or not opt.choices:
                return []
            return sorted(c for c in opt.choices if c.lower().startswith(value_prefix.lower()))

        if text_lower.startswith("install "):
            prefix = text_lower[8:]
            return sorted(
                p for p in tool_registry.get_all_tools() if p.lower().startswith(prefix)
            )

        if text_lower.startswith("upgrade ") or text_lower.startswith("update "):
            parts = text_lower.split(" ", 1)
            prefix = parts[1] if len(parts) > 1 else ""
            return sorted(
                p for p in tool_registry.get_all_tools() if p.lower().startswith(prefix)
            )

        if text_lower.startswith("remove ") or text_lower.startswith("uninstall "):
            parts = text_lower.split(" ", 1)
            prefix = parts[1] if len(parts) > 1 else ""
            return sorted(
                p for p in tool_registry.get_all_tools() if p.lower().startswith(prefix)
            )

        return command_registry.get_completions(text_lower)
