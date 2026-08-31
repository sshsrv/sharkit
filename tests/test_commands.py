import pytest

from sharkit.commands.base import Command, CommandContext
from sharkit.commands.builtins import BUILTIN_COMMANDS, ShowCommand
from sharkit.commands.registry import CommandRegistry
from sharkit.console.completion import CompletionEngine
from sharkit.tools.base import ToolMetadata
from sharkit.tools.registry import ToolRegistry


class MockCommand(Command):
    name = "mock_cmd"
    aliases = ["mc"]
    description = "Mock command for testing"
    usage = "mock_cmd <arg>"

    def execute(self, context, args):
        return f"Executed with: {' '.join(args)}"


def test_command_metadata():
    cmd = MockCommand()
    assert cmd.name == "mock_cmd"
    assert cmd.aliases == ["mc"]
    assert cmd.description == "Mock command for testing"


def test_command_execute():
    cmd = MockCommand()
    context = CommandContext(
        session={},
        tools=[],
        current_tool=None,
        output=None,
    )
    result = cmd.execute(context, ["arg1", "arg2"])
    assert "arg1" in result
    assert "arg2" in result


def test_registry_register_and_get():
    registry = CommandRegistry()
    registry.register_command(MockCommand)
    cmd = registry.get_command("mock_cmd")
    assert cmd is not None
    assert cmd.name == "mock_cmd"


def test_registry_alias_resolution():
    registry = CommandRegistry()
    registry.register_command(MockCommand)
    cmd = registry.get_command("mc")
    assert cmd is not None
    assert cmd.name == "mock_cmd"


def test_registry_get_nonexistent():
    from sharkit.exceptions import CommandNotFoundError
    registry = CommandRegistry()
    with pytest.raises(CommandNotFoundError):
        registry.get_command("nonexistent")


def test_registry_list_commands():
    registry = CommandRegistry()
    registry.register_command(MockCommand)
    commands = registry.get_all_commands()
    assert len(commands) == 1


def test_registry_completions():
    registry = CommandRegistry()
    registry.register_command(MockCommand)
    completions = registry.get_completions("m")
    assert "mock_cmd" in completions
    assert "mc" in completions


def test_builtin_commands_count():
    assert len(BUILTIN_COMMANDS) == 18


def test_quit_is_alias_of_exit():
    from sharkit.commands.builtins import ExitCommand

    assert "quit" in ExitCommand.aliases


def test_builtin_commands_have_required_fields():
    for cmd_class in BUILTIN_COMMANDS:
        cmd = cmd_class()
        assert hasattr(cmd, "name")
        assert hasattr(cmd, "aliases")
        assert hasattr(cmd, "description")
        assert hasattr(cmd, "usage")
        assert cmd.name
        assert isinstance(cmd.aliases, list)


class MockRenderer:
    def __init__(self):
        self.tables = []

    def table(self, title, headers, rows):
        self.tables.append((title, headers, rows))


def _make_tool(path: str, category: str, description: str, name: str | None = None):
    class FakeTool:
        pass

    FakeTool.metadata = ToolMetadata(
        name=name or path.replace("/", "."),
        description=description,
        category=category,
        author="test",
        version="1.0.0",
    )
    return FakeTool


def test_show_all_uses_single_table():
    registry = ToolRegistry()
    registry.register_tool(
        _make_tool("humint/factcheck/truthcheck", "humint", "TruthCheck"),
        "humint/factcheck/truthcheck",
    )
    registry.register_tool(
        _make_tool("osint/recon/domains/dns_lookup", "osint.recon.dns", "DNS lookup"),
        "osint/recon/domains/dns_lookup",
    )
    registry.register_tool(
        _make_tool("osint/humint/social/socialscan", "osint.humint.social", "Social scan"),
        "osint/humint/social/socialscan",
    )

    renderer = MockRenderer()
    context = CommandContext(
        session={"tool_registry": registry, "renderer": renderer, "tool_manager": None},
        tools=[],
        current_tool=None,
        output=None,
    )

    result = ShowCommand().execute(context, ["all"])

    assert result is None
    assert len(renderer.tables) == 1
    assert renderer.tables[0][0] == "show > all"
    assert {row[0] for row in renderer.tables[0][2]} == {
        "humint/factcheck/truthcheck",
        "osint/recon/domains/dns_lookup",
        "osint/humint/social/socialscan",
    }


def test_show_humint_filters_to_humint_tools():
    registry = ToolRegistry()
    registry.register_tool(
        _make_tool("humint/factcheck/truthcheck", "humint", "TruthCheck"),
        "humint/factcheck/truthcheck",
    )
    registry.register_tool(
        _make_tool("osint/recon/domains/dns_lookup", "osint.recon.dns", "DNS lookup"),
        "osint/recon/domains/dns_lookup",
    )
    registry.register_tool(
        _make_tool("osint/humint/social/socialscan", "osint.humint.social", "Social scan"),
        "osint/humint/social/socialscan",
    )

    renderer = MockRenderer()
    context = CommandContext(
        session={"tool_registry": registry, "renderer": renderer, "tool_manager": None},
        tools=[],
        current_tool=None,
        output=None,
    )

    result = ShowCommand().execute(context, ["humint"])

    assert result is None
    assert len(renderer.tables) == 1
    assert renderer.tables[0][0] == "show > humint"
    assert {row[0] for row in renderer.tables[0][2]} == {
        "humint/factcheck/truthcheck",
        "osint/humint/social/socialscan",
    }


def test_show_geoint_filters_to_geoint_tools():
    registry = ToolRegistry()
    registry.register_tool(
        _make_tool("geoint/recon/wifi/mylnikov", "osint.recon.network", "Mylnikov"),
        "geoint/recon/wifi/mylnikov",
    )
    registry.register_tool(
        _make_tool("osint/recon/domains/dns_lookup", "osint.recon.dns", "DNS lookup"),
        "osint/recon/domains/dns_lookup",
    )

    renderer = MockRenderer()
    context = CommandContext(
        session={"tool_registry": registry, "renderer": renderer, "tool_manager": None},
        tools=[],
        current_tool=None,
        output=None,
    )

    result = ShowCommand().execute(context, ["geoint"])

    assert result is None
    assert len(renderer.tables) == 1
    assert renderer.tables[0][0] == "show > geoint"
    assert {row[0] for row in renderer.tables[0][2]} == {"geoint/recon/wifi/mylnikov"}


def test_completion_includes_geoint_for_show():
    engine = CompletionEngine()
    completions = engine.get_completions("show g", CommandRegistry(), ToolRegistry(), None)
    assert "geoint" in completions
