/**
 * monitor() — wrap any async function (or sync function) so every call is
 * recorded by ToolPulse. Never throws monitoring exceptions, always
 * re-raises the wrapped function's own exceptions.
 */

import { extractShape, fingerprint } from "./schemaHash.js";
import { getReporter } from "./reporter.js";

export interface MonitorOptions {
  toolName?: string;
  agentId?: string;
  tags?: Record<string, unknown>;
  captureShape?: boolean;
}

export function monitor<T extends (...args: any[]) => any>(
  fn: T,
  opts: MonitorOptions = {},
): T {
  const name = opts.toolName ?? fn.name ?? "anonymous";
  const agentId = opts.agentId ?? "default";
  const tags = opts.tags ?? {};
  const captureShape = opts.captureShape ?? true;

  const wrapped = function (this: unknown, ...args: any[]) {
    const start = performance.now();
    let result: unknown;
    let error: string | null = null;
    try {
      result = fn.apply(this, args);
      // If the function returns a promise, wait for it before recording
      if (result instanceof Promise) {
        return result
          .then((v) => {
            recordSafe(name, agentId, start, v, null, tags, captureShape);
            return v;
          })
          .catch((e) => {
            recordSafe(name, agentId, start, undefined, formatError(e), tags, captureShape);
            throw e;
          });
      }
      recordSafe(name, agentId, start, result, null, tags, captureShape);
      return result;
    } catch (e) {
      error = formatError(e);
      recordSafe(name, agentId, start, undefined, error, tags, captureShape);
      throw e;
    }
  } as T;

  // Preserve original function name where possible
  Object.defineProperty(wrapped, "name", { value: name, configurable: true });
  return wrapped;
}

function formatError(e: unknown): string {
  const s = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
  return s.slice(0, 500);
}

function recordSafe(
  toolName: string,
  agentId: string,
  start: number,
  result: unknown,
  error: string | null,
  tags: Record<string, unknown>,
  captureShape: boolean,
): void {
  try {
    const latencyMs = Math.round(performance.now() - start);
    let shape: string | null = null;
    let shapeTree: unknown = null;
    if (captureShape && result !== undefined && result !== null && error === null) {
      try {
        shapeTree = extractShape(result);
        shape = fingerprint(result);
      } catch {
        // ignore
      }
    }
    getReporter().record({
      tool_name: toolName,
      agent_id: agentId,
      latency_ms: latencyMs,
      success: error === null,
      error,
      output_shape: shape,
      output_shape_tree: shapeTree,
      tags,
      called_at: new Date().toISOString(),
    });
  } catch {
    // Last-resort guard — never propagate
  }
}
