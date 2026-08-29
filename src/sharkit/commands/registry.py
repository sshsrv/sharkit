from __future__ import annotations

from sharkit.commands.base import Command
from sharkit.exceptions import CommandNotFoundError


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, type[Command]] = {}
        self._aliases: dict[str, str] = {}

    def register_command(self, command_class: type[Command]) -> None:
        self._commands[command_class.name] = command_class
        for alias in command_class.aliases:
            self._aliases[alias] = command_class.name

    def get_command(self, name: str) -> type[Command]:
        canonical = self._aliases.get(name, name)
        command = self._commands.get(canonical)
        if command is None:
            raise CommandNotFoundError(name)
        return command

    def get_all_commands(self) -> list[type[Command]]:
        return list(self._commands.values())

    def get_command_names(self) -> list[str]:
        return sorted(self._commands.keys())

    def get_completions(self, prefix: str) -> list[str]:
        names = set(self._commands.keys()) | set(self._aliases.keys())
        return sorted(name for name in names if name.startswith(prefix))
