/**
 * /feed.xml — RSS for the blog. AI scrapers and humans alike subscribe.
 */

import { listPosts } from "@/lib/content";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://toolpulse.io";

export const revalidate = 3600;

export async function GET() {
  const posts = listPosts();
  const items = posts
    .map(
      (p) => `
    <item>
      <title><![CDATA[${p.frontmatter.title}]]></title>
      <link>${SITE_URL}/blog/${p.frontmatter.slug}</link>
      <guid>${SITE_URL}/blog/${p.frontmatter.slug}</guid>
      <pubDate>${new Date(p.frontmatter.date).toUTCString()}</pubDate>
      <description><![CDATA[${p.frontmatter.description}]]></description>
      <category>${p.frontmatter.category}</category>
    </item>`,
    )
    .join("");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ToolPulse Blog</title>
    <link>${SITE_URL}/blog</link>
    <description>Comparison guides, technical deep-dives, and real failure case studies from monitoring AI agent tools.</description>
    <language>en-us</language>
    <atom:link xmlns:atom="http://www.w3.org/2005/Atom" href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
    ${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
}
