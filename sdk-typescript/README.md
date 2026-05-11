# toolpulse — agent tool reliability monitoring (TypeScript)

[![npm version](https://img.shields.io/npm/v/toolpulse.svg)](https://www.npmjs.com/package/toolpulse)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

One-line wrapper. Catches the silent tool failures your agent can't.

```bash
npm install toolpulse
```

```ts
import { monitor } from "toolpulse";

const searchWeb = monitor(async (query: string) => {
  // your existing tool, unchanged
  return await fetch(`...?q=${query}`).then(r => r.json());
}, { toolName: "search_web", agentId: "my-agent" });
```

That's it. Every call is recorded, schema drift is detected, and you get a dashboard at [toolpulse.io](https://toolpulse.io).

```bash
export TOOLPULSE_API_KEY=tp_live_xxxxxxxxxxxxx
```

## Why ToolPulse

Agent tools fail silently — APIs change response shapes, latency creeps up, exceptions get caught and forgotten. ToolPulse records every tool call, fingerprints the response shape, alerts on schema drift, and runs synthetic health checks.

## Drop-in for popular agent frameworks

```ts
// Vercel AI SDK
import { tool } from "ai";
import { monitor } from "toolpulse";

const search = tool({
  description: "search the web",
  parameters: z.object({ query: z.string() }),
  execute: monitor(async ({ query }) => { /* ... */ }, { toolName: "search" }),
});

// LangChain.js
import { DynamicStructuredTool } from "@langchain/core/tools";
new DynamicStructuredTool({
  name: "search",
  func: monitor(async (input) => { /* ... */ }, { toolName: "search" }),
  // ...
});

// MCP TypeScript server
server.tool("search", { query: z.string() }, monitor(handler, { toolName: "search" }));
```

## License

MIT
