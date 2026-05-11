import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Quickstart",
  description: "Install ToolPulse, add the @monitor decorator, see calls in the dashboard within 60 seconds.",
};

export default function Quickstart() {
  return (
    <article className="max-w-3xl mx-auto px-6 py-16 prose">
      <h1 className="text-4xl font-bold text-white">Quickstart</h1>

      <h2>1. Install</h2>
      <pre>{`pip install toolpulse
# or
npm install toolpulse`}</pre>

      <h2>2. Get an API key</h2>
      <p><a href="/auth/signin">Sign in</a> — your first API key is auto-issued and shown once.</p>
      <pre>{`export TOOLPULSE_API_KEY=tp_live_xxxxxxxxxxxxx`}</pre>

      <h2>3. Wrap a tool</h2>
      <pre>{`from toolpulse import monitor

@monitor(tool_name="search_web", agent_id="my-agent")
async def search_web(query: str) -> dict:
    # your existing code, unchanged
    ...`}</pre>

      <h2>4. Run your agent</h2>
      <p>That's it. Every call is recorded. Open the <a href="/dashboard">dashboard</a> to see latency
      and success rate per tool, drift events as they happen, and recent calls with their response shapes.</p>

      <h2>5. Configure alerts (optional)</h2>
      <p>Add a Discord, Slack, or webhook alert channel from the dashboard, then drift events and synthetic-check failures fan out to all configured channels.</p>

      <h2>MCP servers — wrap the whole server in one line</h2>
      <pre>{`from mcp.server.fastmcp import FastMCP
from toolpulse import wrap_mcp_server

mcp = FastMCP("my-server")
# ... register your tools ...
wrap_mcp_server(mcp, agent_id="my-mcp-server")`}</pre>
    </article>
  );
}
