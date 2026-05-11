// Cloudflare Pages Function — runs on the edge alongside the static site.
// Replaces the Next.js route handler, since output: "export" doesn't allow API routes.

interface Env {}

export const onRequestPost: PagesFunction<Env> = async ({ request }) => {
  let url = "";
  try {
    const body = await request.json<{ url: string }>();
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
    try { json = await res.json(); } catch {}

    const tools = json?.result?.tools ?? [];
    const fingerprint = await sha256Hex(JSON.stringify(extractShape(json)));

    return Response.json({
      ok: res.ok && !json?.error,
      status: res.status,
      latencyMs,
      toolCount: Array.isArray(tools) ? tools.length : 0,
      tools: Array.isArray(tools)
        ? tools.slice(0, 50).map((t: any) => ({ name: t.name, description: t.description }))
        : [],
      shapeFingerprint: fingerprint.slice(0, 16),
      error: json?.error?.message,
    });
  } catch (e) {
    return Response.json({
      ok: false,
      latencyMs: Math.round(performance.now() - start),
      error: e instanceof Error ? e.message : String(e),
    });
  }
};

async function sha256Hex(input: string): Promise<string> {
  const buf = new TextEncoder().encode(input);
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(hash)).map((b) => b.toString(16).padStart(2, "0")).join("");
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
