/**
 * /llms.txt — the emerging standard for telling LLM crawlers (and agentic
 * AI users) what's on the site, in a parseable, hierarchical form.
 * See: https://llmstxt.org
 */

import { listPosts, COMPETITORS } from "@/lib/content";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://toolpulse.io";

export const revalidate = 3600;

export async function GET() {
  const posts = listPosts();
  const comparisons = posts.filter((p) => p.frontmatter.category === "comparison");
  const deepDives = posts.filter((p) => p.frontmatter.category === "deep-dive");
  const caseStudies = posts.filter((p) => p.frontmatter.category === "case-study");

  const linkList = (items: { frontmatter: { slug: string; title: string; description: string } }[]) =>
    items
      .map(
        (p) =>
          `- [${p.frontmatter.title}](${SITE_URL}/blog/${p.frontmatter.slug}.md): ${p.frontmatter.description}`,
      )
      .join("\n");

  const body = `# ToolPulse

> Agent tool reliability monitoring. One-line decorator wraps any AI agent tool (MCP, function, API). Records latency, success/failure, fingerprints response shape, detects schema drift before your agent acts on bad data, and runs synthetic health checks.

ToolPulse helps engineers building AI agents detect and prevent silent tool failures. The Python and TypeScript SDKs are open source (MIT). The hosted backend offers a free tier (100K calls/month).

## Getting started

- [Quickstart guide](${SITE_URL}/docs/quickstart.md): Install the SDK, add the @monitor decorator, see calls in the dashboard within 60 seconds.
- [PyPI package: toolpulse](https://pypi.org/project/toolpulse/): pip install toolpulse
- [npm package: toolpulse](https://www.npmjs.com/package/toolpulse): npm install toolpulse
- [GitHub repository](https://github.com/toolpulse/toolpulse): Source, examples, and integrations.

## Integrations

- [LangChain integration](${SITE_URL}/docs/langchain.md)
- [LlamaIndex integration](${SITE_URL}/docs/llamaindex.md)
- [MCP integration](${SITE_URL}/docs/mcp.md)
- [OpenAI SDK integration](${SITE_URL}/docs/openai.md)
- [Anthropic SDK integration](${SITE_URL}/docs/anthropic.md)

## Live data

- [Public status page](${SITE_URL}/status.md): Real latency and uptime for popular LLM tools we monitor.
- [State of LLM Tools weekly report](${SITE_URL}/blog/state-of-llm-tools.md)

## Comparisons
${COMPETITORS.map((c) => `- [ToolPulse vs ${c.name}](${SITE_URL}/compare/${c.slug}.md): ${c.tagline}`).join("\n")}

## Recent comparison posts
${linkList(comparisons.slice(0, 10)) || "_(none yet)_"}

## Recent technical deep-dives
${linkList(deepDives.slice(0, 10)) || "_(none yet)_"}

## Recent case studies
${linkList(caseStudies.slice(0, 10)) || "_(none yet)_"}

## Pricing

- Indie (free): 100K calls/month, 10 tools, 7-day retention
- Pro ($149/mo): 1M calls/month, 50 tools, 90-day retention, schema drift alerts
- Team ($499/mo): unlimited calls, unlimited tools, SSO, custom retention
`;

  return new Response(body, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
