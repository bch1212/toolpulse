import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://toolpulse.io"),
  title: {
    default: "ToolPulse — Agent tool reliability monitoring",
    template: "%s | ToolPulse",
  },
  description:
    "One-line decorator. Latency, success/failure, schema drift detection, and synthetic health checks for every AI agent tool call.",
  openGraph: {
    type: "website",
    siteName: "ToolPulse",
    title: "ToolPulse — Agent tool reliability monitoring",
    description:
      "Catch silent tool failures before your agent acts on bad data.",
  },
  twitter: { card: "summary_large_image" },
  alternates: { canonical: "/" },
  other: {
    // Hint to AI crawlers that we publish llms.txt
    "ai-content": "/llms.txt",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* JSON-LD organization markup */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "ToolPulse",
              applicationCategory: "DeveloperApplication",
              operatingSystem: "Any",
              description:
                "Agent tool reliability monitoring with schema drift detection and synthetic health checks.",
              offers: {
                "@type": "AggregateOffer",
                lowPrice: "0",
                highPrice: "499",
                priceCurrency: "USD",
              },
            }),
          }}
        />
      </head>
      <body className="min-h-screen flex flex-col">
        <header className="border-b border-gray-800 bg-ink/90 backdrop-blur sticky top-0 z-40">
          <nav className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between text-sm">
            <Link href="/" className="font-semibold text-white">
              <span className="text-accent">tool</span>pulse
            </Link>
            <div className="flex items-center gap-6">
              <Link href="/docs">Docs</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/compare">Compare</Link>
              <Link href="/blog">Blog</Link>
              <Link href="/status">Status</Link>
              <Link href="/tools/health-check">Free tool</Link>
              <Link
                href="/auth/signin"
                className="px-3 py-1.5 rounded-md bg-accent text-white hover:bg-accent/90"
              >
                Sign in
              </Link>
            </div>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-gray-800 mt-16">
          <div className="max-w-6xl mx-auto px-6 py-8 text-sm text-gray-500 flex flex-wrap gap-6 items-center justify-between">
            <div>© {new Date().getFullYear()} ToolPulse</div>
            <div className="flex gap-6">
              <Link href="/llms.txt">llms.txt</Link>
              <Link href="/feed.xml">RSS</Link>
              <a href="https://github.com/toolpulse/toolpulse">GitHub</a>
              <a href="https://pypi.org/project/toolpulse/">PyPI</a>
              <a href="https://www.npmjs.com/package/toolpulse">npm</a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
