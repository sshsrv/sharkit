from __future__ import annotations

from sharkit.commands.registry import CommandRegistry
from sharkit.tools.registry import ToolRegistry


class CompletionEngine:
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
            return sorted(s for s in ("options", "tools") if s.startswith(prefix))

        if text_lower.startswith("set ") or text_lower.startswith("unset "):
            if current_tool is None:
                return []
            try:
                tool_cls = tool_registry.get_tool(current_tool)
                if tool_cls is None:
                    return []
                instance = tool_cls()
                options = instance.get_options()
                prefix = text_lower[4:] if text_lower.startswith("set ") else text_lower[6:]
                return sorted(k for k in options if k.lower().startswith(prefix))
            except Exception:
                return []

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
