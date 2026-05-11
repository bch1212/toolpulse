/**
 * Async batch reporter — buffers records and flushes on a timer or when the
 * batch fills. Never blocks the caller, never throws.
 */

export interface ReporterConfig {
  apiKey?: string;
  endpoint?: string;
  batchSize?: number;
  flushIntervalMs?: number;
  enabled?: boolean;
}

export interface ToolCallRecord {
  tool_name: string;
  agent_id: string;
  latency_ms: number;
  success: boolean;
  error: string | null;
  output_shape: string | null;
  output_shape_tree: unknown;
  tags: Record<string, unknown>;
  called_at: string;
}

const DEFAULTS: Required<ReporterConfig> = {
  apiKey: process.env.TOOLPULSE_API_KEY ?? "",
  endpoint: process.env.TOOLPULSE_ENDPOINT ?? "https://api.toolpulse.io",
  batchSize: 50,
  flushIntervalMs: 5000,
  enabled: true,
};

let cfg: Required<ReporterConfig> = { ...DEFAULTS };

export function configure(overrides: ReporterConfig): void {
  cfg = { ...cfg, ...DEFAULTS, ...overrides };
  if (overrides.apiKey === undefined && !cfg.apiKey) cfg.apiKey = "";
}

class Reporter {
  private queue: ToolCallRecord[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private static _instance: Reporter | null = null;

  static instance(): Reporter {
    if (!this._instance) this._instance = new Reporter();
    return this._instance;
  }

  private constructor() {
    this.timer = setInterval(() => this.flush(), cfg.flushIntervalMs);
    // Don't keep the process alive solely for the flush timer
    if (typeof this.timer === "object" && (this.timer as any).unref) {
      (this.timer as any).unref();
    }
    // Best-effort flush on exit
    if (typeof process !== "undefined" && process.on) {
      process.on("beforeExit", () => this.flush());
    }
  }

  record(rec: ToolCallRecord): void {
    if (!cfg.enabled || !cfg.apiKey) return;
    this.queue.push(rec);
    if (this.queue.length >= cfg.batchSize) this.flush();
  }

  async flush(): Promise<void> {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0, this.queue.length);
    try {
      const res = await fetch(`${cfg.endpoint.replace(/\/$/, "")}/ingest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": cfg.apiKey,
        },
        body: JSON.stringify(batch),
      });
      if (!res.ok && process.env.TOOLPULSE_DEBUG) {
        console.warn(`[toolpulse] ingest non-2xx: ${res.status}`);
      }
    } catch (e) {
      if (process.env.TOOLPULSE_DEBUG) {
        console.warn("[toolpulse] ingest failed:", e);
      }
    }
  }
}

export function getReporter(): Reporter {
  return Reporter.instance();
}
