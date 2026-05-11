"""ToolPulse — agent tool reliability monitoring.

One-line decorator that records latency, success, and response shape
for every tool call your agent makes. Detects schema drift, runs synthetic
health checks, and alerts when tools degrade.

Usage:
    import os
    os.environ["TOOLPULSE_API_KEY"] = "tp_live_..."

    from toolpulse import monitor

    @monitor(tool_name="search_web", agent_id="my-agent")
    async def search_web(query: str) -> dict:
        ...
"""

from .wrapper import monitor
from .reporter import ToolPulseReporter, configure
from .schema_hash import fingerprint
from .mcp import wrap_mcp_server

__version__ = "0.1.0"
__all__ = [
    "monitor",
    "ToolPulseReporter",
    "configure",
    "fingerprint",
    "wrap_mcp_server",
]
