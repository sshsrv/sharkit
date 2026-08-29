from __future__ import annotations

import re
from pathlib import Path

from sharkit.config.paths import get_history_file
from sharkit.exceptions import ConfigurationError

_SENSITIVE_PATTERNS = re.compile(
    r"(password|passwd|token|api[_-]?key|secret|auth|credential)",
    re.IGNORECASE,
)


class HistoryManager:
    _history_file: Path

    def __init__(self) -> None:
        self._history_file = get_history_file()
        self._ensure_file()

    def _ensure_file(self) -> None:
        try:
            if not self._history_file.exists():
                self._history_file.parent.mkdir(parents=True, exist_ok=True)
                self._history_file.touch()
        except OSError as exc:
            raise ConfigurationError(
                f"Failed to initialize history file: {exc}"
            ) from exc

    def _read_lines(self) -> list[str]:
        try:
            content = self._history_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigurationError(f"Failed to read history file: {exc}") from exc
        return [line for line in content.splitlines() if line.strip()]

    def _write_lines(self, lines: list[str]) -> None:
        content = "\n".join(lines)
        if content:
            content += "\n"
        try:
            self._history_file.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ConfigurationError(f"Failed to write history file: {exc}") from exc

    def _is_sensitive(self, command: str) -> bool:
        return bool(_SENSITIVE_PATTERNS.search(command))

    def add_command(self, command: str) -> None:
        if command[:1].isspace():
            return
        stripped = command.strip()
        if not stripped:
            return
        if self._is_sensitive(stripped):
            return
        lines = self._read_lines()
        if lines and lines[-1] == stripped:
            return
        lines.append(stripped)
        self._write_lines(lines)

    def get_history(self, limit: int = 100) -> list[str]:
        lines = self._read_lines()
        commands: list[str] = []
        for line in lines:
            if line.startswith("#"):
                continue
            if line.startswith("+"):
                line = line[1:]
            if line.strip():
                commands.append(line)
        return commands[-limit:]

    def search(self, query: str) -> list[str]:
        lines = self._read_lines()
        query_lower = query.lower()
        return [line for line in lines if query_lower in line.lower()]

    def clear(self) -> None:
        self._write_lines([])
