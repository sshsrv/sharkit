from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from sharkit.exceptions import ToolError


@dataclass(frozen=True)
class OptionDefinition:
    name: str
    description: str
    required: bool = False
    default: str | None = None
    value: str | None = None
    type: str = "str"
    choices: list[str] | None = None


_TRUE_VALUES = ("yes", "true", "enabled", "1", "on")
_FALSE_VALUES = ("no", "false", "disabled", "0", "off")


def parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"Cannot parse {value!r} as boolean (expected: yes/no/true/false/1/0)"
    )


@dataclass(frozen=True)
class ToolInstallSpec:
    git_url: str | None
    requirements_file: str | None = None
    pip_args: list[str] = field(default_factory=list)
    entry: str | None = None
    venv: bool = True


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    description: str
    category: str
    author: str
    version: str
    options: dict[str, OptionDefinition] = field(default_factory=dict)
    safety: str = "safe"
    install: ToolInstallSpec | None = None
    color: str | None = None


@dataclass(frozen=True)
class ExecutionContext:
    tool_name: str
    options: dict[str, str]
    config_dir: Path
    renderer: Any | None = None


@dataclass(frozen=True)
class Result:
    success: bool
    data: dict[str, object] = field(default_factory=dict)
    error: str | None = None


class Tool(ABC):
    metadata: ToolMetadata

    def get_metadata(self) -> ToolMetadata:
        return self.metadata

    @abstractmethod
    def get_options(self) -> dict[str, OptionDefinition]: ...

    def set_option(self, key: str, value: str) -> None:
        options = self.get_options()
        opt = options.get(key)
        if opt is None:
            raise ToolError(f'Option "{key}" not found.')
        if opt.choices and value not in opt.choices:
            raise ToolError(
                f'Value "{value}" is not in choices: {", ".join(opt.choices)}'
            )
        options[key] = replace(opt, value=value)

    @abstractmethod
    def execute(self, context: ExecutionContext) -> Result: ...
