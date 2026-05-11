import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing — Free, Pro, Team",
  description:
    "Free tier covers 100K calls/month. Pro at $149/mo for 1M calls and schema drift alerts. Team at $499/mo for unlimited usage and SSO.",
};

const TIERS = [
  {
    name: "Indie",
    price: "Free",
    sub: "100K calls / month",
    features: [
      "10 monitored tools",
      "7-day call history",
      "Discord + Slack alerts",
      "Open-source SDK",
      "Free MCP health-checker",
    ],
    cta: "Start free",
    href: "/dashboard",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$149",
    sub: "per month — 1M calls",
    features: [
      "Unlimited agents, 50 tools",
      "90-day call history",
      "Schema drift alerts",
      "Synthetic health checks",
      "Email + webhook alerts",
      "Priority support",
    ],
    cta: "Upgrade to Pro",
    href: "/dashboard?plan=pro",
    highlight: true,
  },
  {
    name: "Team",
    price: "$499",
    sub: "per month — unlimited",
    features: [
      "Unlimited everything",
      "Custom retention",
      "SSO + audit log",
      "PagerDuty integration",
      "On-prem option (on roadmap)",
      "SLA",
    ],
    cta: "Upgrade to Team",
    href: "/dashboard?plan=team",
    highlight: false,
  },
];

export default function PricingPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-bold text-center text-white">Simple pricing</h1>
      <p className="mt-3 text-center text-gray-400">
        Free tier is generous and never expires. Upgrade only when you need it.
      </p>

      <div className="mt-12 grid md:grid-cols-3 gap-6">
        {TIERS.map((t) => (
          <div
            key={t.name}
            className={`rounded-xl border p-6 ${
              t.highlight ? "border-accent bg-accent/5" : "border-gray-800"
            }`}
          >
            <div className="text-sm uppercase tracking-wide text-accent">{t.name}</div>
            <div className="mt-4 text-4xl font-bold text-white">{t.price}</div>
            <div className="text-sm text-gray-400 mt-1">{t.sub}</div>
            <ul className="mt-6 space-y-2 text-sm text-gray-300">
              {t.features.map((f) => (
                <li key={f} className="flex gap-2">
                  <span className="text-accent">✓</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <Link
              href={t.href}
              className={`mt-6 block text-center px-4 py-2.5 rounded-md font-medium ${
                t.highlight
                  ? "bg-accent text-white"
                  : "border border-gray-700 hover:border-accent"
              }`}
            >
              {t.cta}
            </Link>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center text-sm text-gray-400">
        Need on-prem, custom retention, or a different volume? <Link href="/contact">Get in touch</Link>.
      </div>
    </div>
  );
}
