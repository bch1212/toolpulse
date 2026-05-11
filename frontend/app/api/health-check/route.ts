/**
 * Free MCP health-check API — no auth, no rate-limit-per-account
 * (rate-limited by edge in production). Probes the supplied URL and
 * returns latency + tool list + shape fingerprint.
 */

import { createHash } from "node:crypto";

export const runtime = "nodejs";

export async function POST(req: Request) {
  let url = "";
  try {
    const body = await req.json();
    url = body.url;
  } catch {
    return Response.json({ ok: false, latencyMs: 0, error: "invalid json" }, { status: 400 });
  }

  if (!url || !/^https?:\/\//.test(url)) {
    return Response.json({ ok: false, latencyMs: 0, error: "invalid url" }, { status: 400 });
  }

  const start = performance.now();
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: "toolpulse-probe",
        method: "tools/list",
        params: {},
      }),
      signal: AbortSignal.timeout(10_000),
    });
    const latencyMs = Math.round(performance.now() - start);

    let json: any = null;
    try {
      json = await res.json();
    } catch {}

    const tools = json?.result?.tools ?? [];
    const fingerprint = createHash("sha256")
      .update(JSON.stringify(extractShape(json)))
      .digest("hex")
      .slice(0, 16);

    return Response.json({
      ok: res.ok && !json?.error,
      status: res.status,
      latencyMs,
      toolCount: Array.isArray(tools) ? tools.length : 0,
      tools: Array.isArray(tools)
        ? tools.slice(0, 50).map((t: any) => ({ name: t.name, description: t.description }))
        : [],
      shapeFingerprint: fingerprint,
      error: json?.error?.message,
    });
  } catch (e) {
    return Response.json({
      ok: false,
      latencyMs: Math.round(performance.now() - start),
      error: e instanceof Error ? e.message : String(e),
    });
  }
}

function extractShape(obj: any): any {
  if (obj === null || obj === undefined) return "null";
  if (typeof obj === "boolean") return "bool";
  if (typeof obj === "number") return Number.isInteger(obj) ? "int" : "float";
  if (typeof obj === "string") return "str";
  if (Array.isArray(obj)) return obj.length === 0 ? ["__empty__"] : [extractShape(obj[0])];
  if (typeof obj === "object") {
    const out: Record<string, any> = {};
    for (const k of Object.keys(obj).sort()) out[k] = extractShape(obj[k]);
    return out;
  }
  return typeof obj;
}
