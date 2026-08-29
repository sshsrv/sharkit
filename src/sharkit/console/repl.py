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
from sharkit.modules.registry import ModuleRegistry
from sharkit.output.renderer import Renderer

_PROMPT_STYLE = Style.from_dict({
    "prompt": "#ff69b4 bold",
    "module": "#ff69b4",
})


class _SharkitHistory(History):
    def __init__(self, manager: HistoryManager) -> None:
        self._manager = manager
        super().__init__()

    def load_history_strings(self) -> list[str]:
        return self._manager.get_history()

    def store_string(self, string: str) -> None:
        self._manager.add_command(string)


class _ConsoleCompleter(Completer):
    def __init__(
        self,
        engine: CompletionEngine,
        command_registry: CommandRegistry,
        module_registry: ModuleRegistry,
        get_current_module: Any,
    ) -> None:
        self._engine = engine
        self._command_registry = command_registry
        self._module_registry = module_registry
        self._get_current_module = get_current_module

    def get_completions(self, document: Any, complete_event: Any) -> Any:
        text = document.text_before_cursor
        completions = self._engine.get_completions(
            text,
            self._command_registry,
            self._module_registry,
            self._get_current_module(),
        )

        last_space = text.rfind(" ")
        start_position = -(len(text) - last_space - 1) if last_space >= 0 else -len(text)

        for completion_text in completions:
            yield Completion(completion_text, start_position=start_position)


class Console:
    def __init__(
        self,
        command_registry: CommandRegistry,
        module_registry: ModuleRegistry,
        config_manager: Any,
        history_manager: HistoryManager,
        renderer: Renderer,
    ) -> None:
        self._command_registry = command_registry
        self._module_registry = module_registry
        self._config_manager = config_manager
        self._history_manager = history_manager
        self._renderer = renderer
        self._current_module: str | None = None
        self._session_data: dict[str, Any] = {
            "command_registry": command_registry,
            "module_registry": module_registry,
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
        if self._current_module is not None:
            prompt = f"shark ({self._current_module}) > "
        else:
            prompt = "shark > "
        return self._prompt_renderer.render(prompt)

    def _init_session(self) -> None:
        self._prompt_renderer = PromptRenderer()
        self._completer = _ConsoleCompleter(
            engine=CompletionEngine(),
            command_registry=self._command_registry,
            module_registry=self._module_registry,
            get_current_module=lambda: self._current_module,
        )
        self._prompt_session = PromptSession[str](
            history=_SharkitHistory(self._history_manager),
            completer=self._completer,
            style=_PROMPT_STYLE,
            complete_while_typing=True,
        )

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
            current_module=self._current_module,
        )

        try:
            command_class = self._command_registry.get_command(command_name)
            command_instance = command_class()
            if "-h" in args or "--help" in args:
                self._renderer.panel(command_instance.name, command_instance.format_help())
                print()
                return True
            result = command_instance.execute(context, args)
            self._current_module = context.current_module
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
