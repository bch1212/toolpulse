import { COMPETITORS, getCompetitor } from "@/lib/content";
import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";

interface Props { params: { competitor: string } }

export function generateStaticParams() {
  return COMPETITORS.map((c) => ({ competitor: c.slug }));
}

export function generateMetadata({ params }: Props): Metadata {
  const c = getCompetitor(params.competitor);
  if (!c) return {};
  return {
    title: `ToolPulse vs ${c.name} — feature comparison`,
    description: `${c.tagline} See where ToolPulse and ${c.name} differ on AI agent tool monitoring.`,
    alternates: { canonical: `/compare/${c.slug}` },
  };
}

export default function CompetitorComparePage({ params }: Props) {
  const c = getCompetitor(params.competitor);
  if (!c) return notFound();

  return (
    <article className="max-w-3xl mx-auto px-6 py-16">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            headline: `ToolPulse vs ${c.name}`,
            description: c.tagline,
          }),
        }}
      />
      <Link href="/compare" className="text-sm text-gray-400">← All comparisons</Link>
      <h1 className="text-4xl font-bold text-white mt-4">ToolPulse vs {c.name}</h1>
      <p className="mt-3 text-gray-400">{c.tagline}</p>

      <h2 className="text-2xl font-semibold text-white mt-12">Key differences</h2>
      <ul className="mt-4 space-y-3 text-gray-300">
        {c.differences.map((d) => (
          <li key={d} className="flex gap-3">
            <span className="text-accent">→</span>
            <span>{d}</span>
          </li>
        ))}
      </ul>

      <h2 className="text-2xl font-semibold text-white mt-12">When to choose ToolPulse</h2>
      <ul className="mt-4 space-y-2 text-gray-300 list-disc list-inside">
        <li>You're building agents that call multiple tools and need shape-level integrity guarantees.</li>
        <li>You're using MCP and want first-class monitoring without writing a proxy.</li>
        <li>You want synthetic checks that proactively page you when a tool degrades.</li>
      </ul>

      <h2 className="text-2xl font-semibold text-white mt-12">When {c.name} might be a better fit</h2>
      <p className="mt-4 text-gray-300">
        If your primary need is prompt-level traces, evals, or self-hosted deployment today,
        {" "}{c.name} may serve you better. ToolPulse focuses narrowly on tool-call reliability.
      </p>

      <div className="mt-16 p-6 rounded-lg border border-accent/30 bg-accent/5">
        <h3 className="text-xl font-semibold text-white">Try ToolPulse free</h3>
        <p className="text-gray-300 mt-2">
          100K calls/month, no credit card. Decorator integrates in one line.
        </p>
        <Link
          href="/dashboard"
          className="mt-4 inline-block px-5 py-2.5 rounded-md bg-accent text-white"
        >
          Start free →
        </Link>
      </div>
    </article>
  );
}
