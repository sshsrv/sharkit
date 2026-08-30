from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path

from sharkit.tools.base import Tool, ToolMetadata


def discover_tools(tools_dir: Path) -> list[tuple[type[Tool], str | None]]:
    tool_classes: list[tuple[type[Tool], str | None]] = []

    if not tools_dir.is_dir():
        return tool_classes

    for py_file in sorted(tools_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue

        loaded = _import_file(py_file)
        if loaded is None:
            continue

        for attr_name in dir(loaded):
            attr = getattr(loaded, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, Tool)
                and attr is not Tool
                and _has_valid_metadata(attr)
            ):
                relative_path = str(py_file.relative_to(tools_dir).with_suffix(""))
                tool_classes.append((attr, relative_path))

    return tool_classes


def _import_file(file_path: Path) -> object | None:
    tool_name = f"sharkit._dynamic.{file_path.stem}"

    spec = importlib.util.spec_from_file_location(tool_name, file_path)
    if spec is None or spec.loader is None:
        return None

    try:
        tool = importlib.util.module_from_spec(spec)
        sys.modules[tool_name] = tool
        spec.loader.exec_module(tool)
        return tool
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Failed to load tool %s: %s", file_path, exc
        )
        sys.modules.pop(tool_name, None)
        return None


def _has_valid_metadata(cls: type[Tool]) -> bool:
    metadata = getattr(cls, "metadata", None)
    return isinstance(metadata, ToolMetadata)
