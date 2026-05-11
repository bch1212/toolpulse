import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-20">
      <section className="text-center max-w-3xl mx-auto">
        <div className="inline-block px-3 py-1 rounded-full text-xs bg-accent/10 text-accent border border-accent/30 mb-6">
          Datadog for agent tools
        </div>
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-white">
          Catch the silent tool failures<br />your agent can't.
        </h1>
        <p className="mt-6 text-lg text-gray-400 leading-relaxed">
          One-line decorator wraps any tool — MCP, function, API. ToolPulse records
          latency and errors, fingerprints response shape, detects schema drift
          before your agent acts on bad data, and runs synthetic health checks.
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="px-6 py-3 rounded-md bg-accent text-white font-medium hover:bg-accent/90"
          >
            Start free — 100K calls/mo
          </Link>
          <Link
            href="/docs/quickstart"
            className="px-6 py-3 rounded-md border border-gray-700 hover:border-accent"
          >
            Read the docs
          </Link>
        </div>
      </section>

      <section className="mt-20 grid md:grid-cols-2 gap-8 items-start">
        <div>
          <h2 className="text-2xl font-semibold text-white mb-4">Install. Decorate. Done.</h2>
          <pre className="text-sm">{`pip install toolpulse

from toolpulse import monitor

@monitor(tool_name="search_web", agent_id="my-agent")
async def search_web(query: str) -> dict:
    # your existing tool, unchanged
    ...`}</pre>
          <p className="mt-4 text-sm text-gray-400">
            TypeScript users: <code>npm install toolpulse</code>
          </p>
        </div>
        <div>
          <h2 className="text-2xl font-semibold text-white mb-4">What you get</h2>
          <ul className="space-y-3 text-gray-300">
            <li className="flex gap-3">
              <span className="text-accent">→</span>
              <span><strong className="text-white">Schema drift detection.</strong> When an API silently changes its response shape, you find out before your agent does.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-accent">→</span>
              <span><strong className="text-white">Latency tracking per tool.</strong> Spot the tool that's now taking 4× longer than last week.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-accent">→</span>
              <span><strong className="text-white">Synthetic health checks.</strong> Cron-style probes alert you the moment a tool goes dark.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-accent">→</span>
              <span><strong className="text-white">Alerts to Discord, Slack, email, webhooks.</strong> No PagerDuty required.</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="mt-20 p-8 rounded-xl border border-gray-800 bg-gray-900/30">
        <h2 className="text-2xl font-semibold text-white mb-2">Live demo: our own agent stack</h2>
        <p className="text-gray-400 mb-6">
          Real latency, real drift events, real uptime — across the LLM tools we monitor for our own agents.
        </p>
        <Link
          href="/status"
          className="inline-block px-5 py-2.5 rounded-md bg-accent2/20 text-accent2 border border-accent2/30 hover:bg-accent2/30"
        >
          See the live status page →
        </Link>
      </section>

      <section className="mt-20">
        <h2 className="text-2xl font-semibold text-white mb-6">How we compare</h2>
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-900/50 text-left">
              <tr>
                <th className="p-4">Feature</th>
                <th className="p-4">ToolPulse</th>
                <th className="p-4">Langfuse</th>
                <th className="p-4">Helicone</th>
                <th className="p-4">Arize</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              <Row feature="Tool-level latency" tp="✓" lf="✓" hl="✓" az="✓" />
              <Row feature="Schema drift detection" tp="✓" lf="—" hl="—" az="—" />
              <Row feature="Synthetic health checks" tp="✓" lf="—" hl="—" az="—" />
              <Row feature="MCP-native" tp="✓" lf="partial" hl="—" az="—" />
              <Row feature="Free tier (calls/mo)" tp="100K" lf="50K" hl="100K" az="trial" />
              <Row feature="Self-host" tp="roadmap" lf="✓" hl="✓" az="—" />
            </tbody>
          </table>
        </div>
        <Link href="/compare" className="mt-4 inline-block text-sm">
          See detailed comparisons →
        </Link>
      </section>
    </div>
  );
}

function Row(props: { feature: string; tp: string; lf: string; hl: string; az: string }) {
  return (
    <tr>
      <td className="p-4 text-gray-300">{props.feature}</td>
      <td className="p-4 text-accent">{props.tp}</td>
      <td className="p-4 text-gray-400">{props.lf}</td>
      <td className="p-4 text-gray-400">{props.hl}</td>
      <td className="p-4 text-gray-400">{props.az}</td>
    </tr>
  );
}
