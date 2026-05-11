"use client";

import { useState, useEffect } from "react";
import Dashboard from "@/components/Dashboard";

export default function DashboardPage() {
  const [apiKey, setApiKey] = useState<string>("");
  const [issued, setIssued] = useState<boolean>(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("tp_api_key");
    if (stored) setApiKey(stored);
  }, []);

  function saveKey() {
    sessionStorage.setItem("tp_api_key", apiKey);
    setIssued(true);
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex items-baseline justify-between flex-wrap gap-4">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <a href="/dashboard/settings" className="text-sm text-gray-400 hover:text-accent">
          Settings & API keys
        </a>
      </div>

      {!apiKey && (
        <div className="mt-8 border border-yellow-700/40 bg-yellow-700/10 rounded-lg p-5">
          <p className="text-yellow-200">
            Paste your ToolPulse API key (starts with <code>tp_live_</code>) to load your data.
          </p>
          <p className="text-xs text-yellow-100/60 mt-2">
            In production, this comes from Clerk auth automatically. This form is for local dev.
          </p>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="tp_live_..."
              className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded font-mono text-sm"
            />
            <button onClick={saveKey} className="px-4 py-2 bg-accent rounded text-white">
              Load
            </button>
          </div>
        </div>
      )}

      {apiKey && (
        <div className="mt-10">
          <Dashboard apiKey={apiKey} />
        </div>
      )}

      {issued && (
        <div className="mt-6 text-sm text-green-400">Loaded.</div>
      )}
    </div>
  );
}
