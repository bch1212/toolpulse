# ToolPulse Health Check — GitHub Action

Probe an MCP server or any HTTP endpoint from CI. Fail the workflow on outage or schema drift.

## Quick start

```yaml
- uses: toolpulse/health-check-action@v1
  with:
    endpoint: https://my-mcp-server.example.com/mcp
    type: mcp
    expected-shape: 4f3a98c1abcd1234   # optional — fail if response shape changes
    api-key: ${{ secrets.TOOLPULSE_API_KEY }}  # optional — also report to your dashboard
```

## Inputs

| Input | Default | Description |
|---|---|---|
| `endpoint` | _(required)_ | URL to probe |
| `type` | `mcp` | `mcp` (calls `tools/list`) or `http` (plain GET) |
| `expected-shape` | — | If set, the action fails when the live shape doesn't match |
| `api-key` | — | If set, the result is reported to ToolPulse |
| `fail-on-drift` | `true` | If false, drift becomes a warning, not a failure |

## Outputs

| Output | Description |
|---|---|
| `ok` | `true` / `false` |
| `latency-ms` | probe latency |
| `shape-fingerprint` | 16-char SHA-256 of the response shape |
| `status` | HTTP status code |

## Why use it

- Catch breaking shape changes in dependencies *before* prod traffic hits them.
- Run on a schedule (cron `*/30 * * * *`) for cheap synthetic monitoring without standing up a service.
- Pair with the [ToolPulse SDK](https://pypi.org/project/toolpulse/) for full agent-tool reliability monitoring.

MIT licensed. No external runtime dependencies.
