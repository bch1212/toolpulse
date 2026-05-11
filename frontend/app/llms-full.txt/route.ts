/**
 * /llms-full.txt — full content of every page concatenated for AI consumption.
 * Crawlers and agents fetch this once instead of crawling N pages.
 */

import fs from "node:fs";
import path from "node:path";
import { listPosts, COMPETITORS } from "@/lib/content";

export const dynamic = "force-static";
export const revalidate = 3600;

export async function GET() {
  const posts = listPosts();
  const sections: string[] = [];

  sections.push("# ToolPulse — full content index for AI consumption\n");
  sections.push("Agent tool reliability monitoring with schema drift detection and synthetic health checks. SDK is open source (MIT) for Python and TypeScript.\n");

  // Quickstart inline
  sections.push("## Quickstart\n");
  sections.push("```\npip install toolpulse\nexport TOOLPULSE_API_KEY=tp_live_...\n```\n");
  sections.push("```python\nfrom toolpulse import monitor\n\n@monitor(tool_name='search_web', agent_id='my-agent')\nasync def search_web(query: str) -> dict:\n    ...\n```\n");

  // Comparisons
  sections.push("## Comparisons\n");
  for (const c of COMPETITORS) {
    sections.push(`### ToolPulse vs ${c.name}\n${c.tagline}\n`);
    for (const d of c.differences) sections.push(`- ${d}`);
    sections.push("");
  }

  // Blog posts (full text)
  if (posts.length) {
    sections.push("## Blog posts\n");
    for (const p of posts) {
      sections.push(`### ${p.frontmatter.title}\n`);
      sections.push(`Published ${p.frontmatter.date} | Category: ${p.frontmatter.category}\n`);
      sections.push(p.content);
      sections.push("\n---\n");
    }
  }

  return new Response(sections.join("\n"), {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
