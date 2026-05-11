"""MCP middleware — wrap an entire MCP server's tool surface in one call.

Usage with FastMCP:
    from mcp.server.fastmcp import FastMCP
    from toolpulse import wrap_mcp_server

    mcp = FastMCP("my-server")

    @mcp.tool()
    async def search(q: str) -> dict: ...

    wrap_mcp_server(mcp, agent_id="my-mcp-server")  # all tools now monitored
"""

from __future__ import annotations

from typing import Any

from .wrapper import monitor


def wrap_mcp_server(server: Any, agent_id: str | None = None) -> Any:
    """Wrap every tool in a FastMCP-style server with the @monitor decorator.

    Works with FastMCP. For other MCP server frameworks, the integration is
    a one-line `@monitor` on each tool function.
    """
    # FastMCP exposes registered tools through `_tool_manager` or `tools`.
    # We probe both to stay compatible across versions.
    tool_manager = getattr(server, "_tool_manager", None) or getattr(server, "tool_manager", None)
    if tool_manager is None:
        raise RuntimeError(
            "wrap_mcp_server: could not find a tool manager on this server. "
            "Add @monitor() to each tool function instead."
        )

    tools = getattr(tool_manager, "_tools", None) or getattr(tool_manager, "tools", None)
    if tools is None:
        raise RuntimeError("wrap_mcp_server: tool manager has no tool registry")

    items = tools.items() if hasattr(tools, "items") else enumerate(tools)
    for name, tool in items:
        original = getattr(tool, "fn", None) or getattr(tool, "func", None) or getattr(tool, "callable", None)
        if original is None:
            continue
        wrapped = monitor(tool_name=name, agent_id=agent_id)(original)
        # Re-attach in whichever attribute the framework uses
        for attr in ("fn", "func", "callable"):
            if hasattr(tool, attr):
                setattr(tool, attr, wrapped)
                break
    return server
