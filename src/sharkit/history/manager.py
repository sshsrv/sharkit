from __future__ import annotations

import re
from pathlib import Path

from sharkit.config.paths import get_history_file
from sharkit.exceptions import ConfigurationError

_SENSITIVE_RE = re.compile(
    r"\b(password|passwd|token|api[_-]?key|secret|auth_token|credential)\b",
    re.IGNORECASE,
)

MAX_HISTORY = 10_000


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
        return bool(_SENSITIVE_RE.search(command))

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
        if len(lines) > MAX_HISTORY:
            lines = lines[-MAX_HISTORY:]
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

    def search(self, query: str, limit: int = 50) -> list[str]:
        lines = self._read_lines()
        query_lower = query.lower()
        results = []
        for line in reversed(lines):
            if not line:
                continue
            if line.startswith("#"):
                continue
            display = line[1:] if line.startswith("+") else line
            if query_lower in display.lower():
                results.append(display)
            if len(results) >= limit:
                break
        return results

    def clear(self) -> None:
        self._write_lines([])
