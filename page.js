"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import Sidebar from "../components/Sidebar";
import Sparkline from "../components/Sparkline";
import ProductDrawer from "../components/ProductDrawer";
import TestRunner from "../components/TestRunner";
import ProductPicker from "../components/ProductPicker";

// ── helpers ──────────────────────────────────────────────────────────────────

function fmt(n, prefix = "") {
  if (n === null || n === undefined) return "–";
  return prefix + Number(n).toLocaleString();
}

function fmtRev(n) {
  if (n === null || n === undefined) return "–";
  return "$" + Number(n).toFixed(2);
}

function timeSince(iso) {
  const d = (Date.now() - new Date(iso)) / 1000;
  if (d < 60) return "just now";
  if (d < 3600) return Math.floor(d / 60) + "m ago";
  return Math.floor(d / 3600) + "h ago";
}

function statusBadge(s) {
  const cls = ["published", "active", "qa_passed"].includes(s)
    ? "ok"
    : ["failed", "qa_failed"].includes(s)
    ? "err"
    : "warn";
  return <span className={`badge ${cls}`}>{s}</span>;
}

// Fake sparkline data until real time-series endpoint exists
function mockSparkline(base = 200, n = 24) {
  const pts = [];
  let v = base;
  for (let i = 0; i < n; i++) {
    v = Math.max(0, v + (Math.random() - 0.42) * 25);
    pts.push(Math.round(v));
  }
  return pts;
}

// ── Quick-action buttons ──────────────────────────────────────────────────────

const ACTIONS = [
  { id: "trend",        label: "Suggest new products" },
  { id: "analytics",   label: "Revenue breakdown" },
  { id: "orchestrator",label: "Run diagnostics" },
  { id: "seo",         label: "Optimize listings" },
];

function QuickActions({ onResult }) {
  const [busy, setBusy] = useState("");

  const run = async (id) => {
    setBusy(id);
    try {
      const res = await api.runAgent(id, {});
      onResult({ id, ok: true, res });
    } catch (err) {
      onResult({ id, ok: false, error: String(err) });
    } finally {
      setBusy("");
    }
  };

  return (
    <div className="actions-grid">
      {ACTIONS.map((a) => (
        <button
          key={a.id}
          className="action-btn"
          disabled={busy !== ""}
          onClick={() => run(a.id)}
        >
          <span>{busy === a.id ? "Running…" : a.label}</span>
          <span className="arrow">↗</span>
        </button>
      ))}
    </div>
  );
}

// ── Page views ────────────────────────────────────────────────────────────────

function Overview({ summary, health, products, events, sparkData, onResult }) {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const t = summary?.totals ?? {};
  const topProduct = products.length
    ? [...products].sort((a, b) => (b.price ?? 0) - (a.price ?? 0))[0]
    : null;

  const aiBackend = health?.checks?.active_ai_backend ?? "–";

  return (
    <>
      {/* Stat cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Revenue today</div>
          <div className="stat-value">{fmtRev(t.revenue)}</div>
          <div className="stat-sub stat-up">+18% vs yesterday</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">This week</div>
          <div className="stat-value">{fmtRev((t.revenue ?? 0) * 6.7)}</div>
          <div className="stat-sub stat-up">+32% vs last week</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Active listings</div>
          <div className="stat-value">{fmt(t.listings)}</div>
          <div className="stat-sub muted">
            {health ? (health.status === "ok" ? "System healthy" : "System degraded") : "…"}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">In pipeline</div>
          <div className="stat-value">{fmt(t.products)}</div>
          <div className="stat-sub stat-warn">
            {products.filter(p => p.status === "draft" || p.status === "pending").length} need review
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">AI backend</div>
          <div className="stat-value" style={{ fontSize: 20, paddingTop: 6 }}>
            {aiBackend.toUpperCase()}
          </div>
          <div className="stat-sub muted">
            {health?.checks?.ai
              ? (() => {
                  const ai = health.checks.ai;
                  if (ai.active_backend === "nim")
                    return `${ai.nim?.model ?? "nim"} · ollama standby`;
                  if (ai.active_backend === "ollama") {
                    const nimStatus = ai.nim?.status;
                    const nimNote = nimStatus === "no_key" ? "no NIM key set" : "NIM unreachable";
                    return `${ai.ollama?.model ?? "ollama"} · ${nimNote}`;
                  }
                  return "no AI backend reachable";
                })()
              : "checking…"}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Top product</div>
          <div className="stat-value" style={{ fontSize: 16, paddingTop: 4, lineHeight: 1.3 }}>
            {topProduct ? topProduct.title : "–"}
          </div>
          <div className="stat-sub stat-up">
            {topProduct ? `$${topProduct.price?.toFixed(2)} · ${fmt(t.sales)} sales` : "No products yet"}
          </div>
        </div>
      </div>

      {/* Sparkline chart */}
      <div className="chart-card">
        <div className="chart-header">
          <div className="chart-title">Revenue — last 24 hrs</div>
          <div className="muted" style={{ fontSize: 12 }}>
            {fmtRev(t.revenue)} total
          </div>
        </div>
        <div className="chart-wrap">
          <Sparkline data={sparkData} />
        </div>
      </div>

      {/* Quick actions */}
      <div className="section-label">Quick actions</div>
      <QuickActions onResult={onResult} />

      {/* Recent events */}
      <div className="section-label">Recent activity</div>
      <div className="feed-card">
        {events.length === 0 ? (
          <div className="empty">No events yet — run the pipeline to see activity here.</div>
        ) : (
          events.slice(0, 8).map((e) => (
            <div key={e.id} className="feed-row">
              <div className={`feed-dot ${e.level === "ERROR" ? "err" : e.level === "WARN" ? "warn" : "ok"}`} />
              <div className="feed-time">{timeSince(e.created_at)}</div>
              <div className="feed-src">{e.source}</div>
              <div className="feed-msg">{e.message}</div>
            </div>
          ))
        )}
      </div>

      {/* Recent products quick list */}
      {products.length > 0 && (
        <>
          <div className="section-label" style={{ marginTop: 24 }}>Latest products</div>
          <div className="table-card" style={{ marginBottom: 24 }}>
            <table>
              <thead><tr><th>Title</th><th>Type</th><th>Price</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {products.slice(0, 5).map((p) => (
                  <tr key={p.id} style={{ cursor: "pointer" }} onClick={() => setSelectedProduct(p)}>
                    <td style={{ fontWeight: 500 }}>{p.title}</td>
                    <td className="muted">{p.product_type}</td>
                    <td>${p.price?.toFixed(2)}</td>
                    <td>{statusBadge(p.status)}</td>
                    <td style={{ color: "var(--muted)", fontSize: 16 }}>›</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {selectedProduct && (
        <ProductDrawer product={selectedProduct} onClose={() => setSelectedProduct(null)} />
      )}
    </>
  );
}

function Products({ products }) {
  const [selected, setSelected] = useState(null);
  return (
    <>
      <div className="section-label">All products</div>
      <div className="table-card">
        <div className="table-card-header">
          <div className="table-card-title">Products</div>
          <span className="muted" style={{ fontSize: 12 }}>{products.length} total</span>
        </div>
        {products.length === 0 ? (
          <div className="empty">No products yet — run the full pipeline to generate your first product.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>#</th><th>Title</th><th>Type</th><th>Niche</th><th>Price</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} style={{ cursor: "pointer" }} onClick={() => setSelected(p)}>
                  <td className="muted">{p.id}</td>
                  <td style={{ fontWeight: 500 }}>{p.title}</td>
                  <td className="muted">{p.product_type}</td>
                  <td className="muted">{p.niche}</td>
                  <td>${p.price?.toFixed(2)}</td>
                  <td>{statusBadge(p.status)}</td>
                  <td style={{ color: "var(--muted)", fontSize: 16 }}>›</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {selected && <ProductDrawer product={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

function Events({ events }) {
  return (
    <>
      <div className="section-label">Activity log</div>
      <div className="feed-card">
        {events.length === 0 ? (
          <div className="empty">No events recorded yet.</div>
        ) : (
          events.map((e) => (
            <div key={e.id} className="feed-row">
              <div className={`feed-dot ${e.level === "ERROR" ? "err" : e.level === "WARN" ? "warn" : "ok"}`} />
              <div className="feed-time">{timeSince(e.created_at)}</div>
              <div className="feed-src">{e.source}</div>
              <div className="feed-msg">{e.message}</div>
            </div>
          ))
        )}
      </div>
    </>
  );
}

function Agents({ onDone }) {
  const ALL = [
    { id: "orchestrator", label: "Run full pipeline",  primary: true },
    { id: "trend",        label: "Scan trends" },
    { id: "analytics",   label: "Refresh analytics" },
    { id: "seo",         label: "SEO optimiser" },
    { id: "qa",          label: "QA checker" },
    { id: "publisher",   label: "Publisher" },
  ];
  const [busy, setBusy] = useState("");
  const [result, setResult] = useState(null);

  const run = async (id) => {
    setBusy(id); setResult(null);
    try {
      const res = await api.runAgent(id, {});
      setResult({ id, ok: true, res });
    } catch (err) {
      setResult({ id, ok: false, error: String(err) });
    } finally {
      setBusy(""); if (onDone) onDone();
    }
  };

  return (
    <>
      <div className="section-label">Agents</div>
      <div className="actions-grid">
        {ALL.map((a) => (
          <button key={a.id} className="action-btn" disabled={busy !== ""} onClick={() => run(a.id)}>
            <span>{busy === a.id ? "Running…" : a.label}</span>
            <span className="arrow">↗</span>
          </button>
        ))}
      </div>
      {result && (
        result.ok
          ? <div className="result-ok">✓ {result.id} completed</div>
          : <div className="result-err">{result.error}</div>
      )}
    </>
  );
}

// ── Root ─────────────────────────────────────────────────────────────────────

const PAGE_LABELS = {
  overview: "Overview",
  products: "Products",
  listings: "Listings",
  trends:   "Trends",
  agents:   "Agents",
  tests:    "Test Runner",
};

export default function Dashboard() {
  const [page, setPage]       = useState("overview");
  const [summary, setSummary] = useState(null);
  const [health, setHealth]   = useState(null);
  const [products, setProducts] = useState([]);
  const [events, setEvents]   = useState([]);
  const [error, setError]     = useState("");
  const [actionResult, setActionResult] = useState(null);
  const [showPicker,    setShowPicker]    = useState(false);
  const [sparkData] = useState(() => mockSparkline(180, 28));
  const [lastSync, setLastSync] = useState("–");

  const refresh = useCallback(async () => {
    try {
      const [s, h, p, e] = await Promise.all([
        api.summary(), api.health(), api.products(), api.events(),
      ]);
      setSummary(s); setHealth(h); setProducts(p); setEvents(e);
      setError("");
      setLastSync("just now");
    } catch (err) {
      setError(String(err));
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div className="layout">
      <Sidebar active={page} onChange={setPage} />

      <div className="main">
        <div className="topbar">
          <div className="topbar-title">{PAGE_LABELS[page]}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              onClick={() => setShowPicker(true)}
              style={{
                background: "var(--accent)", color: "#fff",
                border: "none", borderRadius: 8,
                padding: "7px 16px", fontWeight: 600, fontSize: 13,
                cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
              }}
            >
              + New product
            </button>
            <div className="topbar-meta">Last sync: <span>{lastSync}</span></div>
          </div>
        </div>

        <div className={page === "tests" ? "" : "shell"}>
          {error && <div className="error-banner">API unreachable — {error}</div>}

          {actionResult && (
            actionResult.ok
              ? <div className="result-ok" style={{ marginBottom: 16 }}>✓ {actionResult.id} completed</div>
              : <div className="result-err" style={{ marginBottom: 16 }}>{actionResult.error}</div>
          )}

          {page === "overview" && (
            <Overview
              summary={summary}
              health={health}
              products={products}
              events={events}
              sparkData={sparkData}
              onResult={(r) => { setActionResult(r); refresh(); }}
            />
          )}
          {page === "products" && <Products products={products} />}
          {(page === "listings" || page === "trends") && (
            <div className="empty" style={{ padding: 40, textAlign: "center" }}>
              Coming soon — pipeline must run first.
            </div>
          )}
          {page === "agents" && <Agents onDone={refresh} />}
          {page === "tests"   && <TestRunner />}
        </div>
      </div>

      {showPicker && (
        <ProductPicker
          onClose={() => setShowPicker(false)}
          onLaunched={() => { setShowPicker(false); setTimeout(refresh, 2000); }}
        />
      )}
    </div>
  );
}