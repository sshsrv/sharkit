from dataclasses import replace
from pathlib import Path

import pytest

from sharkit.modules.base import ExecutionContext, Module, ModuleMetadata, OptionDefinition, Result
from sharkit.modules.registry import ModuleRegistry


class MockModule(Module):
    metadata = ModuleMetadata(
        name="mock",
        description="Mock module for testing",
        category="testing",
        author="Test",
        version="0.1.0",
        safety="safe",
    )

    def __init__(self):
        self._options = {
            "target": OptionDefinition(
                name="target",
                description="Target to test",
                required=True,
                default=None,
                value=None,
            )
        }

    def get_metadata(self):
        return self.metadata

    def get_options(self):
        return self._options

    def set_option(self, key, value):
        if key not in self._options:
            raise ValueError(f'Option "{key}" not found.')
        self._options[key] = replace(self._options[key], value=value)

    def execute(self, context):
        return Result(success=True, data={"target": self._options["target"].value}, error=None)


def test_module_metadata():
    module = MockModule()
    metadata = module.get_metadata()
    assert metadata.name == "mock"
    assert metadata.category == "testing"
    assert metadata.safety == "safe"


def test_module_options():
    module = MockModule()
    options = module.get_options()
    assert "target" in options
    assert options["target"].required is True


def test_module_set_option():
    module = MockModule()
    module.set_option("target", "localhost")
    assert module.get_options()["target"].value == "localhost"


def test_module_set_invalid_option():
    module = MockModule()
    with pytest.raises(ValueError):
        module.set_option("nonexistent", "value")


def test_module_execute():
    module = MockModule()
    module.set_option("target", "localhost")
    context = ExecutionContext(
        module_name="mock",
        options={"target": "localhost"},
        config_dir=Path("/tmp"),
    )
    result = module.execute(context)
    assert result.success is True
    assert result.data["target"] == "localhost"


def test_registry_register_and_get():
    registry = ModuleRegistry()
    registry.register_module(MockModule)
    module_class = registry.get_module("mock")
    assert module_class is not None
    assert module_class.metadata.name == "mock"


def test_registry_get_nonexistent():
    registry = ModuleRegistry()
    assert registry.get_module("nonexistent") is None


def test_registry_list_modules():
    registry = ModuleRegistry()
    registry.register_module(MockModule)
    modules = registry.list_modules()
    assert len(modules) == 1
    assert modules[0].name == "mock"


def test_registry_search():
    registry = ModuleRegistry()
    registry.register_module(MockModule)
    results = registry.search_modules("mock")
    assert len(results) == 1
    results = registry.search_modules("nonexistent")
    assert len(results) == 0
