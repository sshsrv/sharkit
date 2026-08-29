from __future__ import annotations

from sharkit.exceptions import ModuleNotFoundError
from sharkit.modules.base import Module, ModuleMetadata


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, type[Module]] = {}
        self._paths: dict[str, str] = {}

    def register_module(self, module_class: type[Module], path: str | None = None) -> None:
        name = module_class.metadata.name
        self._modules[name] = module_class
        if path:
            self._paths[path] = name

    def get_module(self, key: str) -> type[Module] | None:
        module = self._modules.get(key)
        if module is not None:
            return module
        name = self._paths.get(key)
        if name is not None:
            return self._modules.get(name)
        return None

    def require_module(self, key: str) -> type[Module]:
        module = self.get_module(key)
        if module is None:
            raise ModuleNotFoundError(key)
        return module

    def list_modules(self) -> list[ModuleMetadata]:
        return [cls.metadata for cls in self._modules.values()]

    def search_modules(self, query: str) -> list[ModuleMetadata]:
        lower_query = query.lower()
        return [
            module.metadata
            for module in self._modules.values()
            if lower_query in module.metadata.name.lower()
            or lower_query in module.metadata.description.lower()
        ]

    def get_modules_by_category(self, category: str) -> list[ModuleMetadata]:
        lower_category = category.lower()
        return [
            module.metadata
            for module in self._modules.values()
            if module.metadata.category.lower() == lower_category
        ]

    def get_all_modules(self) -> dict[str, type[Module]]:
        result: dict[str, type[Module]] = {}
        pathed_names = set(self._paths.values())
        for name, cls in self._modules.items():
            if name not in pathed_names:
                result[name] = cls
        for path, name in self._paths.items():
            result[path] = self._modules[name]
        return result
