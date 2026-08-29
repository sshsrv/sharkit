from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

from sharkit.modules.base import Module, ModuleMetadata


def discover_modules(modules_dir: Path) -> list[tuple[type[Module], str | None]]:
    module_classes: list[tuple[type[Module], str | None]] = []

    if not modules_dir.is_dir():
        return module_classes

    for py_file in sorted(modules_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue

        loaded = _import_file(py_file)
        if loaded is None:
            continue

        for attr_name in dir(loaded):
            attr = getattr(loaded, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, Module)
                and attr is not Module
                and _has_valid_metadata(attr)
            ):
                relative_path = str(py_file.relative_to(modules_dir).with_suffix(""))
                module_classes.append((attr, relative_path))

    return module_classes


def _import_file(file_path: Path) -> object | None:
    module_name = f"sharkit._dynamic.{file_path.stem}"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception:
        sys.modules.pop(module_name, None)
        return None


def _has_valid_metadata(cls: type[Module]) -> bool:
    metadata = getattr(cls, "metadata", None)
    return isinstance(metadata, ModuleMetadata)
