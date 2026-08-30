from __future__ import annotations

import os
from pathlib import Path

from sharkit.config.paths import (
    get_cache_dir,
    get_config_dir,
    get_config_file,
    get_data_dir,
    get_history_file,
)
from sharkit.exceptions import ConfigurationError


class ConfigManager:
    _config: dict[str, str]
    _config_file: Path

    def __init__(self) -> None:
        self._config = {}
        self._config_file = get_config_file()
        self._ensure_directory_structure()
        if self._config_file.exists():
            self._load()

    def _ensure_directory_structure(self) -> None:
        for path_func in (get_config_dir, get_cache_dir, get_data_dir):
            path = path_func()
            path.mkdir(parents=True, exist_ok=True)
        history_file = get_history_file()
        if not history_file.exists():
            history_file.touch()

    def _load(self) -> None:
        try:
            content = self._config_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ConfigurationError(f"Failed to read config file: {exc}") from exc

        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigurationError(
                    f"Invalid config syntax at line {line_number}: {raw_line!r}"
                )
            key, _, value = line.partition("=")
            self._config[key.strip()] = value.strip()

    def _save(self) -> None:
        try:
            tmp = self._config_file.with_suffix(".tmp")
            lines = [f"{k}={v}" for k, v in sorted(self._config.items())]
            tmp.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")
            os.replace(tmp, self._config_file)
        except OSError as exc:
            raise ConfigurationError(f"Failed to save config: {exc}") from exc

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._config.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._config[key] = value
        self._save()

    def has(self, key: str) -> bool:
        return key in self._config

    def keys(self) -> list[str]:
        return list(self._config.keys())

    def items(self) -> list[tuple[str, str]]:
        return list(self._config.items())
