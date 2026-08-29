class SharkitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(SharkitError):
    pass


class ModuleError(SharkitError):
    pass


class ModuleNotFoundError(ModuleError):
    def __init__(self, name: str) -> None:
        super().__init__(f'Module "{name}" was not found.')
        self.module_name = name


class ModuleExecutionError(ModuleError):
    def __init__(self, module_name: str, reason: str) -> None:
        super().__init__(f'Module "{module_name}" execution failed: {reason}')
        self.module_name = module_name
        self.reason = reason


class ModuleLoadError(ModuleError):
    def __init__(self, module_path: str, reason: str) -> None:
        super().__init__(f'Failed to load module from "{module_path}": {reason}')
        self.module_path = module_path
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
