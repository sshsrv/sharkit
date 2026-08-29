from __future__ import annotations

from pathlib import Path

from sharkit import __version__
from sharkit.commands.base import Command, CommandContext
from sharkit.modules.base import Module


def _get_module_instance(context: CommandContext) -> Module | None:
    module_name = context.current_module
    if module_name is None:
        return None
    module_registry = context.session.get("module_registry")
    if module_registry is None:
        return None
    module_cls = module_registry.get_module(module_name)
    if module_cls is None:
        return None
    instances: dict[str, Module] = context.session.setdefault("module_instances", {})
    if module_name not in instances:
        instances[module_name] = module_cls()
    return instances[module_name]


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
        module_registry = context.session.get("module_registry")
        module_count = len(module_registry.get_all_modules()) if module_registry else 0
        renderer.banner(module_count=module_count)
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
        module_registry = context.session.get("module_registry")
        module_count = len(module_registry.get_all_modules()) if module_registry else 0
        current = context.current_module or "none"
        lines = [
            f"modules     {module_count}",
            f"current     {current}",
            "status      ready",
        ]
        return "\n".join(lines)


class UseCommand(Command):
    name = "use"
    aliases = []
    description = "Select a module by name, search query, or index (msfconsole-style)"
    usage = "use <query|index>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        token = args[0]
        module_registry = context.session.get("module_registry")
        if module_registry is None:
            return "Module registry not available."

        if token.isdigit():
            matches = context.session.get("use_matches")
            if not matches:
                return 'No module selection in progress. Use "use <query>" to search first.'
            index = int(token)
            if index < 0 or index >= len(matches):
                return f"Invalid module index: {index}"
            context.current_module = matches[index]
            return f'Module "{matches[index]}" selected.'

        query = token.lower()
        matches = module_registry.find_modules(query)
        if not matches:
            return f'No modules found matching "{token}".\nTry: search {token}'

        paths = [path for path, _ in matches]
        context.session["use_matches"] = paths

        renderer = context.session.get("renderer")
        if renderer is not None:
            rows = [
                [str(i), path, metadata.description]
                for i, (path, metadata) in enumerate(matches)
            ]
            renderer.table(f"use > {token}", ["#", "Module", "Description"], rows)

        if len(matches) == 1:
            context.current_module = paths[0]
            return f'Module "{paths[0]}" selected.'
        return 'Select a module by index, e.g. "use 0".'

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if not args:
            return False, f"Usage: {self.usage}"
        return True, None


class BackCommand(Command):
    name = "back"
    aliases = []
    description = "Deselect current module"
    usage = "back"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if context.current_module is None:
            return "No module is currently selected."
        previous = context.current_module
        context.current_module = None
        return f'Deselected module "{previous}".'


class InfoCommand(Command):
    name = "info"
    aliases = []
    description = "Show info about current module"
    usage = "info"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if context.current_module is None:
            return "No module selected. Use 'use <module>' first."
        module_registry = context.session.get("module_registry")
        if module_registry is None:
            return f"Module: {context.current_module}"
        try:
            module_cls = module_registry.get_module(context.current_module)
            metadata = module_cls.metadata
            lines = [
                f"description   {metadata.description}",
                f"category      {metadata.category}",
                f"author        {metadata.author}",
                f"version       {metadata.version}",
                f"safety        {metadata.safety}",
            ]
            return "\n".join(lines)
        except Exception:
            return f"Module: {context.current_module}"


class ShowCommand(Command):
    name = "show"
    aliases = []
    description = "Show tools or module options"
    usage = "show <tools|options> [module]"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if not args:
            if context.current_module is not None:
                return self._show_options(context, None)
            return self._show_tools(context)
        if args[0] == "options":
            return self._show_options(context, args[1] if len(args) > 1 else None)
        if args[0] == "tools":
            return self._show_tools(context)
        return f"Unknown show subcommand: {args[0]}\nUsage: {self.usage}"

    def _show_tools(self, context: CommandContext) -> str | None:
        module_registry = context.session.get("module_registry")
        renderer = context.session.get("renderer")
        if module_registry is None or renderer is None:
            return "Module registry not available."
        all_modules = module_registry.get_all_modules()
        if not all_modules:
            return "No modules available."
        rows = [
            [module_path, module_cls.metadata.description]
            for module_path, module_cls in all_modules.items()
        ]
        renderer.table("show > tools", ["Module", "Description"], rows)
        return None

    def _show_options(self, context: CommandContext, module_arg: str | None) -> str | None:
        module_registry = context.session.get("module_registry")
        renderer = context.session.get("renderer")
        if module_registry is None or renderer is None:
            return "Module registry not available."
        if module_arg is not None:
            module_cls = module_registry.get_module(module_arg)
            if module_cls is None:
                return f'Module "{module_arg}" not found.\nTry: show tools'
            instance = module_cls()
            title_module = module_cls.metadata.name
        else:
            if context.current_module is None:
                return "No module selected. Use 'show tools' or 'use <module>' first."
            module_cls = module_registry.get_module(context.current_module)
            if module_cls is None:
                return "Current module not found."
            instance = _get_module_instance(context)
            if instance is None:
                return "Module registry not available."
            title_module = module_cls.metadata.name
        try:
            options = instance.get_options()
            if not options:
                return "This module has no options."
            rows = []
            for opt in options.values():
                value = opt.value or opt.default or "not set"
                required = " (required)" if opt.required else ""
                rows.append([opt.name, value, f"{opt.description}{required}"])
            renderer.table(
                f"show > options > {title_module}",
                ["Name", "Value", "Description"],
                rows,
            )
            return None
        except Exception:
            return "Could not retrieve options for module."


class SetCommand(Command):
    name = "set"
    aliases = []
    description = "Set option value for current module"
    usage = "set <option> <value>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        if context.current_module is None:
            return "No module selected. Use 'use <module>' first."
        module_instance = _get_module_instance(context)
        if module_instance is None:
            return "Module registry not available."
        try:
            options = module_instance.get_options()
            key = args[0]
            if key not in options:
                available = ", ".join(options.keys())
                return f'Option "{key}" not found.\nAvailable options: {available}'
            module_instance.set_option(key, " ".join(args[1:]))
            return f"Set {key} = {' '.join(args[1:])}"
        except Exception as e:
            return f"Failed to set option: {e}"

    def validate_args(self, args: list[str]) -> tuple[bool, str | None]:
        if len(args) < 2:
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
        if context.current_module is None:
            return "No module selected. Use 'use <module>' first."
        module_instance = _get_module_instance(context)
        if module_instance is None:
            return "Module registry not available."
        try:
            options = module_instance.get_options()
            key = args[0]
            if key not in options:
                available = ", ".join(options.keys())
                return f'Option "{key}" not found.\nAvailable options: {available}'
            module_instance.set_option(key, options[key].default or "")
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
    description = "Execute current module"
    usage = "run"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        if context.current_module is None:
            return "No module selected. Use 'use <module>' first."
        module_instance = _get_module_instance(context)
        if module_instance is None:
            return "Module registry not available."
        try:
            options = module_instance.get_options()
            option_values = {k: v.value or v.default or "" for k, v in options.items()}
            config_dir = context.session.get("config_dir") or Path("/tmp")
            from sharkit.modules.base import ExecutionContext

            exec_context = ExecutionContext(
                module_name=context.current_module,
                options=option_values,
                config_dir=config_dir,
            )
            result = module_instance.execute(exec_context)
            renderer = context.session.get("renderer")
            if result.success:
                if renderer is not None:
                    renderer.result(result.data)
                    return None
                lines = [f"{key}: {value}" for key, value in result.data.items()]
                return "\n".join(lines) if lines else "Module executed successfully."
            if renderer is not None:
                renderer.error(f"Module execution failed: {result.error}")
                return None
            return f"Module execution failed: {result.error}"
        except Exception as e:
            return f"Module execution error: {e}"


class SearchCommand(Command):
    name = "search"
    aliases = ["find"]
    description = "Search modules by query"
    usage = "search <query>"

    def execute(self, context: CommandContext, args: list[str]) -> str | None:
        valid, error = self.validate_args(args)
        if not valid:
            return error
        query = args[0].lower()
        module_registry = context.session.get("module_registry")
        if module_registry is None:
            return "Module registry not available."
        try:
            all_modules = module_registry.get_all_modules()
            matches = []
            for module_path, module_cls in all_modules.items():
                metadata = module_cls.metadata
                searchable = f"{metadata.name} {metadata.description} {metadata.category}".lower()
                if query in searchable or query in module_path.lower():
                    matches.append(f"  {module_path:<30}{metadata.description}")
            if not matches:
                return f'No modules found matching "{query}".'
            lines = [f"Modules matching \"{query}\":"] + matches
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


BUILTIN_COMMANDS: list[type[Command]] = [
    HelpCommand,
    BannerCommand,
    VersionCommand,
    StatusCommand,
    UseCommand,
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
