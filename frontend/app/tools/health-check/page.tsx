"use client";

import { useState } from "react";

interface CheckResult {
  ok: boolean;
  status?: number;
  latencyMs: number;
  error?: string;
  toolCount?: number;
  tools?: { name: string; description?: string }[];
  shapeFingerprint?: string;
}

export default function HealthCheckTool() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<CheckResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function runCheck(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch("/api/health-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      setResult(await r.json());
    } catch (err) {
      setResult({ ok: false, latencyMs: 0, error: String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-bold text-white">Free MCP Server Health Checker</h1>
      <p className="mt-3 text-gray-400">
        Paste your MCP server URL. We'll probe the <code>tools/list</code> endpoint,
        measure latency, and fingerprint the response shape. No signup required.
      </p>

      <form onSubmit={runCheck} className="mt-8 flex gap-2">
        <input
          required
          type="url"
          placeholder="https://your-mcp-server.example.com/mcp"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 px-4 py-3 rounded-md bg-gray-900 border border-gray-700 focus:border-accent outline-none text-white"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 rounded-md bg-accent text-white font-medium disabled:opacity-50"
        >
          {loading ? "Checking…" : "Check"}
        </button>
      </form>

      {result && (
        <div className="mt-8 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3">
            <span className={result.ok ? "text-green-400" : "text-red-400"}>
              {result.ok ? "● healthy" : "● error"}
            </span>
            <span className="text-gray-400 text-sm">{result.latencyMs} ms</span>
            {result.status && (
              <span className="text-gray-500 text-sm">HTTP {result.status}</span>
            )}
          </div>
          {result.error && <p className="mt-3 text-red-300 text-sm">{result.error}</p>}
          {result.toolCount !== undefined && (
            <p className="mt-3 text-gray-300">
              <strong>{result.toolCount}</strong> tools registered
            </p>
          )}
          {result.tools && result.tools.length > 0 && (
            <ul className="mt-2 space-y-1 text-sm text-gray-400 max-h-60 overflow-auto">
              {result.tools.map((t) => (
                <li key={t.name}>
                  <code className="text-accent">{t.name}</code>
                  {t.description ? ` — ${t.description}` : ""}
                </li>
              ))}
            </ul>
          )}
          {result.shapeFingerprint && (
            <p className="mt-4 text-xs text-gray-500">
              Response shape fingerprint: <code>{result.shapeFingerprint}</code>
            </p>
          )}
        </div>
      )}

      <div className="mt-12 p-6 rounded-lg border border-accent/30 bg-accent/5">
        <h2 className="text-xl font-semibold text-white">Want continuous monitoring?</h2>
        <p className="mt-2 text-gray-300">
          One-time checks are useful but tool failures happen at 3am too. Sign up free
          and get the <code>@monitor</code> decorator + scheduled health checks + drift
          alerts to Discord/Slack/email.
        </p>
        <a
          href="/dashboard"
          className="mt-4 inline-block px-5 py-2.5 rounded-md bg-accent text-white"
        >
          Get continuous monitoring →
        </a>
      </div>
    </div>
  );
}
