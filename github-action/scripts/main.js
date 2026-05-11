// ToolPulse Health Check GitHub Action — single-file Node 20 script.
// No external dependencies — uses only the Node standard library and global fetch.

const crypto = require("node:crypto");
const fs = require("node:fs");

function out(name, value) {
  const f = process.env.GITHUB_OUTPUT;
  if (f) fs.appendFileSync(f, `${name}=${value}\n`);
  console.log(`::notice::${name}=${value}`);
}

function fail(msg) {
  console.error(`::error::${msg}`);
  process.exit(1);
}

function input(name, fallback) {
  const env = process.env[`INPUT_${name.toUpperCase().replace(/-/g, "_")}`];
  return env && env.trim() !== "" ? env : fallback;
}

function extractShape(o) {
  if (o === null || o === undefined) return "null";
  if (typeof o === "boolean") return "bool";
  if (typeof o === "number") return Number.isInteger(o) ? "int" : "float";
  if (typeof o === "string") return "str";
  if (Array.isArray(o)) return o.length === 0 ? ["__empty__"] : [extractShape(o[0])];
  if (typeof o === "object") {
    const r = {};
    for (const k of Object.keys(o).sort()) r[k] = extractShape(o[k]);
    return r;
  }
  return typeof o;
}

function fingerprint(o) {
  return crypto
    .createHash("sha256")
    .update(JSON.stringify(extractShape(o)))
    .digest("hex")
    .slice(0, 16);
}

async function main() {
  const endpoint = input("endpoint");
  const type = input("type", "mcp");
  const expectedShape = input("expected-shape", "");
  const apiKey = input("api-key", "");
  const failOnDrift = (input("fail-on-drift", "true") || "").toLowerCase() === "true";

  if (!endpoint) fail("input 'endpoint' is required");

  const start = performance.now();
  let ok = false;
  let status = 0;
  let body = null;

  try {
    let res;
    if (type === "mcp") {
      res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: "tp-action",
          method: "tools/list",
          params: {},
        }),
      });
    } else {
      res = await fetch(endpoint);
    }
    status = res.status;
    try {
      body = await res.json();
    } catch {
      body = await res.text().catch(() => null);
    }
    ok = res.ok && (typeof body !== "object" || !body?.error);
  } catch (e) {
    fail(`probe failed: ${e instanceof Error ? e.message : String(e)}`);
    return;
  }

  const latencyMs = Math.round(performance.now() - start);
  const shape = fingerprint(body);

  out("ok", String(ok));
  out("latency-ms", String(latencyMs));
  out("shape-fingerprint", shape);
  out("status", String(status));

  // Optionally report to ToolPulse
  if (apiKey) {
    try {
      await fetch("https://api.toolpulse.io/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify([
          {
            tool_name: `gha:${endpoint}`,
            agent_id: "github-action",
            latency_ms: latencyMs,
            success: ok,
            error: ok ? null : `status=${status}`,
            output_shape: shape,
            tags: { source: "github-action", repo: process.env.GITHUB_REPOSITORY ?? "" },
          },
        ]),
      });
    } catch (e) {
      console.error(`::warning::toolpulse report failed: ${e}`);
    }
  }

  // Drift assertion
  if (expectedShape && expectedShape !== shape) {
    if (failOnDrift) {
      fail(`shape drift: expected ${expectedShape}, got ${shape}`);
    } else {
      console.warn(`::warning::shape drift: expected ${expectedShape}, got ${shape}`);
    }
  }

  if (!ok) fail(`probe returned non-ok status ${status}`);
  console.log(`✓ healthy: ${latencyMs}ms, shape=${shape}`);
}

main().catch((e) => fail(e instanceof Error ? e.message : String(e)));
