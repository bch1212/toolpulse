"use client";

import { useEffect, useState } from "react";

interface ToolRow {
  tool_name: string;
  calls_24h: number;
  avg_latency_ms: number;
  success_rate: number;
}

export default function StatusPage() {
  const [data, setData] = useState<{ tools: ToolRow[]; as_of: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "https://api-production-2181.up.railway.app";
    fetch(`${apiUrl}/public/status/summary`)
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-6 py-16">
      <div className="flex items-baseline justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-4xl font-bold text-white">Live LLM Tool Status</h1>
          <p className="mt-2 text-gray-400">
            Real measurements from our own agent stack. Updated every 5 minutes.
          </p>
        </div>
        {data && (
          <div className="text-xs text-gray-500">
            As of {new Date(data.as_of).toLocaleString()}
          </div>
        )}
      </div>

      <div className="mt-10 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-900/50 text-left">
            <tr>
              <th className="p-4">Tool</th>
              <th className="p-4">Calls (24h)</th>
              <th className="p-4">Avg latency</th>
              <th className="p-4">Success rate</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {!data && !error && (
              <tr><td colSpan={5} className="p-8 text-center text-gray-500">Loading…</td></tr>
            )}
            {error && (
              <tr><td colSpan={5} className="p-8 text-center text-gray-500">Status feed temporarily unavailable.</td></tr>
            )}
            {data && data.tools.length === 0 && (
              <tr><td colSpan={5} className="p-8 text-center text-gray-500">
                Bootstrapping — first measurements publish within 24 hours of launch.
              </td></tr>
            )}
            {data && data.tools.map((t) => (
              <tr key={t.tool_name}>
                <td className="p-4 font-mono text-gray-300">{t.tool_name}</td>
                <td className="p-4 text-gray-400">{t.calls_24h.toLocaleString()}</td>
                <td className="p-4 text-gray-400">{t.avg_latency_ms} ms</td>
                <td className="p-4 text-gray-400">{(t.success_rate * 100).toFixed(2)}%</td>
                <td className="p-4">
                  {t.success_rate > 0.99 ? <span className="text-green-400">✓ healthy</span>
                   : t.success_rate > 0.95 ? <span className="text-yellow-400">⚠ degraded</span>
                   : <span className="text-red-400">● outage</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-8 text-sm text-gray-400">
        Want this on your own tools? <a href="/docs/quickstart">Set up in 60 seconds</a>.
      </div>

      <div className="mt-12 p-6 rounded-lg border border-accent/30 bg-accent/5">
        <h2 className="text-xl font-semibold text-white">Weekly &quot;State of LLM Tools&quot; report</h2>
        <p className="mt-2 text-gray-300">
          Subscribe via <a href="/feed.xml">RSS</a> for a weekly summary of latency,
          incidents, and shape changes across the LLM ecosystem.
        </p>
      </div>
    </div>
  );
}
