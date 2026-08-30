import pytest

from sharkit.commands.base import Command, CommandContext
from sharkit.commands.builtins import BUILTIN_COMMANDS
from sharkit.commands.registry import CommandRegistry


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
