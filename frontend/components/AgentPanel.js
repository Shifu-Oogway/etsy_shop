"use client";

import { useState } from "react";
import { api } from "../lib/api";

const AGENTS = [
  { name: "orchestrator", label: "Run full pipeline", primary: true },
  { name: "trend", label: "Scan trends" },
  { name: "analytics", label: "Refresh analytics" },
];

export default function AgentPanel({ onDone }) {
  const [busy, setBusy] = useState("");
  const [result, setResult] = useState(null);

  const run = async (name) => {
    setBusy(name);
    setResult(null);
    try {
      const res = await api.runAgent(name, {});
      setResult({ name, res });
    } catch (err) {
      setResult({ name, res: { ok: false, error: String(err) } });
    } finally {
      setBusy("");
      if (onDone) onDone();
    }
  };

  return (
    <section>
      <h2>Agents</h2>
      <div className="row">
        {AGENTS.map((a) => (
          <button
            key={a.name}
            className={a.primary ? "" : "secondary"}
            disabled={busy !== ""}
            onClick={() => run(a.name)}
          >
            {busy === a.name ? "Running…" : a.label}
          </button>
        ))}
      </div>
      {result && (
        <div style={{ marginTop: 12 }}>
          {result.res.ok ? (
            <span className="status published">{result.name} completed</span>
          ) : (
            <div className="error-box">{result.res.error || "failed"}{result.res.traceback ? "\n" + result.res.traceback : ""}</div>
          )}
        </div>
      )}
    </section>
  );
}
