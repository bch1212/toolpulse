# ToolPulse — agent tool reliability monitoring

[![PyPI version](https://img.shields.io/pypi/v/toolpulse.svg)](https://pypi.org/project/toolpulse/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

**One-line decorator. Catches the silent tool failures your agent can't.**

ToolPulse is the observability layer for AI agent tool calls. Wrap any function — MCP tool, API call, database query — and ToolPulse records latency, success/failure, response shape, and detects schema drift before your agent acts on bad data.

```python
from toolpulse import monitor

@monitor(tool_name="search_web", agent_id="my-agent")
async def search_web(query: str) -> dict:
    # your existing tool code, unchanged
    ...
```

That's it. Every call is recorded, schema drift triggers alerts, and you get a dashboard at [toolpulse.io](https://toolpulse.io).

---

## Why

Agent tools fail silently. An API returns a slightly different shape, your agent passes it to the next step, and three tool calls later the agent makes a wrong decision based on data it never knew was malformed. By the time you notice, the user has had a bad experience and you're combing through traces.

ToolPulse catches:

- **Schema drift** — the API changed its response shape and your agent is now operating on an unexpected structure
- **Latency regressions** — a tool that used to take 200ms now takes 4 seconds and is starving downstream calls
- **Silent failures** — exceptions caught by your try/except that you forgot to alert on
- **Outright outages** — synthetic health checks ping your tools on a schedule and alert when they go dark

---

## Install

```bash
pip install toolpulse
```

Get a free API key at [toolpulse.io/signup](https://toolpulse.io/signup).

```bash
export TOOLPULSE_API_KEY=tp_live_xxxxxxxxxxxxx
```

---

## Usage

### Basic decorator (async or sync)

```python
from toolpulse import monitor

@monitor()
async def query_database(sql: str) -> list[dict]:
    ...

@monitor(tool_name="external_api", agent_id="research-agent", tags={"region": "us-east"})
def fetch_data(url: str) -> dict:
    ...
```

### MCP servers — wrap the whole server in one call

```python
from mcp.server.fastmcp import FastMCP
from toolpulse import wrap_mcp_server

mcp = FastMCP("my-server")

@mcp.tool()
async def search(q: str) -> dict: ...

@mcp.tool()
async def lookup(id: str) -> dict: ...

wrap_mcp_server(mcp, agent_id="my-mcp-server")
# All tools above are now monitored.
```

### LangChain tools

```python
from langchain.tools import tool
from toolpulse import monitor

@tool
@monitor(tool_name="search_web")
async def search_web(query: str) -> str:
    ...
```

### Configuration

```python
from toolpulse import configure

configure(
    api_key="tp_live_...",          # or TOOLPULSE_API_KEY env var
    endpoint="https://api.toolpulse.io",
    batch_size=50,                   # flush after N records
    flush_interval=5.0,              # or after N seconds
    enabled=True,
)
```

---

## How it works

- **Zero overhead on the hot path.** Records are queued in memory and flushed by a background thread. Your agent never waits on the network.
- **Never crashes the caller.** All monitoring exceptions are swallowed. Your tool's own exceptions are re-raised unchanged.
- **Shape-only fingerprinting.** We hash the *structure* of responses, not the values, so PII never leaves your environment.
- **Smart drift detection.** Compares each new response shape against the most common shape in the last 24 hours. Alerts deduped per hour.

---

## Pricing

| Plan | Price | Calls / mo | Tools | Retention |
|------|-------|------------|-------|-----------|
| Indie | Free | 100K | 10 | 7 days |
| Pro | $149/mo | 1M | 50 | 90 days |
| Team | $499/mo | unlimited | unlimited | custom |

[See full pricing →](https://toolpulse.io/pricing)

---

## Examples

See [`examples/`](https://github.com/toolpulse/toolpulse/tree/main/examples) for working integrations with:

- LangChain
- LlamaIndex
- CrewAI
- AutoGen
- OpenAI SDK
- Anthropic SDK
- raw MCP

---

## Comparison

| | ToolPulse | Langfuse | Helicone | Arize |
|---|---|---|---|---|
| Tool-level latency | ✅ | ✅ | ✅ | ✅ |
| Schema drift detection | ✅ | ❌ | ❌ | ❌ |
| Synthetic health checks | ✅ | ❌ | ❌ | ❌ |
| MCP-native | ✅ | partial | ❌ | ❌ |
| Free tier | 100K calls | 50K | 100K | trial |
| Self-host | roadmap | ✅ | ✅ | ❌ |

[Detailed comparisons →](https://toolpulse.io/compare)

---

## License

MIT — use it anywhere, including commercial projects.

## Contributing

Issues and PRs welcome at [github.com/toolpulse/toolpulse](https://github.com/toolpulse/toolpulse).
