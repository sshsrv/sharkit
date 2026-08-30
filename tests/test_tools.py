from dataclasses import replace
from pathlib import Path

import pytest

from sharkit.tools.base import ExecutionContext, OptionDefinition, Result, Tool, ToolMetadata
from sharkit.tools.registry import ToolRegistry


class MockTool(Tool):
    metadata = ToolMetadata(
        name="mock",
        description="Mock tool for testing",
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


def test_tool_metadata():
    tool = MockTool()
    metadata = tool.get_metadata()
    assert metadata.name == "mock"
    assert metadata.category == "testing"
    assert metadata.safety == "safe"


def test_tool_options():
    tool = MockTool()
    options = tool.get_options()
    assert "target" in options
    assert options["target"].required is True


def test_tool_set_option():
    tool = MockTool()
    tool.set_option("target", "localhost")
    assert tool.get_options()["target"].value == "localhost"


def test_tool_set_invalid_option():
    tool = MockTool()
    with pytest.raises(ValueError):
        tool.set_option("nonexistent", "value")


def test_tool_execute():
    tool = MockTool()
    tool.set_option("target", "localhost")
    context = ExecutionContext(
        tool_name="mock",
        options={"target": "localhost"},
        config_dir=Path("/tmp"),
    )
    result = tool.execute(context)
    assert result.success is True
    assert result.data["target"] == "localhost"


def test_registry_register_and_get():
    registry = ToolRegistry()
    registry.register_tool(MockTool)
    tool_class = registry.get_tool("mock")
    assert tool_class is not None
    assert tool_class.metadata.name == "mock"


def test_registry_get_nonexistent():
    registry = ToolRegistry()
    assert registry.get_tool("nonexistent") is None


def test_registry_list_tools():
    registry = ToolRegistry()
    registry.register_tool(MockTool)
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "mock"


def test_registry_search():
    registry = ToolRegistry()
    registry.register_tool(MockTool)
    results = registry.search_tools("mock")
    assert len(results) == 1
    results = registry.search_tools("nonexistent")
    assert len(results) == 0
