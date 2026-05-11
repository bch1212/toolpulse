import type { MetadataRoute } from "next";
import { listPosts, COMPETITORS } from "@/lib/content";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://toolpulse.io";

const STATIC_ROUTES = [
  "/",
  "/pricing",
  "/docs",
  "/docs/quickstart",
  "/docs/mcp",
  "/docs/langchain",
  "/blog",
  "/compare",
  "/status",
  "/tools/health-check",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticEntries = STATIC_ROUTES.map((path) => ({
    url: `${SITE_URL}${path}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: path === "/" ? 1.0 : 0.7,
  }));

  const compareEntries = COMPETITORS.map((c) => ({
    url: `${SITE_URL}/compare/${c.slug}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  const blogEntries = listPosts().map((p) => ({
    url: `${SITE_URL}/blog/${p.frontmatter.slug}`,
    lastModified: new Date(p.frontmatter.date),
    changeFrequency: "yearly" as const,
    priority: 0.5,
  }));

  return [...staticEntries, ...compareEntries, ...blogEntries];
}
