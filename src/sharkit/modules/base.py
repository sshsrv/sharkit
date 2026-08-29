from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class OptionDefinition:
    name: str
    description: str
    required: bool = False
    default: str | None = None
    value: str | None = None


@dataclass(frozen=True)
class ModuleMetadata:
    name: str
    description: str
    category: str
    author: str
    version: str
    options: dict[str, OptionDefinition] = field(default_factory=dict)
    safety: str = "safe"


@dataclass(frozen=True)
class ExecutionContext:
    module_name: str
    options: dict[str, str]
    config_dir: Path


@dataclass(frozen=True)
class Result:
    success: bool
    data: dict[str, object] = field(default_factory=dict)
    error: str | None = None


class Module(ABC):
    metadata: ModuleMetadata

    def get_metadata(self) -> ModuleMetadata:
        return self.metadata

    @abstractmethod
    def get_options(self) -> dict[str, OptionDefinition]: ...

    @abstractmethod
    def set_option(self, key: str, value: str) -> None: ...

    @abstractmethod
    def execute(self, context: ExecutionContext) -> Result: ...
