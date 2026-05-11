import Link from "next/link";
import { COMPETITORS } from "@/lib/content";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Compare ToolPulse vs alternatives",
  description:
    "How ToolPulse compares to Langfuse, Helicone, Arize Phoenix, AgentOps, and Langtrace for AI agent tool monitoring.",
};

export default function ComparePage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-bold text-white">Compare ToolPulse</h1>
      <p className="mt-4 text-gray-400">
        Honest, side-by-side comparisons against the major LLM observability tools.
      </p>
      <ul className="mt-10 space-y-4">
        {COMPETITORS.map((c) => (
          <li key={c.slug} className="border border-gray-800 rounded-lg p-5 hover:border-accent">
            <Link href={`/compare/${c.slug}`} className="text-xl font-medium text-white">
              ToolPulse vs {c.name} →
            </Link>
            <p className="text-gray-400 mt-1">{c.tagline}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
