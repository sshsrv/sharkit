from dataclasses import dataclass

from sharkit.modules.base import ExecutionContext, Module, ModuleMetadata, OptionDefinition, Result


@dataclass
class EchoMetadata:
    name: str = "echo"
    description: str = "Echo module for testing framework functionality"
    category: str = "testing/demo"
    author: str = "sharkit"
    version: str = "0.1.0"
    safety: str = "safe"


class EchoModule(Module):
    metadata: ModuleMetadata = ModuleMetadata(
        name="echo",
        description="Echo module for testing framework functionality",
        category="testing/demo",
        author="sharkit",
        version="0.1.0",
        safety="safe",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "message": OptionDefinition(
                name="message",
                description="Message to echo back",
                required=False,
                default="Hello from sharkit! :3",
                value=None,
            ),
            "repeat": OptionDefinition(
                name="repeat",
                description="Number of times to repeat the message",
                required=False,
                default="1",
                value=None,
            ),
        }

    def get_metadata(self) -> ModuleMetadata:
        return self.metadata

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def set_option(self, key: str, value: str) -> None:
        if key not in self._options:
            raise ValueError(f'Option "{key}" not found.')
        import dataclasses
        self._options[key] = dataclasses.replace(self._options[key], value=value)

    def execute(self, context: ExecutionContext) -> Result:
        message = self._options["message"].value or self._options["message"].default
        repeat_value = self._options["repeat"].value or self._options["repeat"].default
        if not repeat_value:
            return Result(
                success=False,
                data={},
                error="Repeat value is required.",
            )

        try:
            repeat = int(repeat_value)
        except ValueError:
            return Result(
                success=False,
                data={},
                error="Repeat value must be an integer.",
            )

        if repeat < 1:
            return Result(
                success=False,
                data={},
                error="Repeat value must be at least 1.",
            )

        messages = [message] * repeat

        return Result(
            success=True,
            data={
                "message": message,
                "repeat": repeat,
                "messages": messages,
            },
            error=None,
        )
