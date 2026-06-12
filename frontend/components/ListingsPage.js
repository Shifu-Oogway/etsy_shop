"use client";

import { useState } from "react";
import { api } from "../lib/api";

export default function ListingsPage({ listings, onRefresh }) {
  const [editing, setEditing] = useState(null);   // listing id being edited
  const [draft,   setDraft]   = useState({});
  const [busy,    setBusy]    = useState("");

  const totalViews = listings.reduce((s, l) => s + (l.stats?.views || 0), 0);
  const totalFavs  = listings.reduce((s, l) => s + (l.stats?.favorites || 0), 0);

  const startEdit = (l) => {
    setEditing(l.id);
    setDraft({ title: l.title, price: l.price });
  };

  const saveEdit = async (id) => {
    setBusy(`save-${id}`);
    try {
      await api.patchListing(id, { title: draft.title, price: parseFloat(draft.price) });
      setEditing(null);
      onRefresh();
    } catch (e) { alert(String(e)); }
    finally { setBusy(""); }
  };

  const refreshStats = async (id) => {
    setBusy(`stats-${id}`);
    try { await api.refreshListingStats(id); onRefresh(); }
    catch (e) { alert(String(e)); }
    finally { setBusy(""); }
  };

  const inputStyle = {
    background: "var(--surface2)", border: "1px solid var(--border)",
    borderRadius: 6, padding: "5px 9px", color: "var(--text)",
    fontSize: 13, outline: "none",
  };

  return (
    <>
      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
        <div className="stat-card">
          <div className="stat-label">Active listings</div>
          <div className="stat-value">{listings.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total views</div>
          <div className="stat-value">{totalViews.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total favorites</div>
          <div className="stat-value">{totalFavs.toLocaleString()}</div>
        </div>
      </div>

      <div className="section-label">All listings</div>
      <div className="table-card">
        {listings.length === 0 ? (
          <div className="empty">No listings yet — publish a product to create one.</div>
        ) : (
          <table>
            <thead><tr>
              <th>Title</th><th>Price</th><th>Views</th><th>Favs</th>
              <th>Status</th><th>Etsy ID</th><th style={{textAlign:"right"}}>Actions</th>
            </tr></thead>
            <tbody>
              {listings.map((l) => (
                <tr key={l.id}>
                  <td style={{ fontWeight: 500, maxWidth: 280 }}>
                    {editing === l.id ? (
                      <input style={{ ...inputStyle, width: "100%" }}
                             value={draft.title}
                             onChange={e => setDraft(d => ({ ...d, title: e.target.value }))} />
                    ) : l.title}
                  </td>
                  <td>
                    {editing === l.id ? (
                      <input style={{ ...inputStyle, width: 70 }} type="number" step="0.5"
                             value={draft.price}
                             onChange={e => setDraft(d => ({ ...d, price: e.target.value }))} />
                    ) : `$${l.price?.toFixed(2)}`}
                  </td>
                  <td>{l.stats?.views?.toLocaleString() ?? "—"}</td>
                  <td>{l.stats?.favorites?.toLocaleString() ?? "—"}</td>
                  <td><span className={`badge ${l.status === "active" ? "ok" : "warn"}`}>{l.status}</span></td>
                  <td className="muted" style={{ fontSize: 11, fontFamily: "monospace" }}>
                    {l.etsy_listing_id?.slice(0, 14)}
                  </td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    {editing === l.id ? (
                      <>
                        <button onClick={() => saveEdit(l.id)} disabled={busy !== ""}
                          style={{ background: "var(--accent)", color: "#fff", border: "none",
                                   borderRadius: 6, padding: "4px 10px", fontSize: 12,
                                   cursor: "pointer", marginRight: 6 }}>
                          {busy === `save-${l.id}` ? "…" : "Save"}
                        </button>
                        <button onClick={() => setEditing(null)}
                          style={{ background: "none", border: "1px solid var(--border)",
                                   color: "var(--muted)", borderRadius: 6,
                                   padding: "4px 10px", fontSize: 12, cursor: "pointer" }}>
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => startEdit(l)}
                          style={{ background: "none", border: "1px solid var(--border)",
                                   color: "var(--muted)", borderRadius: 6,
                                   padding: "4px 10px", fontSize: 12, cursor: "pointer",
                                   marginRight: 6 }}>
                          Edit
                        </button>
                        <button onClick={() => refreshStats(l.id)} disabled={busy !== ""}
                          style={{ background: "none", border: "1px solid var(--border)",
                                   color: "var(--muted)", borderRadius: 6,
                                   padding: "4px 10px", fontSize: 12, cursor: "pointer" }}>
                          {busy === `stats-${l.id}` ? "…" : "↻ Stats"}
                        </button>
                      </>
                    )}
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
