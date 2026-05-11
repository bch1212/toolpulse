"use client";

import useSWR from "swr";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

interface ToolHealthRow {
  tool_name: string;
  total_calls: number;
  successful: number;
  avg_latency_ms: number;
  p95_latency_ms: number | null;
  last_seen: string;
}

const fetcher = (url: string) =>
  fetch(url, {
    headers: { Authorization: `Bearer ${(window as any).__clerkToken ?? ""}` },
  }).then((r) => r.json());

export default function Dashboard({ apiKey }: { apiKey?: string }) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const headers: HeadersInit = apiKey ? { "X-API-Key": apiKey } : {};

  const { data: tools } = useSWR<ToolHealthRow[]>(
    apiKey ? [`${apiUrl}/tools`, "key"] : null,
    () => fetch(`${apiUrl}/tools`, { headers }).then((r) => r.json()),
    { refreshInterval: 30_000 },
  );

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Monitored tools</h2>
        <p className="text-sm text-gray-400 mt-1">Last 24 hours</p>
      </div>

      {!tools && <div className="text-gray-500">Loading…</div>}
      {tools && tools.length === 0 && (
        <div className="border border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-300">No calls yet. Add the <code>@monitor</code> decorator to a tool and run your agent.</p>
          <a href="/docs/quickstart" className="mt-4 inline-block text-accent">View quickstart →</a>
        </div>
      )}

      {tools && tools.length > 0 && (
        <div className="grid md:grid-cols-2 gap-4">
          {tools.map((t) => (
            <ToolCard key={t.tool_name} row={t} apiKey={apiKey} apiUrl={apiUrl} />
          ))}
        </div>
      )}
    </div>
  );
}

function ToolCard({
  row,
  apiKey,
  apiUrl,
}: {
  row: ToolHealthRow;
  apiKey?: string;
  apiUrl: string;
}) {
  const headers: HeadersInit = apiKey ? { "X-API-Key": apiKey } : {};
  const { data: history } = useSWR(
    apiKey ? [`${apiUrl}/tools/${row.tool_name}/latency`, "key"] : null,
    () =>
      fetch(`${apiUrl}/tools/${row.tool_name}/latency?hours=24`, { headers }).then(
        (r) => r.json(),
      ),
  );

  const successRate = row.total_calls > 0 ? (row.successful / row.total_calls) * 100 : 0;

  return (
    <div className="rounded-lg border border-gray-800 p-5">
      <div className="flex justify-between items-start">
        <div>
          <div className="font-mono text-white">{row.tool_name}</div>
          <div className="text-xs text-gray-500 mt-1">
            {row.total_calls.toLocaleString()} calls
          </div>
        </div>
        <div className="text-right text-sm">
          <div className="text-gray-400">{Math.round(row.avg_latency_ms)} ms avg</div>
          <div className={successRate > 99 ? "text-green-400" : "text-yellow-400"}>
            {successRate.toFixed(1)}% ok
          </div>
        </div>
      </div>
      {history && history.length > 0 && (
        <div className="mt-4 h-24">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <XAxis dataKey="hour" hide />
              <YAxis hide />
              <Tooltip
                contentStyle={{ background: "#111827", border: "1px solid #1f2937" }}
                formatter={(v: any) => `${Math.round(v)} ms`}
              />
              <Line type="monotone" dataKey="avg_ms" stroke="#7c3aed" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
