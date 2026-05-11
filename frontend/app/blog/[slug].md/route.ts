/**
 * /blog/[slug].md — raw markdown mirror of every blog post.
 * AI agents and llms.txt consumers prefer this over rendered HTML.
 */

import { getPost, listPosts } from "@/lib/content";

export async function generateStaticParams() {
  return listPosts().map((p) => ({ slug: p.frontmatter.slug }));
}

export async function GET(_req: Request, { params }: { params: { slug: string } }) {
  const post = getPost(params.slug);
  if (!post) return new Response("not found", { status: 404 });
  const fm = post.frontmatter;
  const body = `# ${fm.title}

> ${fm.description}

**Published:** ${fm.date}
**Category:** ${fm.category}
${fm.tags?.length ? `**Tags:** ${fm.tags.join(", ")}\n` : ""}
---

${post.content}
`;
  return new Response(body, {
    headers: { "Content-Type": "text/markdown; charset=utf-8" },
  });
}
