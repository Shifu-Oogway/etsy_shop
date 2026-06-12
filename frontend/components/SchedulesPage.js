"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";

const AGENTS = ["orchestrator", "trend", "analytics", "seo", "qa", "publisher", "experiment"];

const PRESETS = [
  { label: "Daily 6:00",       cron: "0 6 * * *" },
  { label: "Daily 5:30",       cron: "30 5 * * *" },
  { label: "Every hour",       cron: "0 * * * *" },
  { label: "Every 15 min",     cron: "*/15 * * * *" },
  { label: "Weekdays 9:00",    cron: "0 9 * * 0-4" },
];

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", cron: "0 6 * * *",
                                     task_name: "orchestrator", enabled: true });
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    try { setSchedules(await api.schedules()); setError(""); }
    catch (e) { setError(String(e)); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!form.name.trim()) return;
    setBusy("create");
    try { await api.createSchedule(form);
          setForm({ name: "", cron: "0 6 * * *", task_name: "orchestrator", enabled: true });
          load(); }
    catch (e) { alert(String(e)); }
    finally { setBusy(""); }
  };

  const toggle = async (id) => {
    setBusy(`t-${id}`);
    try { await api.toggleSchedule(id); load(); }
    finally { setBusy(""); }
  };

  const remove = async (id, name) => {
    if (!confirm(`Delete schedule "${name}"?`)) return;
    setBusy(`d-${id}`);
    try { await api.deleteSchedule(id); load(); }
    finally { setBusy(""); }
  };

  const inputStyle = {
    background: "var(--surface2)", border: "1px solid var(--border)",
    borderRadius: 8, padding: "8px 12px", color: "var(--text)",
    fontSize: 13, outline: "none",
  };

  return (
    <>
      {error && <div className="error-banner">{error}</div>}

      <div className="section-label">Create schedule</div>
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)",
                    borderRadius: 12, padding: 18, marginBottom: 24,
                    display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div style={{ flex: 2, minWidth: 160 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 6,
                        textTransform: "uppercase", fontWeight: 600 }}>Name</div>
          <input style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
                 placeholder="e.g. Morning pipeline"
                 value={form.name}
                 onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>
        <div style={{ flex: 1, minWidth: 140 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 6,
                        textTransform: "uppercase", fontWeight: 600 }}>Agent</div>
          <select style={{ ...inputStyle, width: "100%" }}
                  value={form.task_name}
                  onChange={e => setForm(f => ({ ...f, task_name: e.target.value }))}>
            {AGENTS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 130 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 6,
                        textTransform: "uppercase", fontWeight: 600 }}>Cron</div>
          <input style={{ ...inputStyle, width: "100%", fontFamily: "monospace",
                          boxSizing: "border-box" }}
                 value={form.cron}
                 onChange={e => setForm(f => ({ ...f, cron: e.target.value }))} />
        </div>
        <button onClick={create} disabled={busy === "create" || !form.name.trim()}
          style={{ background: "var(--accent)", color: "#fff", border: "none",
                   borderRadius: 8, padding: "9px 18px", fontSize: 13,
                   fontWeight: 600, cursor: "pointer" }}>
          {busy === "create" ? "…" : "+ Add"}
        </button>
        <div style={{ width: "100%", display: "flex", gap: 6, flexWrap: "wrap" }}>
          {PRESETS.map(p => (
            <button key={p.cron}
              onClick={() => setForm(f => ({ ...f, cron: p.cron }))}
              style={{ background: form.cron === p.cron ? "rgba(79,142,247,.15)" : "var(--surface2)",
                       border: `1px solid ${form.cron === p.cron ? "var(--accent)" : "var(--border)"}`,
                       color: form.cron === p.cron ? "var(--accent)" : "var(--muted)",
                       borderRadius: 999, padding: "4px 12px", fontSize: 11,
                       cursor: "pointer" }}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="section-label">Active schedules</div>
      <div className="table-card">
        {schedules.length === 0 ? (
          <div className="empty">
            No DB schedules yet. (The built-in beat schedule — 5:30 trends, 6:00 pipeline,
            hourly analytics — still runs regardless.)
          </div>
        ) : (
          <table>
            <thead><tr>
              <th>Name</th><th>Agent</th><th>Cron</th><th>Last run</th>
              <th>Status</th><th style={{ textAlign: "right" }}>Actions</th>
            </tr></thead>
            <tbody>
              {schedules.map(s => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 500 }}>{s.name}</td>
                  <td className="muted">{s.task_name}</td>
                  <td style={{ fontFamily: "monospace", fontSize: 12 }}>{s.cron}</td>
                  <td className="muted" style={{ fontSize: 12 }}>
                    {s.last_run_at ? new Date(s.last_run_at).toLocaleString() : "never"}
                  </td>
                  <td>
                    <span className={`badge ${s.enabled ? "ok" : "neutral"}`}>
                      {s.enabled ? "enabled" : "paused"}
                    </span>
                  </td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <button onClick={() => toggle(s.id)} disabled={busy !== ""}
                      style={{ background: "none", border: "1px solid var(--border)",
                               color: "var(--muted)", borderRadius: 6,
                               padding: "4px 10px", fontSize: 12, cursor: "pointer",
                               marginRight: 6 }}>
                      {s.enabled ? "Pause" : "Resume"}
                    </button>
                    <button onClick={() => remove(s.id, s.name)} disabled={busy !== ""}
                      style={{ background: "none", border: "1px solid rgba(242,84,74,.4)",
                               color: "var(--err)", borderRadius: 6,
                               padding: "4px 10px", fontSize: 12, cursor: "pointer" }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
