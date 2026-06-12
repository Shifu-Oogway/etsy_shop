"use client";

import { useState } from "react";
import { api } from "../lib/api";

export default function TrendsPage({ trends, onRefresh }) {
  const [busy, setBusy] = useState("");
  const [buildResult, setBuildResult] = useState(null);

  const discover = async () => {
    setBusy("discover");
    try { await api.discoverTrends(8); onRefresh(); }
    catch (e) { alert(String(e)); }
    finally { setBusy(""); }
  };

  const build = async (trend) => {
    setBusy(`build-${trend.id}`);
    setBuildResult(null);
    try {
      const res = await api.buildFromTrend(trend.id);
      setBuildResult({ trend: trend.keyword, ...res });
      onRefresh();
    } catch (e) { setBuildResult({ trend: trend.keyword, ok: false, error: String(e) }); }
    finally { setBusy(""); }
  };

  const scoreColor = (s) =>
    s >= 0.7 ? "var(--ok)" : s >= 0.4 ? "var(--warn)" : "var(--muted)";

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
        <div className="section-label" style={{ marginBottom: 0 }}>Market trends</div>
        <button onClick={discover} disabled={busy !== ""}
          style={{ marginLeft: "auto", background: "var(--accent)", color: "#fff",
                   border: "none", borderRadius: 8, padding: "8px 16px",
                   fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
          {busy === "discover" ? "⟳ Scanning…" : "🔍 Discover trends"}
        </button>
      </div>

      {buildResult && (
        <div style={{
          padding: "10px 16px", borderRadius: 8, marginBottom: 14, fontSize: 13,
          background: buildResult.ok ? "rgba(62,207,142,.08)" : "rgba(242,84,74,.08)",
          border: `1px solid ${buildResult.ok ? "rgba(62,207,142,.3)" : "rgba(242,84,74,.3)"}`,
          color: buildResult.ok ? "var(--ok)" : "var(--err)",
        }}>
          {buildResult.ok
            ? `✓ Product built from "${buildResult.trend}" — product #${buildResult.product_id}`
            : `✕ Build from "${buildResult.trend}" failed: ${buildResult.error || buildResult.failed_step}`}
        </div>
      )}

      <div className="table-card">
        {trends.length === 0 ? (
          <div className="empty">No trends yet — hit "Discover trends" to scan real Etsy + Google search data.</div>
        ) : (
          <table>
            <thead><tr>
              <th>Keyword</th><th>Niche</th><th>Score</th><th>Source</th>
              <th>Rationale</th><th></th>
            </tr></thead>
            <tbody>
              {trends.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 500 }}>{t.keyword}</td>
                  <td className="muted">{t.niche}</td>
                  <td>
                    <span style={{ color: scoreColor(t.score), fontWeight: 700 }}>
                      {(t.score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${t.details?.source === "market_data" ? "ok" : "neutral"}`}>
                      {t.details?.source === "market_data" ? "real data" : "AI only"}
                    </span>
                  </td>
                  <td className="muted" style={{ fontSize: 12, maxWidth: 300 }}>
                    {t.details?.rationale?.slice(0, 90)}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button onClick={() => build(t)} disabled={busy !== ""}
                      style={{ background: "none", border: "1px solid var(--accent)",
                               color: "var(--accent)", borderRadius: 6,
                               padding: "5px 12px", fontSize: 12, fontWeight: 600,
                               cursor: "pointer", whiteSpace: "nowrap" }}>
                      {busy === `build-${t.id}` ? "Building…" : "▶ Build product"}
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
