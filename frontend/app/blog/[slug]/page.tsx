import { getPost, listPosts } from "@/lib/content";
import { notFound } from "next/navigation";
import Link from "next/link";
import { MDXRemote } from "next-mdx-remote/rsc";
import type { Metadata } from "next";

interface Props { params: { slug: string } }

export async function generateStaticParams() {
  return listPosts().map((p) => ({ slug: p.frontmatter.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = getPost(params.slug);
  if (!post) return {};
  const { title, description } = post.frontmatter;
  return {
    title,
    description,
    alternates: { canonical: `/blog/${params.slug}` },
    openGraph: { title, description, type: "article" },
  };
}

export default function BlogPostPage({ params }: Props) {
  const post = getPost(params.slug);
  if (!post) return notFound();
  const { title, date, category, description } = post.frontmatter;

  return (
    <article className="max-w-3xl mx-auto px-6 py-16 prose">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            headline: title,
            datePublished: date,
            description,
            articleSection: category,
          }),
        }}
      />
      <Link href="/blog" className="text-sm text-gray-400">← Back to blog</Link>
      <div className="mt-4 text-xs uppercase tracking-wide text-accent">{category}</div>
      <h1 className="text-4xl font-bold text-white mt-2">{title}</h1>
      <div className="text-sm text-gray-500 mt-2">{new Date(date).toLocaleDateString()}</div>
      <div className="mt-8">
        <MDXRemote source={post.content} />
      </div>
      <div className="mt-12 text-sm text-gray-400">
        Also available as <Link href={`/blog/${params.slug}.md`}>raw markdown</Link> for AI agents.
      </div>
    </article>
  );
}
