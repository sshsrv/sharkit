from __future__ import annotations


class SharkitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(SharkitError):
    pass


class ToolError(SharkitError):
    pass


class ToolNotFoundError(ToolError):
    def __init__(self, name: str) -> None:
        super().__init__(f'Tool "{name}" was not found.')
        self.tool_name = name


class ToolExecutionError(ToolError):
    def __init__(self, tool_name: str, reason: str) -> None:
        super().__init__(f'Tool "{tool_name}" execution failed: {reason}')
        self.tool_name = tool_name
        self.reason = reason


class ToolLoadError(ToolError):
    def __init__(self, tool_path: str, reason: str) -> None:
        super().__init__(f'Failed to load tool from "{tool_path}": {reason}')
        self.tool_path = tool_path
        self.reason = reason


class CommandError(SharkitError):
    pass


class CommandNotFoundError(CommandError):
    def __init__(self, name: str) -> None:
        super().__init__(f'Command "{name}" was not found.')
        self.command_name = name


class NetworkError(SharkitError):
    pass


class ProviderError(SharkitError):
    pass


class PlatformError(SharkitError):
    pass
