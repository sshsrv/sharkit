from __future__ import annotations

from sharkit.exceptions import ToolNotFoundError
from sharkit.tools.base import Tool, ToolMetadata


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, type[Tool]] = {}
        self._paths: dict[str, str] = {}

    def register_tool(self, tool_class: type[Tool], path: str | None = None) -> None:
        name = tool_class.metadata.name
        self._tools[name] = tool_class
        if path:
            self._paths[path] = name

    def get_tool(self, key: str) -> type[Tool] | None:
        tool = self._tools.get(key)
        if tool is not None:
            return tool
        name = self._paths.get(key)
        if name is not None:
            return self._tools.get(name)
        return None

    def require_tool(self, key: str) -> type[Tool]:
        tool = self.get_tool(key)
        if tool is None:
            raise ToolNotFoundError(key)
        return tool

    def list_tools(self) -> list[ToolMetadata]:
        return [cls.metadata for cls in self._tools.values()]

    def search_tools(self, query: str) -> list[ToolMetadata]:
        lower_query = query.lower()
        return [
            tool.metadata
            for tool in self._tools.values()
            if lower_query in tool.metadata.name.lower()
            or lower_query in tool.metadata.description.lower()
        ]

    def find_tools(self, query: str) -> list[tuple[str, ToolMetadata]]:
        lower_query = query.lower()
        results: list[tuple[str, ToolMetadata]] = []
        for path, cls in self.get_all_tools().items():
            metadata = cls.metadata
            searchable = (
                f"{metadata.name} {metadata.description} {metadata.category} {path}".lower()
            )
            if lower_query in searchable:
                results.append((path, metadata))
        return results

    def get_tools_by_category(self, category: str) -> list[ToolMetadata]:
        lower_category = category.lower()
        return [
            tool.metadata
            for tool in self._tools.values()
            if tool.metadata.category.lower() == lower_category
        ]

    def get_all_tools(self) -> dict[str, type[Tool]]:
        result: dict[str, type[Tool]] = {}
        pathed_names = set(self._paths.values())
        for name, cls in self._tools.items():
            if name not in pathed_names:
                result[name] = cls
        for path, name in self._paths.items():
            result[path] = self._tools[name]
        return result

    def get_tool_path(self, name: str) -> str:
        """Return the full path for a tool name, or just the name if no path."""
        for path, tool_name in self._paths.items():
            if tool_name == name:
                return path
        return name

    def format_display(self, path: str) -> str:
        """Format tool path as 'category(subpath)' for display."""
        if "/" in path:
            parts = path.split("/", 1)
            return f"{parts[0]}({parts[1]})"
        return path
