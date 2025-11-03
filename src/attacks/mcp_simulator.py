"""Phase 2: MCP context builder.

Provides utilities to build an MCP-style context from a user query and a set
of tools, with validation and multiple serialization formats suitable for LLM
input (string and JSON). Designed to be lightweight and independent from any
specific MCP runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolMetadata:
    """Minimal tool metadata aligned with the schema in data/schemas/tool_schema.json."""

    name: str
    description: str
    parameters: Dict[str, Any]
    server: str = "UnknownServer"

    def to_dict(self) -> Dict[str, Any]:
        """Return dict representation of tool metadata."""
        return asdict(self)


class ToolRegistry:
    """Registry for tools available to the MCP context builder."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._tools: Dict[str, ToolMetadata] = {}

    def register(self, tool: ToolMetadata) -> None:
        """Register a single tool after validation."""
        self._validate_tool(tool)
        self._tools[tool.name] = tool

    def bulk_register(self, tools: List[ToolMetadata]) -> None:
        """Register multiple tools."""
        for t in tools:
            self.register(t)

    def get(self, name: str) -> Optional[ToolMetadata]:
        """Return tool by name if present."""
        return self._tools.get(name)

    def list(self) -> List[ToolMetadata]:
        """List all registered tools."""
        return list(self._tools.values())

    def _validate_tool(self, tool: ToolMetadata) -> None:
        """Validate required fields and types for a tool."""
        if not tool.name:
            raise ValueError("Tool.name is required")
        if not tool.description:
            raise ValueError("Tool.description is required")
        if not isinstance(tool.parameters, dict):
            raise ValueError("Tool.parameters must be a dict")


class MCPContextBuilder:
    """Build MCP context blocks for LLM input.

    The builder accepts a user query and an ordered set of tools. It can emit a
    compact textual representation that is easy to feed to an LLM, and a JSON
    representation for programmatic inspection.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        """Create a builder bound to a tool registry."""
        self.registry = registry

    def build_context(
        self,
        user_query: str,
        tool_names: List[str],
        include_servers: bool = True,
    ) -> Dict[str, Any]:
        """Create a normalized MCP context dict.

        Args:
            user_query: The user's natural language request.
            tool_names: Ordered list of tool names to include in context.
            include_servers: Whether to include the `server` field in output.

        Returns:
            A dict with `user_query` and `tools` entries.
        """
        tools: List[Dict[str, Any]] = []
        for name in tool_names:
            tool = self.registry.get(name)
            if tool is None:
                raise KeyError(f"Tool not found in registry: {name}")
            tool_dict = tool.to_dict()
            if not include_servers:
                tool_dict.pop("server", None)
            tools.append(tool_dict)

        return {"user_query": user_query, "tools": tools}

    def serialize_text(self, context: Dict[str, Any]) -> str:
        r"""Serialize context to an LLM-friendly text block.

        Format:
            User: <query>\n
            Tools:\n
            - <name>: <description>\n
              params: <json>
        """
        lines: List[str] = []
        lines.append(f"User: {context['user_query']}")
        lines.append("")
        lines.append("Tools:")
        for tool in context["tools"]:
            lines.append(f"- {tool['name']}: {tool['description']}")
            lines.append(f"  params: {tool['parameters']}")
        return "\n".join(lines)

    def serialize_json(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a JSON-serializable structure for the context."""
        return context


__all__ = [
    "ToolMetadata",
    "ToolRegistry",
    "MCPContextBuilder",
]
