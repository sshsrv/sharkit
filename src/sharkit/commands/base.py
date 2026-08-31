from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class CommandContext:
    session: dict[str, Any] = field(default_factory=dict)
    tools: list[Any] = field(default_factory=list)
    current_tool: str | None = None
    output: Any = None


class Command(ABC):
    name: str
    aliases: ClassVar[list[str]] = []
    description: str = ""
    usage: str = ""
    options: ClassVar[list[tuple[str, str]]] = []
    notes: str = ""

    @abstractmethod
    def execute(self, context: CommandContext, args: list[str]) -> str | None: ...

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        return True, None

    def format_help(self) -> str:
        usage = self.usage or self.name
        lines = [f"Usage: {usage}", "", self.description]
        if self.notes:
            lines.append("")
            lines.append(self.notes)
        if self.options:
            lines.append("")
            lines.append("OPTIONS:")
            lines.append("")
            max_flag = max((len(f) for f, _ in self.options), default=0)
            for flag, desc in self.options:
                lines.append(f"    {flag:<{max_flag}}  {desc}")
        return "\n".join(lines)
