from __future__ import annotations

import sys
from pathlib import Path

from sharkit.commands.builtins import BUILTIN_COMMANDS
from sharkit.commands.registry import CommandRegistry
from sharkit.config.manager import ConfigManager
from sharkit.console.repl import Console
from sharkit.exceptions import SharkitError
from sharkit.history.manager import HistoryManager
from sharkit.network.client import HttpClient
from sharkit.output.renderer import Renderer
from sharkit.tools.loader import discover_tools
from sharkit.tools.manager import ToolManager
from sharkit.tools.registry import ToolRegistry

NON_LINUX_MESSAGE = (
    "sharkit is a shark.\n"
    "it was built for open water,\n"
    "where it can actually swim.\n"
    "\n"
    "windows is more of a glass aquarium.\n"
    "tidy, bright, and a little too enclosed.\n"
    "\n"
    "the shark doesn't dislike the aquarium.\n"
    "it just wasn't shaped for it,\n"
    "and it shows.\n"
    "\n"
    "find us in linux.\n"
    "mrrp :3"
)


def main() -> int:
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()
    renderer = Renderer()

    if sys.platform == "win32":
        renderer.banner(tool_count=0, message=NON_LINUX_MESSAGE)
        return 1

    config_manager = ConfigManager()

    history_manager = HistoryManager()

    tool_registry = ToolRegistry()
    tool_manager = ToolManager()
    tools_dir = Path(__file__).parent / "tools"
    discovered = discover_tools(tools_dir)
    for tool_class, tool_path in discovered:
        tool_registry.register_tool(tool_class, tool_path)

    command_registry = CommandRegistry()
    for command_class in BUILTIN_COMMANDS:
        command_registry.register_command(command_class)

    http_client = HttpClient()

    renderer.banner(tool_count=len(discovered))
    print()

    console = Console(
        command_registry=command_registry,
        tool_registry=tool_registry,
        tool_manager=tool_manager,
        config_manager=config_manager,
        history_manager=history_manager,
        renderer=renderer,
    )

    try:
        console.run()
    except KeyboardInterrupt:
        print()
    except SharkitError as exc:
        renderer.error(str(exc))
        return 1
    finally:
        http_client.close()

    return 0
