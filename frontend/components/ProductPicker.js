"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

const TYPES = [
  {
    id:    "pdf_planner",
    label: "PDF Planner",
    icon:  "📄",
    desc:  "Printable planner with sections, ruled lines, and a cover page. Great for budgets, habits, journals.",
  },
  {
    id:    "excel_template",
    label: "Excel Template",
    icon:  "📊",
    desc:  "Formatted .xlsx with styled headers, alternating rows, and sample data. Great for trackers and calculators.",
  },
  {
    id:    "notion_template",
    label: "Notion Template",
    icon:  "📝",
    desc:  "Rich Markdown + companion Notion JSON. Great for dashboards, wikis, and productivity systems.",
  },
];

const NICHES = [
  "Finance & Budgeting",
  "Health & Fitness",
  "Productivity",
  "Business & Freelance",
  "Wedding & Events",
  "Student & Education",
  "Travel",
  "Meal Planning",
  "Real Estate",
  "Content Creator",
];

export default function ProductPicker({ onClose, onLaunched }) {
  const [step,        setStep]        = useState("type");   // type | details | running | done
  const [productType, setProductType] = useState(null);
  const [mode,        setMode]        = useState("auto");   // auto | manual
  const [title,       setTitle]       = useState("");
  const [niche,       setNiche]       = useState("");
  const [customNiche, setCustomNiche] = useState("");
  const [price,       setPrice]       = useState("");
  const [result,      setResult]      = useState(null);
  const [error,       setError]       = useState("");

  const resolvedNiche = niche === "__custom__" ? customNiche : niche;

  const launch = async () => {
    setStep("running");
    setError("");
    try {
      const payload = {
        product_type: productType,
        skip_trends:  mode === "manual",
        ...(resolvedNiche && { niche: resolvedNiche }),
        ...(title.trim() && { title: title.trim() }),
        ...(price && !isNaN(parseFloat(price)) && { price: parseFloat(price) }),
      };

      const resp = await fetch(`${API}/agents/orchestrator/run`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });
      const data = await resp.json();
      setResult(data);
      setStep("done");
      if (onLaunched) onLaunched();
    } catch (err) {
      setError(String(err));
      setStep("details");
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "rgba(0,0,0,0.6)",
      zIndex: 200,
      display: "flex", alignItems: "center", justifyContent: "center",
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>

      <div style={{
        width: "min(560px, 94vw)",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 16,
        overflow: "hidden",
        animation: "fadeUp .18s ease",
      }}>

        {/* header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "18px 24px",
          borderBottom: "1px solid var(--border)",
        }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>New product</div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
              {step === "type"    && "Choose a product type"}
              {step === "details" && "Configure options"}
              {step === "running" && "Running pipeline…"}
              {step === "done"    && "Pipeline complete"}
            </div>
          </div>
          <button onClick={onClose} style={{
            background: "none", border: "none", color: "var(--muted)",
            fontSize: 20, cursor: "pointer", lineHeight: 1, padding: "0 4px",
          }}>✕</button>
        </div>

        <div style={{ padding: "20px 24px 24px" }}>

          {/* ── Step 1: type picker ── */}
          {step === "type" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {TYPES.map(t => (
                <button
                  key={t.id}
                  onClick={() => { setProductType(t.id); setStep("details"); }}
                  style={{
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    padding: "14px 16px",
                    cursor: "pointer",
                    display: "flex", alignItems: "flex-start", gap: 14,
                    textAlign: "left",
                    transition: "border-color .15s, background .15s",
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = "var(--accent)";
                    e.currentTarget.style.background  = "rgba(79,142,247,.07)";
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = "var(--border)";
                    e.currentTarget.style.background  = "var(--surface2)";
                  }}
                >
                  <span style={{ fontSize: 28, lineHeight: 1, flexShrink: 0 }}>{t.icon}</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text)", marginBottom: 4 }}>
                      {t.label}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5 }}>
                      {t.desc}
                    </div>
                  </div>
                  <span style={{ color: "var(--muted)", fontSize: 18, marginLeft: "auto", alignSelf: "center" }}>›</span>
                </button>
              ))}
            </div>
          )}

          {/* ── Step 2: details ── */}
          {step === "details" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {/* selected type badge */}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 20 }}>{TYPES.find(t => t.id === productType)?.icon}</span>
                <span style={{ fontWeight: 600 }}>{TYPES.find(t => t.id === productType)?.label}</span>
                <button
                  onClick={() => setStep("type")}
                  style={{
                    background: "none", border: "none",
                    color: "var(--accent)", fontSize: 12,
                    cursor: "pointer", marginLeft: 4,
                  }}
                >
                  Change
                </button>
              </div>

              {/* mode toggle */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)",
                              textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                  Generation mode
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {[
                    { id: "auto",   label: "Auto",   sub: "AI picks niche and title from trends" },
                    { id: "manual", label: "Manual",  sub: "You set the niche and title" },
                  ].map(m => (
                    <button
                      key={m.id}
                      onClick={() => setMode(m.id)}
                      style={{
                        flex: 1,
                        background: mode === m.id ? "rgba(79,142,247,.12)" : "var(--surface2)",
                        border: `1px solid ${mode === m.id ? "var(--accent)" : "var(--border)"}`,
                        borderRadius: 10, padding: "10px 12px",
                        cursor: "pointer", textAlign: "left",
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: 13,
                                    color: mode === m.id ? "var(--accent)" : "var(--text)" }}>
                        {m.label}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}>{m.sub}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* niche selector */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)",
                                textTransform: "uppercase", letterSpacing: "0.06em",
                                display: "block", marginBottom: 8 }}>
                  Niche {mode === "auto" && <span style={{ fontWeight: 400 }}>(optional override)</span>}
                </label>
                <select
                  value={niche}
                  onChange={e => setNiche(e.target.value)}
                  style={{
                    width: "100%", background: "var(--surface2)",
                    border: "1px solid var(--border)", borderRadius: 8,
                    padding: "9px 12px", color: "var(--text)", fontSize: 13,
                    outline: "none",
                  }}
                >
                  <option value="">— Let AI decide —</option>
                  {NICHES.map(n => <option key={n} value={n}>{n}</option>)}
                  <option value="__custom__">Custom…</option>
                </select>
                {niche === "__custom__" && (
                  <input
                    placeholder="Enter niche…"
                    value={customNiche}
                    onChange={e => setCustomNiche(e.target.value)}
                    style={{
                      marginTop: 8, width: "100%",
                      background: "var(--surface2)",
                      border: "1px solid var(--border)", borderRadius: 8,
                      padding: "9px 12px", color: "var(--text)", fontSize: 13,
                      outline: "none", boxSizing: "border-box",
                    }}
                  />
                )}
              </div>

              {/* title (manual only) */}
              {mode === "manual" && (
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)",
                                  textTransform: "uppercase", letterSpacing: "0.06em",
                                  display: "block", marginBottom: 8 }}>
                    Product title
                  </label>
                  <input
                    placeholder="e.g. 2026 Monthly Budget Planner"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    style={{
                      width: "100%", background: "var(--surface2)",
                      border: "1px solid var(--border)", borderRadius: 8,
                      padding: "9px 12px", color: "var(--text)", fontSize: 13,
                      outline: "none", boxSizing: "border-box",
                    }}
                  />
                </div>
              )}

              {/* price */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)",
                                textTransform: "uppercase", letterSpacing: "0.06em",
                                display: "block", marginBottom: 8 }}>
                  Price (USD) <span style={{ fontWeight: 400 }}>(optional, 2.99 – 14.99)</span>
                </label>
                <input
                  type="number" min="2.99" max="14.99" step="0.50"
                  placeholder="AI decides"
                  value={price}
                  onChange={e => setPrice(e.target.value)}
                  style={{
                    width: 140, background: "var(--surface2)",
                    border: "1px solid var(--border)", borderRadius: 8,
                    padding: "9px 12px", color: "var(--text)", fontSize: 13,
                    outline: "none",
                  }}
                />
              </div>

              {error && (
                <div style={{
                  background: "rgba(242,84,74,.08)",
                  border: "1px solid rgba(242,84,74,.25)",
                  borderRadius: 8, padding: "10px 14px",
                  color: "var(--err)", fontSize: 12,
                }}>
                  {error}
                </div>
              )}

              <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                <button onClick={() => setStep("type")} style={{
                  background: "none", border: "1px solid var(--border)",
                  color: "var(--muted)", borderRadius: 8,
                  padding: "10px 18px", fontSize: 13, cursor: "pointer",
                }}>
                  Back
                </button>
                <button
                  onClick={launch}
                  disabled={mode === "manual" && !title.trim()}
                  style={{
                    flex: 1,
                    background: (mode === "manual" && !title.trim()) ? "var(--surface2)" : "var(--accent)",
                    color: (mode === "manual" && !title.trim()) ? "var(--muted)" : "#fff",
                    border: "none", borderRadius: 8,
                    padding: "10px 18px", fontWeight: 600, fontSize: 13,
                    cursor: (mode === "manual" && !title.trim()) ? "not-allowed" : "pointer",
                  }}
                >
                  Generate product ↗
                </button>
              </div>
            </div>
          )}

          {/* ── Step 3: running ── */}
          {step === "running" && (
            <div style={{ textAlign: "center", padding: "32px 0" }}>
              <div style={{ fontSize: 36, marginBottom: 16, animation: "spin 1.5s linear infinite", display: "inline-block" }}>⟳</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Pipeline running…</div>
              <div style={{ fontSize: 13, color: "var(--muted)" }}>
                Trend → Strategy → Build → SEO → QA → Publish
              </div>
              <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 8 }}>
                This usually takes 30–90 seconds.
              </div>
            </div>
          )}

          {/* ── Step 4: done ── */}
          {step === "done" && result && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {result.ok ? (
                <>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 28 }}>✅</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>Product created!</div>
                      <div style={{ fontSize: 12, color: "var(--muted)" }}>
                        Product ID #{result.product_id}
                        {result.listing_id && ` · Listing ${result.listing_id}`}
                      </div>
                    </div>
                  </div>

                  {/* step summary */}
                  <div style={{ background: "var(--surface2)", borderRadius: 10, overflow: "hidden" }}>
                    {Object.entries(result.steps || {}).map(([name, s]) => (
                      <div key={name} style={{
                        display: "flex", alignItems: "center", gap: 10,
                        padding: "8px 14px",
                        borderBottom: "1px solid var(--border)",
                        fontSize: 13,
                      }}>
                        <span style={{ color: s.ok !== false ? "var(--ok)" : "var(--err)", fontWeight: 700 }}>
                          {s.ok !== false ? "✓" : "✕"}
                        </span>
                        <span style={{ textTransform: "capitalize", fontWeight: 500 }}>{name}</span>
                        {s.error && (
                          <span style={{ fontSize: 11, color: "var(--err)", marginLeft: "auto" }}>{s.error}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 28 }}>❌</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>Pipeline failed</div>
                      <div style={{ fontSize: 12, color: "var(--err)" }}>
                        Failed at: {result.failed_step || "unknown step"}
                      </div>
                    </div>
                  </div>
                  {result.error && (
                    <div style={{
                      background: "rgba(242,84,74,.08)", border: "1px solid rgba(242,84,74,.25)",
                      borderRadius: 8, padding: "10px 14px",
                      color: "var(--err)", fontSize: 12, fontFamily: "ui-monospace, monospace",
                    }}>
                      {result.error}
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={onClose}
                style={{
                  background: "var(--accent)", color: "#fff",
                  border: "none", borderRadius: 8,
                  padding: "10px 18px", fontWeight: 600, fontSize: 13,
                  cursor: "pointer", marginTop: 4,
                }}
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeUp {
          from { transform: translateY(16px); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
