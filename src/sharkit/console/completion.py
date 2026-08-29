from __future__ import annotations

from sharkit.commands.registry import CommandRegistry
from sharkit.modules.registry import ModuleRegistry


class CompletionEngine:
    def get_completions(
        self,
        text: str,
        command_registry: CommandRegistry,
        module_registry: ModuleRegistry,
        current_module: str | None,
    ) -> list[str]:
        text_lower = text.lower()

        if text_lower.startswith("use "):
            prefix = text_lower[4:]
            return sorted(
                p for p in module_registry.get_all_modules() if p.lower().startswith(prefix)
            )

        if text_lower.startswith("show "):
            prefix = text_lower[5:]
            return sorted(s for s in ("options", "tools") if s.startswith(prefix))

        if text_lower.startswith("set ") or text_lower.startswith("unset "):
            if current_module is None:
                return []
            try:
                module_cls = module_registry.get_module(current_module)
                if module_cls is None:
                    return []
                instance = module_cls()
                options = instance.get_options()
                prefix = text_lower[4:] if text_lower.startswith("set ") else text_lower[6:]
                return sorted(k for k in options if k.lower().startswith(prefix))
            except Exception:
                return []

        return command_registry.get_completions(text_lower)
