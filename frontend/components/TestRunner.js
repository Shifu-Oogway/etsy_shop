"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

const FILE_LABELS = {
  "tests/test_imports.py":  "Imports",
  "tests/test_models.py":   "Models",
  "tests/test_services.py": "Services",
  "tests/test_agents.py":   "Agents",
  "tests/test_api.py":      "API",
};

const STATUS_STYLE = {
  passed:  { color: "var(--ok)",   icon: "✓" },
  failed:  { color: "var(--err)",  icon: "✕" },
  error:   { color: "var(--err)",  icon: "!" },
  running: { color: "var(--warn)", icon: "…" },
  pending: { color: "var(--muted)",icon: "·" },
};

function statusStyle(s) {
  return STATUS_STYLE[s] || STATUS_STYLE.pending;
}

function groupByFile(results) {
  const groups = {};
  for (const r of results) {
    const key = r.file || "other";
    if (!groups[key]) groups[key] = [];
    groups[key].push(r);
  }
  return groups;
}

function SummaryBar({ summary, running }) {
  if (!summary && !running) return null;
  const total    = summary?.total    ?? 0;
  const passed   = summary?.passed   ?? 0;
  const failed   = summary?.failed   ?? 0;
  const errors   = summary?.errors   ?? 0;
  const duration = summary?.duration ?? 0;
  const pct      = total ? Math.round((passed / total) * 100) : 0;

  return (
    <div style={{
      display: "flex", gap: 20, alignItems: "center",
      padding: "12px 20px",
      background: "var(--surface2)",
      borderBottom: "1px solid var(--border)",
      flexShrink: 0,
    }}>
      {running ? (
        <span style={{ color: "var(--warn)", fontWeight: 600, fontSize: 13 }}>
          ⟳ Running tests…
        </span>
      ) : (
        <>
          <span style={{ color: failed || errors ? "var(--err)" : "var(--ok)", fontWeight: 700, fontSize: 15 }}>
            {failed || errors ? "✕ Tests failed" : "✓ All tests passed"}
          </span>
          <span style={{ color: "var(--ok)", fontSize: 13 }}>{passed} passed</span>
          {(failed + errors) > 0 && (
            <span style={{ color: "var(--err)", fontSize: 13 }}>{failed + errors} failed</span>
          )}
          <span style={{ color: "var(--muted)", fontSize: 13 }}>{total} total</span>
          <span style={{ color: "var(--muted)", fontSize: 12, marginLeft: "auto" }}>
            {duration}s
          </span>
        </>
      )}

      {/* progress bar */}
      {(running || summary) && (
        <div style={{
          position: "absolute", bottom: 0, left: 0,
          height: 2, width: running ? "60%" : `${pct}%`,
          background: failed || errors ? "var(--err)" : "var(--ok)",
          transition: "width 0.4s ease",
        }} />
      )}
    </div>
  );
}

export default function TestRunner() {
  const [tests,    setTests]    = useState([]);      // collected test IDs
  const [results,  setResults]  = useState({});      // nodeid -> result obj
  const [summary,  setSummary]  = useState(null);
  const [running,  setRunning]  = useState(false);
  const [filter,   setFilter]   = useState("all");   // all | passed | failed
  const [expanded, setExpanded] = useState({});      // file -> bool
  const [output,   setOutput]   = useState("");
  const [showOutput, setShowOutput] = useState(false);
  const abortRef = useRef(null);

  // Load test list on mount
  useEffect(() => {
    fetch(`${API}/tests`)
      .then(r => r.json())
      .then(d => {
        setTests(d.tests || []);
        // Pre-expand all files
        const exp = {};
        for (const t of (d.tests || [])) { exp[t.file] = true; }
        setExpanded(exp);
      })
      .catch(() => {});
  }, []);

  const run = useCallback(async (file = null) => {
    if (running) return;
    setRunning(true);
    setSummary(null);
    setOutput("");

    // Mark all relevant tests as running
    setResults(prev => {
      const next = { ...prev };
      for (const t of tests) {
        if (!file || t.file === file) {
          next[t.id] = { ...t, status: "running", message: "", duration: 0 };
        }
      }
      return next;
    });

    try {
      const url = file
        ? `${API}/tests/run?file=${encodeURIComponent(file.replace("tests/", ""))}`
        : `${API}/tests/run`;

      const resp = await fetch(url, { method: "POST" });
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const msg = JSON.parse(line);
            if (msg.type === "result") {
              setResults(prev => ({ ...prev, [msg.id]: msg }));
            } else if (msg.type === "summary") {
              setSummary(msg);
              setOutput(msg.output || "");
            }
          } catch {}
        }
      }
    } catch (err) {
      setSummary({ passed: 0, failed: 0, errors: 1, total: 0,
                   duration: 0, output: String(err) });
    } finally {
      setRunning(false);
    }
  }, [running, tests]);

  const groups = groupByFile(
    tests.map(t => results[t.id] || { ...t, status: "pending" })
  );

  const filterFn = (r) => {
    if (filter === "all") return true;
    if (filter === "failed") return r.status === "failed" || r.status === "error";
    return r.status === filter;
  };

  const toggle = (file) =>
    setExpanded(prev => ({ ...prev, [file]: !prev[file] }));

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "calc(100vh - 52px)",
      overflow: "hidden",
      position: "relative",
    }}>

      {/* toolbar */}
      <div style={{
        display: "flex", gap: 10, alignItems: "center",
        padding: "12px 20px",
        borderBottom: "1px solid var(--border)",
        background: "var(--surface)",
        flexShrink: 0,
      }}>
        <button
          onClick={() => run()}
          disabled={running}
          style={{
            background: running ? "var(--surface2)" : "var(--accent)",
            color: running ? "var(--muted)" : "#fff",
            border: "none", borderRadius: 8,
            padding: "8px 18px", fontWeight: 600, fontSize: 13,
            cursor: running ? "wait" : "pointer",
            display: "flex", alignItems: "center", gap: 6,
          }}
        >
          {running ? "⟳ Running…" : "▶ Run all tests"}
        </button>

        {/* filter tabs */}
        <div style={{ display: "flex", gap: 2, marginLeft: 8 }}>
          {["all", "passed", "failed"].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              background: filter === f ? "var(--surface2)" : "transparent",
              border: "1px solid " + (filter === f ? "var(--border)" : "transparent"),
              color: filter === f ? "var(--text)" : "var(--muted)",
              borderRadius: 6, padding: "5px 12px", fontSize: 12,
              fontWeight: 500, cursor: "pointer",
            }}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "var(--muted)" }}>
            {tests.length} tests collected
          </span>
          {output && (
            <button onClick={() => setShowOutput(v => !v)} style={{
              background: "transparent", border: "1px solid var(--border)",
              color: "var(--muted)", borderRadius: 6,
              padding: "5px 10px", fontSize: 12, cursor: "pointer",
            }}>
              {showOutput ? "Hide output" : "Show output"}
            </button>
          )}
        </div>
      </div>

      {/* summary bar */}
      <div style={{ position: "relative" }}>
        <SummaryBar summary={summary} running={running} />
      </div>

      {/* body */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex" }}>

        {/* test list */}
        <div style={{
          flex: 1, overflowY: "auto",
          padding: "8px 0",
        }}>
          {Object.entries(groups).map(([file, fileTests]) => {
            const visible = fileTests.filter(filterFn);
            if (visible.length === 0 && filter !== "all") return null;

            const filePassed  = fileTests.filter(t => t.status === "passed").length;
            const fileFailed  = fileTests.filter(t => t.status === "failed" || t.status === "error").length;
            const fileRunning = fileTests.some(t => t.status === "running");
            const fileLabel   = FILE_LABELS[file] || file;

            return (
              <div key={file}>
                {/* file header */}
                <div
                  onClick={() => toggle(file)}
                  style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "8px 20px", cursor: "pointer",
                    borderBottom: "1px solid var(--border)",
                    background: "var(--surface)",
                    userSelect: "none",
                  }}
                >
                  <span style={{ color: "var(--muted)", fontSize: 12, width: 10 }}>
                    {expanded[file] ? "▾" : "▸"}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{fileLabel}</span>
                  <span style={{ fontSize: 11, color: "var(--muted)" }}>{file}</span>

                  <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
                    {fileRunning && (
                      <span style={{ color: "var(--warn)", fontSize: 12 }}>running</span>
                    )}
                    {filePassed > 0 && (
                      <span style={{ color: "var(--ok)", fontSize: 12 }}>{filePassed} ✓</span>
                    )}
                    {fileFailed > 0 && (
                      <span style={{ color: "var(--err)", fontSize: 12 }}>{fileFailed} ✕</span>
                    )}
                    <span style={{ color: "var(--muted)", fontSize: 12 }}>{fileTests.length} tests</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); run(file); }}
                      disabled={running}
                      style={{
                        background: "transparent",
                        border: "1px solid var(--border)",
                        color: "var(--muted)", borderRadius: 5,
                        padding: "2px 8px", fontSize: 11,
                        cursor: running ? "wait" : "pointer",
                      }}
                    >
                      Run
                    </button>
                  </div>
                </div>

                {/* test rows */}
                {expanded[file] && visible.map(t => {
                  const st = statusStyle(t.status);
                  return (
                    <div key={t.id}>
                      <div style={{
                        display: "flex", alignItems: "center", gap: 10,
                        padding: "7px 20px 7px 36px",
                        borderBottom: "1px solid var(--border)",
                        background: t.status === "failed" || t.status === "error"
                          ? "rgba(242,84,74,0.04)" : "transparent",
                      }}>
                        <span style={{ color: st.color, fontWeight: 700, width: 14, flexShrink: 0 }}>
                          {st.icon}
                        </span>
                        <span style={{
                          fontSize: 13, flex: 1,
                          color: t.status === "pending" ? "var(--muted)" : "var(--text)",
                          fontFamily: "ui-monospace, monospace",
                        }}>
                          {t.name}
                        </span>
                        {t.duration > 0 && (
                          <span style={{ fontSize: 11, color: "var(--muted)", flexShrink: 0 }}>
                            {t.duration}s
                          </span>
                        )}
                      </div>
                      {/* error message */}
                      {t.message && (t.status === "failed" || t.status === "error") && (
                        <div style={{
                          padding: "8px 20px 8px 50px",
                          background: "rgba(242,84,74,0.06)",
                          borderBottom: "1px solid var(--border)",
                          fontFamily: "ui-monospace, monospace",
                          fontSize: 12, color: "var(--err)",
                          whiteSpace: "pre-wrap", lineHeight: 1.5,
                        }}>
                          {t.message}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}

          {tests.length === 0 && (
            <div style={{ padding: 40, textAlign: "center", color: "var(--muted)", fontSize: 13 }}>
              Could not reach test runner — is the API container running?
            </div>
          )}
        </div>

        {/* raw output panel */}
        {showOutput && (
          <div style={{
            width: 420, borderLeft: "1px solid var(--border)",
            background: "var(--bg)", overflowY: "auto",
            padding: 16, flexShrink: 0,
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)",
                          textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>
              Raw output
            </div>
            <pre style={{
              fontSize: 11, color: "var(--muted)", whiteSpace: "pre-wrap",
              lineHeight: 1.6, fontFamily: "ui-monospace, monospace",
            }}>
              {output || "No output yet."}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
