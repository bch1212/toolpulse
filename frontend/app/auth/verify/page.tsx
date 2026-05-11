"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function VerifyPage() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [status, setStatus] = useState<"verifying" | "ok" | "error">("verifying");
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMsg("missing token");
      return;
    }
    (async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
        const r = await fetch(`${apiUrl}/auth/verify?token=${encodeURIComponent(token)}`);
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail ?? "verification failed");
        // Persist the session JWT — set as cookie via document.cookie for SSR-friendly auth
        document.cookie = `tp_session=${j.session}; path=/; max-age=${30 * 86400}; samesite=lax`;
        sessionStorage.setItem("tp_session", j.session);
        if (j.first_api_key) setApiKey(j.first_api_key);
        setStatus("ok");
        if (!j.first_api_key) {
          // Returning user — straight to dashboard
          setTimeout(() => router.push("/dashboard"), 600);
        }
      } catch (e) {
        setStatus("error");
        setErrorMsg(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [token, router]);

  return (
    <div className="max-w-md mx-auto px-6 py-20">
      {status === "verifying" && (
        <div className="text-center text-gray-400">Verifying your sign-in link…</div>
      )}
      {status === "error" && (
        <div className="p-5 rounded-lg border border-red-700/40 bg-red-700/10">
          <p className="text-red-200">Sign-in failed</p>
          <p className="text-sm text-red-100/70 mt-2">{errorMsg}</p>
          <a href="/auth/signin" className="mt-4 inline-block text-accent">Try again →</a>
        </div>
      )}
      {status === "ok" && apiKey && (
        <div>
          <h1 className="text-2xl font-bold text-white">Welcome to ToolPulse</h1>
          <p className="mt-2 text-gray-400">Your account is ready. Here's your API key — copy it now, you won't see it again.</p>
          <pre className="mt-6 p-4 bg-gray-900 border border-accent rounded text-accent break-all">{apiKey}</pre>
          <p className="mt-4 text-sm text-gray-400">
            Set it as <code>TOOLPULSE_API_KEY</code> in your environment, then run:
          </p>
          <pre className="mt-2">{`pip install toolpulse

from toolpulse import monitor

@monitor(tool_name="my_tool")
async def my_tool(...): ...`}</pre>
          <a href="/dashboard" className="mt-6 inline-block px-5 py-2.5 rounded-md bg-accent text-white">
            Open dashboard →
          </a>
        </div>
      )}
      {status === "ok" && !apiKey && (
        <div className="text-center text-gray-400">Signed in. Redirecting…</div>
      )}
    </div>
  );
}
