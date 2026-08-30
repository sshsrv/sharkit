from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sharkit import __version__
from sharkit.commands.base import Command, CommandContext
from sharkit.output.theme import BLUE, BOLD, GREEN, PINK, RED, RESET
from sharkit.tools.base import Tool

_TRUE_VALUES = ("yes", "true", "enabled", "1", "on")
_FALSE_VALUES = ("no", "false", "disabled", "0", "off")


def _normalize_bool(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in _TRUE_VALUES:
        return "true"
    if lowered in _FALSE_VALUES:
        return "false"
    return value


def _get_tool_instance(context: CommandContext) -> Tool | None:
    tool_name = context.current_tool
    if tool_name is None:
        return None
    tool_registry = context.session.get("tool_registry")
    if tool_registry is None:
        return None
    tool_cls = tool_registry.get_tool(tool_name)
    if tool_cls is None:
        return None
    instances: dict[str, Tool] = context.session.setdefault("tool_instances", {})
    if tool_name not in instances:
        instances[tool_name] = tool_cls()
    return instances[tool_name]


class HelpCommand(Command):
    name = "help"
    aliases = ["h", "?"]
    description = "Show available commands or help for a specific command"
    usage = "help [command]"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if args:
            return self._show_command_help(context, args[0])
        return self._show_all_commands(context)

    def _show_all_commands(self, context: CommandContext) -> str | None:
        registry = context.session.get("command_registry")
        if registry is None:
            return "No command registry available."
        renderer = context.session.get("renderer")
        if renderer is None:
            return "No command registry available."
        rows = []
        for cmd_class in registry.get_all_commands():
            aliases = ", ".join(cmd_class.aliases)
            rows.append([cmd_class.name, cmd_class.description, aliases])
        renderer.table("help", ["Command", "Description", "Aliases"], rows)
        return None

    def _show_command_help(self, context: CommandContext, name: str) -> str | None:
        registry = context.session.get("command_registry")
        renderer = context.session.get("renderer")
        if registry is None or renderer is None:
            return "No command registry available."
        try:
            cmd_class = registry.get_command(name)
        except Exception:
            return f'Command "{name}" not found.'
        if cmd_class is None:
            return f'Command "{name}" not found.'
        renderer.panel(cmd_class.name, cmd_class().format_help())
        return None


class BannerCommand(Command):
    name = "banner"
    aliases = ["logo"]
    description = "Show sharkit banner"
    usage = "banner"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        renderer = context.session.get("renderer")
        if renderer is None:
            return f"sharkit v{__version__}"
        tool_registry = context.session.get("tool_registry")
        tool_count = len(tool_registry.get_all_tools()) if tool_registry else 0
        renderer.banner(tool_count=tool_count)
        return None


class VersionCommand(Command):
    name = "version"
    aliases = ["ver"]
    description = "Show sharkit version"
    usage = "version"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        return f"sharkit v{__version__}"


class StatusCommand(Command):
    name = "status"
    aliases = []
    description = "Show framework status"
    usage = "status"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        tool_registry = context.session.get("tool_registry")
        tool_count = len(tool_registry.get_all_tools()) if tool_registry else 0
        current = context.current_tool or "none"
        lines = [
            f"tools     {tool_count}",
            f"current     {current}",
            "status      ready",
        ]
        return "\n".join(lines)


class UseCommand(Command):
    name = "use"
    aliases = []
    description = "Select a tool by name, search query, or index (msfconsole-style)"
    usage = "use <query|index>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        token = args[0]
        tool_registry = context.session.get("tool_registry")
        if tool_registry is None:
            return "Tool registry not available."

        if token.isdigit():
            matches = context.session.get("use_matches")
            if not matches:
                self._log(context, 'No tool selection in progress. Use "use <query>" first.')
                return None
            index = int(token)
            if index < 0 or index >= len(matches):
                self._log(context, f"Invalid tool index: {index}")
                return None
            return self._select_tool(context, matches[index])

        query = token.lower()
        matches = tool_registry.find_tools(query)
        if not matches:
            self._log(context, f'No tools found matching "{token}". Try: search {token}')
            return None

        paths = [path for path, _ in matches]
        context.session["use_matches"] = paths

        renderer = context.session.get("renderer")
        if renderer is not None:
            rows = [
                [str(i), path, metadata.description]
                for i, (path, metadata) in enumerate(matches)
            ]
            renderer.table(f"use > {token}", ["#", "Tool", "Description"], rows)

        if len(matches) == 1:
            return self._select_tool(context, paths[0])
        self._log(context, 'Select a tool by index, e.g. "use 0".')
        return None

    def _log(self, context: CommandContext, message: str) -> None:
        renderer = context.session.get("renderer")
        if renderer is not None:
            renderer.log_line("use", message)

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None

    def _select_tool(self, context: CommandContext, path: str) -> str | None:
        tool_registry = context.session.get("tool_registry")
        tool_manager = context.session.get("tool_manager")
        tool_cls = tool_registry.get_tool(path) if tool_registry else None
        if tool_cls is not None and tool_cls.metadata.install is not None:
            spec = tool_cls.metadata.install
            name = tool_cls.metadata.name
            display = tool_registry.format_display(path) if tool_registry else name
            if tool_manager is not None and not tool_manager.is_installed(name):
                if not self._prompt_install(name):
                    self._log(context, f'Tool "{name}" is not installed. Run: install {name}')
                    return None
                renderer = context.session.get("renderer")

                def on_progress(msg: str) -> None:
                    if renderer is not None:
                        renderer.log_line(f"install {display}", msg, color=GREEN)

                ok, message = tool_manager.install(name, spec, on_progress=on_progress)
                if not ok:
                    self._log(context, message)
                    return None
        context.current_tool = path
        self._log(context, f'Tool "{path}" selected.')
        if tool_cls is not None and tool_cls.metadata.install is not None:
            renderer = context.session.get("renderer")
            if renderer is not None:
                install_spec = tool_cls.metadata.install
                renderer.support_creator(
                    tool_cls.metadata.author,
                    tool_cls.metadata.name,
                    install_spec.git_url,
                )
        return None

    def _prompt_install(self, name: str) -> bool:
        if not sys.stdin.isatty():
            return False
        try:
            answer = input(f'Install tool "{name}" now? [Y/n] ').strip().lower()
        except Exception:
            return False
        return answer in ("", "y", "yes")


class BackCommand(Command):
    name = "back"
    aliases = []
    description = "Deselect current tool"
    usage = "back"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if context.current_tool is None:
            return "No tool is currently selected."
        previous = context.current_tool
        context.current_tool = None
        return f'Deselected tool "{previous}".'


class InfoCommand(Command):
    name = "info"
    aliases = []
    description = "Show info about current tool"
    usage = "info"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if context.current_tool is None:
            return "No tool selected. Use 'use <tool>' first."
        tool_registry = context.session.get("tool_registry")
        if tool_registry is None:
            return f"Tool: {context.current_tool}"
        try:
            tool_cls = tool_registry.get_tool(context.current_tool)
            metadata = tool_cls.metadata
            lines = [
                f"description   {metadata.description}",
                f"category      {metadata.category}",
                f"author        {metadata.author}",
                f"version       {metadata.version}",
                f"safety        {metadata.safety}",
            ]
            return "\n".join(lines)
        except Exception:
            return f"Tool: {context.current_tool}"


class ShowCommand(Command):
    name = "show"
    aliases = []
    description = "Show tools or tool options"
    usage = "show <tools|options> [tool]"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if not args:
            if context.current_tool is not None:
                return self._show_options(context, None)
            return self._show_tools(context)
        if args[0] == "options":
            return self._show_options(context, args[1] if len(args) > 1 else None)
        if args[0] == "tools":
            return self._show_tools(context)
        return f"Unknown show subcommand: {args[0]}\nUsage: {self.usage}"

    def _show_tools(self, context: CommandContext) -> str | None:
        tool_registry = context.session.get("tool_registry")
        tool_manager = context.session.get("tool_manager")
        renderer = context.session.get("renderer")
        if tool_registry is None or renderer is None:
            return "Tool registry not available."
        all_tools = tool_registry.get_all_tools()
        if not all_tools:
            return "No tools available."
        rows = []
        for tool_path, tool_cls in all_tools.items():
            metadata = tool_cls.metadata
            if metadata.install is None or (
                tool_manager is not None and tool_manager.is_installed(metadata.name)
            ):
                installed = f"{BOLD}{PINK}Yes{RESET}"
            else:
                installed = ""
            rows.append([tool_path, installed, metadata.description])
        renderer.table("show > tools", ["Tool", "Installed", "Description"], rows)
        return None

    def _show_options(self, context: CommandContext, tool_arg: str | None) -> str | None:
        tool_registry = context.session.get("tool_registry")
        renderer = context.session.get("renderer")
        if tool_registry is None or renderer is None:
            return "Tool registry not available."
        if tool_arg is not None:
            tool_cls = tool_registry.get_tool(tool_arg)
            if tool_cls is None:
                return f'Tool "{tool_arg}" not found.\nTry: show tools'
            instance = tool_cls()
            title_tool = tool_cls.metadata.name
        else:
            if context.current_tool is None:
                return "No tool selected. Use 'show tools' or 'use <tool>' first."
            tool_cls = tool_registry.get_tool(context.current_tool)
            if tool_cls is None:
                return "Current tool not found."
            instance = _get_tool_instance(context)
            if instance is None:
                return "Tool registry not available."
            title_tool = tool_cls.metadata.name
        try:
            options = instance.get_options()
            if not options:
                return "This tool has no options."
            rows = []
            for opt in options.values():
                value = opt.value or opt.default or "not set"
                required = " (required)" if opt.required else ""
                rows.append([opt.name, value, f"{opt.description}{required}"])
            renderer.table(
                f"show > options > {title_tool}",
                ["Name", "Value", "Description"],
                rows,
            )
            return None
        except Exception:
            return "Could not retrieve options for tool."


class SetCommand(Command):
    name = "set"
    aliases = []
    description = "Set option value for current tool"
    usage = "set <option> <value>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        if context.current_tool is None:
            return "No tool selected. Use 'use <tool>' first."
        tool_instance = _get_tool_instance(context)
        if tool_instance is None:
            return "Tool registry not available."
        try:
            options = tool_instance.get_options()
            key = args[0]
            if key not in options:
                available = ", ".join(options.keys())
                return f'Option "{key}" not found.\nAvailable options: {available}'
            option = options[key]
            raw = " ".join(args[1:])
            if option.type == "bool":
                value = _normalize_bool(raw)
            elif option.choices:
                if raw not in option.choices:
                    return (
                        f'Invalid value for "{key}": {raw}\n'
                        f'Allowed: {", ".join(option.choices)}'
                    )
                value = raw
            else:
                value = raw
            tool_instance.set_option(key, value)
            renderer = context.session.get("renderer")
            if renderer is not None:
                renderer.log_line(f"set ({context.current_tool})", f"{key} = {value}")
                return None
            return f"Set {key} = {value}"
        except Exception as e:
            return f"Failed to set option: {e}"

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None


class UnsetCommand(Command):
    name = "unset"
    aliases = []
    description = "Unset option value"
    usage = "unset <option>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        if context.current_tool is None:
            return "No tool selected. Use 'use <tool>' first."
        tool_instance = _get_tool_instance(context)
        if tool_instance is None:
            return "Tool registry not available."
        try:
            options = tool_instance.get_options()
            key = args[0]
            if key not in options:
                available = ", ".join(options.keys())
                return f'Option "{key}" not found.\nAvailable options: {available}'
            tool_instance.set_option(key, options[key].default or "")
            return f"Unset {key}."
        except Exception as e:
            return f"Failed to unset option: {e}"

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None


class RunCommand(Command):
    name = "run"
    aliases = ["sharkit"]
    description = "Execute current tool"
    usage = "run"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if context.current_tool is None:
            return "No tool selected. Use 'use <tool>' first."
        tool_instance = _get_tool_instance(context)
        if tool_instance is None:
            return "Tool registry not available."
        try:
            options = tool_instance.get_options()
            option_values = {k: v.value or v.default or "" for k, v in options.items()}
            config_dir = context.session.get("config_dir") or Path("/tmp")
            from sharkit.tools.base import ExecutionContext

            exec_context = ExecutionContext(
                tool_name=context.current_tool,
                options=option_values,
                config_dir=config_dir,
                renderer=context.session.get("renderer"),
            )
            try:
                result = tool_instance.execute(exec_context)
            except KeyboardInterrupt:
                renderer = context.session.get("renderer")
                if renderer is not None:
                    renderer.info("Run aborted (Ctrl+C).")
                else:
                    print("Run aborted (Ctrl+C).")
                return None
            renderer = context.session.get("renderer")
            if result.success:
                if result.data:
                    if renderer is not None:
                        renderer.result(result.data)
                        return None
                    lines = [f"{key}: {value}" for key, value in result.data.items()]
                    return "\n".join(lines) if lines else "Tool executed successfully."
                if renderer is not None:
                    return None
                return "Tool executed successfully."
            if renderer is not None:
                renderer.error(f"Tool execution failed: {result.error}")
                return None
            return f"Tool execution failed: {result.error}"
        except Exception as e:
            return f"Tool execution error: {e}"


class SearchCommand(Command):
    name = "search"
    aliases = ["find"]
    description = "Search tools by query"
    usage = "search <query>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        query = args[0].lower()
        tool_registry = context.session.get("tool_registry")
        if tool_registry is None:
            return "Tool registry not available."
        try:
            all_tools = tool_registry.get_all_tools()
            matches = []
            for tool_path, tool_cls in all_tools.items():
                metadata = tool_cls.metadata
                searchable = f"{metadata.name} {metadata.description} {metadata.category}".lower()
                if query in searchable or query in tool_path.lower():
                    matches.append(f"  {tool_path:<30}{metadata.description}")
            if not matches:
                return f'No tools found matching "{query}".'
            lines = [f"Tools matching \"{query}\":"] + matches
            return "\n".join(lines)
        except Exception as e:
            return f"Search failed: {e}"

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None


class HistoryCommand(Command):
    name = "history"
    aliases = []
    description = "Show command history"
    usage = "history [options]"
    options = [
        ("-a, --all-commands", "Show all commands in history."),
        ("-c, --clear", "Clear command history and history file."),
        ("-h, --help", "Help banner."),
        ("-n <num>", "Show the last n commands."),
    ]
    notes = (
        "By default only the last 100 entries are shown. Use -a to dump them all.\n"
        "-c wipes both the live history and the history file on disk. mrrp :3\n"
        "Lead a command with a space and it stays out of the history."
    )

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        clear = False
        all_commands = False
        limit = 100
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-c", "--clear"):
                clear = True
            elif arg in ("-a", "--all-commands"):
                all_commands = True
            elif arg in ("-n", "--last"):
                i += 1
                if i >= len(args):
                    return f"Error: {arg} requires a number."
                try:
                    limit = int(args[i])
                except ValueError:
                    return f"Error: invalid number for {arg}: {args[i]}"
            elif arg in ("-h", "--help"):
                return self.format_help()
            else:
                return f"Unknown option: {arg}\nUsage: {self.usage}"
            i += 1

        manager = context.session.get("history_manager")
        if manager is None:
            return "History manager not available."

        if clear:
            manager.clear()
            context.session["history"] = []
            sharkit_history = context.session.get("sharkit_history")
            if sharkit_history is not None:
                sharkit_history.clear()
            return "[+] Command history and history file cleared"

        all_entries = manager.get_history(10_000_000)
        if all_commands:
            limit = len(all_entries)
        if limit < 0:
            limit = 0
        shown = all_entries[-limit:] if limit else all_entries
        if not shown:
            return "No command history."
        start = len(all_entries) - len(shown) + 1
        rows = [[str(start + idx), cmd] for idx, cmd in enumerate(shown)]
        renderer = context.session.get("renderer")
        if renderer is None:
            return "Renderer not available."
        renderer.table("history", ["#", "Command"], rows)
        return None


class ClearCommand(Command):
    name = "clear"
    aliases = ["cls"]
    description = "Clear terminal"
    usage = "clear"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        renderer = context.session.get("renderer")
        if renderer is not None:
            renderer.raw("\033[2J\033[3J\033[H")
            return None
        return "\033[2J\033[3J\033[H"


class ExitCommand(Command):
    name = "exit"
    aliases = ["quit"]
    description = "Exit application"
    usage = "exit"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        context.session["exit_requested"] = True
        return "Bye! :3"


class InstallCommand(Command):
    name = "install"
    aliases = []
    description = "Install an external tool"
    usage = "install <tool_name>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        name = args[0]
        tool_registry = context.session.get("tool_registry")
        tool_manager = context.session.get("tool_manager")
        if tool_registry is None or tool_manager is None:
            return "Tool registry or manager not available."
        tool_cls = tool_registry.get_tool(name)
        if tool_cls is None or tool_cls.metadata.install is None:
            return f'Tool "{name}" is not an external tool or was not found.'
        display = tool_registry.format_display(tool_registry.get_tool_path(name))
        if tool_manager.is_installed(name):
            renderer = context.session.get("renderer")
            if renderer is not None:
                renderer.log_line(f"install {display}", "already installed", color=GREEN)
            return None
        renderer = context.session.get("renderer")

        def on_progress(msg: str) -> None:
            if renderer is not None:
                renderer.log_line(f"install {display}", msg, color=GREEN)

        ok, message = tool_manager.install(name, tool_cls.metadata.install, on_progress=on_progress)
        if renderer is not None:
            if ok:
                renderer.log_line(f"install {display}", "installed", color=GREEN)
            else:
                renderer.log_line(f"install {display}", f"failed: {message}", color=GREEN)
            return None
        return str(message)

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None


class UpgradeCommand(Command):
    name = "upgrade"
    aliases = ["update"]
    description = "Upgrade an installed external tool (or all with no name)"
    usage = "upgrade <tool_name>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        tool_registry = context.session.get("tool_registry")
        tool_manager = context.session.get("tool_manager")
        if tool_registry is None or tool_manager is None:
            return "Tool registry or manager not available."
        if not args:
            return self._upgrade_all(context, tool_manager, tool_registry)
        name = args[0]
        tool_cls = tool_registry.get_tool(name)
        if tool_cls is None or tool_cls.metadata.install is None:
            return f'Tool "{name}" is not an external tool or was not found.'
        display = tool_registry.format_display(tool_registry.get_tool_path(name))
        if not tool_manager.is_installed(name):
            renderer = context.session.get("renderer")
            if renderer is not None:
                renderer.log_line(f"upgrade {display}", "not installed (skipped)", color=BLUE)
            return None
        renderer = context.session.get("renderer")

        def on_progress(msg: str) -> None:
            if renderer is not None:
                renderer.log_line(f"upgrade {display}", msg, color=BLUE)

        ok, message = tool_manager.update(name, tool_cls.metadata.install, on_progress=on_progress)
        if renderer is not None:
            if ok:
                renderer.log_line(f"upgrade {display}", "upgraded", color=BLUE)
            else:
                renderer.log_line(f"upgrade {display}", f"failed: {message}", color=BLUE)
            return None
        return str(message)

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if len(args) > 1:
            return False, f"Usage: {self.usage}"
        return True, None

    def _upgrade_all(
        self,
        context: CommandContext,
        tool_manager: Any,
        tool_registry: Any,
    ) -> str | None:
        metas = [m for m in tool_registry.list_tools() if m.install is not None]
        if not metas:
            renderer = context.session.get("renderer")
            if renderer is not None:
                renderer.log_line("upgrade", "no external tools to update", color=BLUE)
            return None
        for meta in metas:
            spec = meta.install
            if spec is None:
                continue
            name = meta.name
            display = tool_registry.format_display(tool_registry.get_tool_path(name))
            if not tool_manager.is_installed(name):
                renderer = context.session.get("renderer")
                if renderer is not None:
                    renderer.log_line(f"upgrade {display}", "not installed (skipped)", color=BLUE)
                continue
            renderer = context.session.get("renderer")

            def on_progress(msg: str, display: str = display, renderer: Any = renderer) -> None:
                if renderer is not None:
                    renderer.log_line(f"upgrade {display}", msg, color=BLUE)

            ok, message = tool_manager.update(name, spec, on_progress=on_progress)
            if renderer is not None:
                if ok:
                    renderer.log_line(f"upgrade {display}", "upgraded", color=BLUE)
                else:
                    renderer.log_line(f"upgrade {display}", f"failed: {message}", color=BLUE)
        return None


class RemoveCommand(Command):
    name = "remove"
    aliases = ["uninstall"]
    description = "Remove an installed external tool"
    usage = "remove <tool_name>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        name = args[0]
        tool_registry = context.session.get("tool_registry")
        tool_manager = context.session.get("tool_manager")
        if tool_registry is None or tool_manager is None:
            return "Tool registry or manager not available."
        tool_cls = tool_registry.get_tool(name)
        if tool_cls is None or tool_cls.metadata.install is None:
            return f'Tool "{name}" is not an external tool or was not found.'
        display = tool_registry.format_display(tool_registry.get_tool_path(name))
        renderer = context.session.get("renderer")
        ok, message = tool_manager.uninstall(name)
        if renderer is not None:
            if ok:
                renderer.log_line(f"remove {display}", "removed", color=RED)
            else:
                renderer.log_line(f"remove {display}", f"failed: {message}", color=RED)
            return None
        return str(message)

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None


BUILTIN_COMMANDS: list[type[Command]] = [
    HelpCommand,
    BannerCommand,
    VersionCommand,
    StatusCommand,
    UseCommand,
    InstallCommand,
    UpgradeCommand,
    RemoveCommand,
    BackCommand,
    InfoCommand,
    ShowCommand,
    SetCommand,
    UnsetCommand,
    RunCommand,
    SearchCommand,
    HistoryCommand,
    ClearCommand,
    ExitCommand,
]
