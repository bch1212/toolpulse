import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Docs" };

const SECTIONS = [
  { href: "/docs/quickstart", title: "Quickstart", desc: "Install + decorator + first call in 60 seconds." },
  { href: "/docs/python-sdk", title: "Python SDK", desc: "@monitor decorator API reference." },
  { href: "/docs/typescript-sdk", title: "TypeScript SDK", desc: "monitor() wrapper API reference." },
  { href: "/docs/mcp", title: "MCP integration", desc: "wrap_mcp_server for FastMCP and TS MCP." },
  { href: "/docs/langchain", title: "LangChain", desc: "@monitor on tools and chains." },
  { href: "/docs/llamaindex", title: "LlamaIndex", desc: "Wrapping LlamaIndex tools." },
  { href: "/docs/openai", title: "OpenAI SDK", desc: "Monitoring tool calls in the OpenAI Assistants API." },
  { href: "/docs/anthropic", title: "Anthropic SDK", desc: "Monitoring tool_use blocks." },
  { href: "/docs/health-checks", title: "Synthetic checks", desc: "Configure scheduled probes." },
  { href: "/docs/alerts", title: "Alert channels", desc: "Discord, Slack, email, webhook." },
  { href: "/docs/badges", title: "Status badges", desc: "Embed live uptime in your README." },
  { href: "/docs/github-action", title: "GitHub Action", desc: "Run health checks in CI." },
];

export default function DocsIndex() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-bold text-white">Docs</h1>
      <p className="mt-3 text-gray-400">
        Everything you need to instrument, monitor, and alert on your AI agent's tools.
      </p>
      <div className="mt-10 grid md:grid-cols-2 gap-4">
        {SECTIONS.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="block p-5 rounded-lg border border-gray-800 hover:border-accent"
          >
            <div className="text-white font-medium">{s.title}</div>
            <div className="text-sm text-gray-400 mt-1">{s.desc}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
