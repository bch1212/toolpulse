"use client";

import { useState } from "react";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
      const r = await fetch(`${apiUrl}/auth/request-magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail ?? `request failed (${r.status})`);
      }
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="max-w-md mx-auto px-6 py-20">
      <h1 className="text-3xl font-bold text-white">Sign in to ToolPulse</h1>
      <p className="mt-2 text-gray-400">
        We'll email you a one-tap sign-in link. No passwords.
      </p>

      {status !== "sent" && (
        <form onSubmit={submit} className="mt-8 space-y-4">
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="w-full px-4 py-3 rounded-md bg-gray-900 border border-gray-700 focus:border-accent outline-none text-white"
          />
          <button
            type="submit"
            disabled={status === "sending"}
            className="w-full px-6 py-3 rounded-md bg-accent text-white font-medium disabled:opacity-50"
          >
            {status === "sending" ? "Sending…" : "Send sign-in link"}
          </button>
          {status === "error" && (
            <p className="text-red-400 text-sm">{errorMsg}</p>
          )}
        </form>
      )}

      {status === "sent" && (
        <div className="mt-8 p-5 rounded-lg border border-green-700/40 bg-green-700/10">
          <p className="text-green-200">Check your inbox.</p>
          <p className="text-sm text-green-100/70 mt-2">
            We sent a sign-in link to <strong>{email}</strong>. The link expires in 15 minutes.
          </p>
        </div>
      )}

      <div className="mt-12 text-sm text-gray-500">
        First time signing in? An account + your first API key are auto-issued
        on the first link click.
      </div>
    </div>
  );
}
