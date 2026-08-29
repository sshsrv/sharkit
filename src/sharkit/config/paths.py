from __future__ import annotations

from pathlib import Path

_BASE_DIR_NAME = "sharkit"


def _get_xdg_config_home() -> Path:
    import os

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def get_config_dir() -> Path:
    return _get_xdg_config_home() / _BASE_DIR_NAME


def get_config_file() -> Path:
    return get_config_dir() / "config"


def get_history_file() -> Path:
    return get_config_dir() / "history"


def get_cache_dir() -> Path:
    return get_config_dir() / "cache"


def get_data_dir() -> Path:
    return get_config_dir() / "data"
