import Link from "next/link";
import { listPosts } from "@/lib/content";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Blog — Comparisons, deep-dives, real failures",
  description:
    "Weekly comparison guides, technical deep-dives, and real failure case studies from monitoring AI agent tools.",
};

export default function BlogIndex() {
  const posts = listPosts();
  const groups = {
    comparison: posts.filter((p) => p.frontmatter.category === "comparison"),
    "deep-dive": posts.filter((p) => p.frontmatter.category === "deep-dive"),
    "case-study": posts.filter((p) => p.frontmatter.category === "case-study"),
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-bold text-white">Blog</h1>
      <p className="mt-3 text-gray-400">
        New posts every week — comparison guides, deep technical dives, and real
        failures we caught monitoring our own agent stack.
        <Link href="/feed.xml" className="ml-2 text-sm">RSS</Link>
      </p>

      {posts.length === 0 ? (
        <p className="mt-12 text-gray-500">First posts publishing this week.</p>
      ) : (
        <div className="mt-10 space-y-12">
          {(["comparison", "deep-dive", "case-study"] as const).map((cat) =>
            groups[cat].length === 0 ? null : (
              <section key={cat}>
                <h2 className="text-xs uppercase tracking-wider text-accent mb-4">
                  {cat.replace("-", " ")}
                </h2>
                <ul className="space-y-4">
                  {groups[cat].map((p) => (
                    <li key={p.frontmatter.slug} className="border-b border-gray-800 pb-4">
                      <Link
                        href={`/blog/${p.frontmatter.slug}`}
                        className="text-xl font-medium text-white hover:text-accent block"
                      >
                        {p.frontmatter.title}
                      </Link>
                      <p className="text-gray-400 mt-1">{p.frontmatter.description}</p>
                      <div className="text-xs text-gray-500 mt-2">
                        {new Date(p.frontmatter.date).toLocaleDateString()}
                        {p.frontmatter.generatedBy && (
                          <span className="ml-2">· auto-published from live data</span>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ),
          )}
        </div>
      )}
    </div>
  );
}
