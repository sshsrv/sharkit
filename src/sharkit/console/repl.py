from __future__ import annotations

import shlex
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import History
from prompt_toolkit.styles import Style

from sharkit.commands.base import CommandContext
from sharkit.commands.registry import CommandRegistry
from sharkit.config.paths import get_config_dir
from sharkit.console.completion import CompletionEngine
from sharkit.console.prompt import PromptRenderer
from sharkit.exceptions import CommandNotFoundError, SharkitError
from sharkit.history.manager import HistoryManager
from sharkit.output.renderer import Renderer
from sharkit.tools.manager import ToolManager
from sharkit.tools.registry import ToolRegistry

_PROMPT_STYLE = Style.from_dict({
    "prompt": "#ff69b4 bold",
    "tool": "#ff69b4",
})


class _SharkitHistory(History):
    def __init__(self, manager: HistoryManager) -> None:
        self._manager = manager
        super().__init__()

    def load_history_strings(self) -> list[str]:
        return self._manager.get_history()

    def store_string(self, string: str) -> None:
        self._manager.add_command(string)

    def clear(self) -> None:
        """Reset the in-memory buffer so next load() re-reads from file."""
        self._loaded = False
        self._loaded_strings = []


class _ConsoleCompleter(Completer):
    def __init__(
        self,
        engine: CompletionEngine,
        command_registry: CommandRegistry,
        tool_registry: ToolRegistry,
        get_current_tool: Any,
    ) -> None:
        self._engine = engine
        self._command_registry = command_registry
        self._tool_registry = tool_registry
        self._get_current_tool = get_current_tool

    def get_completions(self, document: Any, complete_event: Any) -> Any:
        text = document.text_before_cursor
        completions = self._engine.get_completions(
            text,
            self._command_registry,
            self._tool_registry,
            self._get_current_tool(),
        )

        last_space = text.rfind(" ")
        start_position = -(len(text) - last_space - 1) if last_space >= 0 else -len(text)

        for completion_text in completions:
            yield Completion(completion_text, start_position=start_position)


class Console:
    def __init__(
        self,
        command_registry: CommandRegistry,
        tool_registry: ToolRegistry,
        tool_manager: ToolManager,
        config_manager: Any,
        history_manager: HistoryManager,
        renderer: Renderer,
    ) -> None:
        self._command_registry = command_registry
        self._tool_registry = tool_registry
        self._tool_manager = tool_manager
        self._config_manager = config_manager
        self._history_manager = history_manager
        self._renderer = renderer
        self._current_tool: str | None = None
        self._session_data: dict[str, Any] = {
            "command_registry": command_registry,
            "tool_registry": tool_registry,
            "tool_manager": tool_manager,
            "config_manager": config_manager,
            "http_client": None,
            "config_dir": get_config_dir(),
            "renderer": renderer,
            "history_manager": history_manager,
            "history": history_manager.get_history(),
        }
        self._prompt_renderer: Any = None
        self._completer: _ConsoleCompleter | None = None
        self._prompt_session: PromptSession[str] | None = None

    def _get_prompt(self) -> Any:
        if self._current_tool is not None:
            prompt = self._prompt_renderer.tool_prompt(self._current_tool)
        else:
            prompt = self._prompt_renderer.default_prompt()
        return self._prompt_renderer.render(prompt)

    def _init_session(self) -> None:
        self._prompt_renderer = PromptRenderer()
        self._completer = _ConsoleCompleter(
            engine=CompletionEngine(),
            command_registry=self._command_registry,
            tool_registry=self._tool_registry,
            get_current_tool=lambda: self._current_tool,
        )
        self._sharkit_history = _SharkitHistory(self._history_manager)
        self._prompt_session = PromptSession[str](
            history=self._sharkit_history,
            completer=self._completer,
            style=_PROMPT_STYLE,
            complete_while_typing=True,
        )
        self._session_data["sharkit_history"] = self._sharkit_history

    def run(self) -> None:
        self._init_session()

        assert self._prompt_session is not None

        while True:
            try:
                line = self._prompt_session.prompt(self._get_prompt)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

            stripped = line.strip()
            if not stripped:
                continue

            if not line[:1].isspace():
                self._history_manager.add_command(stripped)
            self._session_data["history"] = self._history_manager.get_history()

            if not self.process_command(stripped):
                break

    def process_command(self, line: str) -> bool:
        try:
            parts = shlex.split(line)
        except ValueError:
            self._renderer.error(f'Invalid command syntax: "{line}"')
            print()
            return True

        if not parts:
            return True

        command_name = parts[0]
        args = parts[1:]

        context = CommandContext(
            session=self._session_data,
            current_tool=self._current_tool,
        )

        try:
            command_class = self._command_registry.get_command(command_name)
            command_instance = command_class()
            if "-h" in args or "--help" in args:
                self._renderer.panel(command_instance.name, command_instance.format_help())
                print()
                return True
            result = command_instance.execute(context, args)
            self._current_tool = context.current_tool
            if result is not None:
                self._renderer.panel(command_instance.name, result)
        except CommandNotFoundError as exc:
            self._renderer.error(str(exc))
        except SharkitError as exc:
            self._renderer.error(str(exc))
        except Exception as exc:
            self._renderer.error(f"Unexpected error: {exc}")

        print()
        return not self._session_data.pop("exit_requested", None)
