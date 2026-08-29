from dataclasses import dataclass

from sharkit.modules.base import ExecutionContext, Module, ModuleMetadata, OptionDefinition, Result


@dataclass
class HttpMetadataMetadata:
    name: str = "metadata"
    description: str = "HTTP metadata module for testing network abstraction"
    category: str = "testing/http"
    author: str = "sharkit"
    version: str = "0.1.0"
    safety: str = "safe"


class HttpMetadataModule(Module):
    metadata: ModuleMetadata = ModuleMetadata(
        name="metadata",
        description="HTTP metadata module for testing network abstraction",
        category="testing/http",
        author="sharkit",
        version="0.1.0",
        safety="safe",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "url": OptionDefinition(
                name="url",
                description="URL to fetch metadata from",
                required=True,
                default=None,
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
        url = self._options["url"].value
        if not url:
            return Result(
                success=False,
                data={},
                error="URL is required. Use: set url <url>",
            )

        from sharkit.network.client import HttpClient

        client = HttpClient()
        try:
            response = client.get(url, timeout=10.0)
            return Result(
                success=True,
                data={
                    "url": response.url,
                    "status_code": response.status_code,
                    "protocol": response.protocol,
                    "headers": response.headers,
                    "content_type": response.headers.get("content-type", "unknown"),
                    "content_length": len(response.content),
                    "duration": response.duration,
                },
                error=None,
            )
        except Exception as e:
            return Result(
                success=False,
                data={},
                error=f"Request failed: {e}",
            )
        finally:
            client.close()
