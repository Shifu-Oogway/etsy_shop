"use client";

import { useEffect, useRef, useState } from "react";
import { api, apiBase, getApiKey } from "../lib/api";

const TYPE_ICON = {
  pdf_planner: "📄", excel_template: "📊", notion_template: "📝",
};

const STATUS_COLOR = {
  published: "var(--ok)", qa_passed: "var(--ok)",
  qa_failed: "var(--err)", failed: "var(--err)",
  draft: "var(--warn)", generated: "var(--warn)", pending: "var(--warn)",
  archived: "var(--muted)",
};

export default function ProductDrawer({ product, onClose, onChanged }) {
  const overlayRef = useRef();
  const [mode, setMode]   = useState("view");   // view | edit
  const [draft, setDraft] = useState({});
  const [busy, setBusy]   = useState("");
  const [msg, setMsg]     = useState(null);
  const [imgErr, setImgErr] = useState({});

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!product) return null;

  const key = getApiKey();
  const keyQ = key ? `?api_key=${encodeURIComponent(key)}` : "";
  const previewUrl  = `${apiBase()}/products/${product.id}/preview${keyQ}`;
  const downloadUrl = `${apiBase()}/products/${product.id}/download${keyQ}`;
  const images = (product.spec?.images || []);
  const hasFile = Boolean(product.file_path);
  const statusColor = STATUS_COLOR[product.status] || "var(--muted)";
  const icon = TYPE_ICON[product.product_type] || "📦";
  const canPublish = product.status === "qa_passed";
  const canQA = ["generated", "qa_failed"].includes(product.status);

  const startEdit = () => {
    setDraft({ title: product.title, description: product.description,
               price: product.price });
    setMode("edit");
  };

  const save = async () => {
    setBusy("save");
    try {
      await api.patchProduct(product.id, {
        title: draft.title, description: draft.description,
        price: parseFloat(draft.price),
      });
      setMsg({ ok: true, text: "Saved. Content changes require re-running QA." });
      setMode("view");
      if (onChanged) onChanged();
    } catch (e) { setMsg({ ok: false, text: String(e) }); }
    finally { setBusy(""); }
  };

  const runQA = async () => {
    setBusy("qa");
    try {
      const r = await api.runQA(product.id);
      setMsg(r.passed
        ? { ok: true,  text: `QA passed — score ${(r.score * 100).toFixed(0)}%` }
        : { ok: false, text: `QA failed — score ${(r.score * 100).toFixed(0)}%` });
      if (onChanged) onChanged();
    } catch (e) { setMsg({ ok: false, text: String(e) }); }
    finally { setBusy(""); }
  };

  const publish = async () => {
    setBusy("publish");
    try {
      const r = await api.publishProduct(product.id);
      setMsg(r.ok
        ? { ok: true,  text: `Published${r.dry_run ? " (dry-run)" : ""} — listing #${r.listing_id}` }
        : { ok: false, text: r.error || "publish failed" });
      if (onChanged) onChanged();
    } catch (e) { setMsg({ ok: false, text: String(e) }); }
    finally { setBusy(""); }
  };

  const btn = (label, onClick, opts = {}) => (
    <button onClick={onClick} disabled={busy !== ""}
      style={{
        background: opts.primary ? "var(--accent)" : "none",
        color: opts.primary ? "#fff" : (opts.color || "var(--muted)"),
        border: opts.primary ? "none" : `1px solid ${opts.border || "var(--border)"}`,
        borderRadius: 8, padding: "8px 14px", fontSize: 13,
        fontWeight: opts.primary ? 600 : 500, cursor: "pointer",
      }}>
      {busy === opts.busyKey ? "…" : label}
    </button>
  );

  const inputStyle = {
    width: "100%", boxSizing: "border-box",
    background: "var(--surface2)", border: "1px solid var(--border)",
    borderRadius: 8, padding: "9px 12px", color: "var(--text)",
    fontSize: 13, outline: "none", fontFamily: "inherit",
  };

  return (
    <>
      <div ref={overlayRef}
        onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
        style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)",
                 zIndex: 100, display: "flex", justifyContent: "flex-end" }}>
        <div style={{ width: "min(780px, 92vw)", height: "100%",
                      background: "var(--surface)",
                      borderLeft: "1px solid var(--border)",
                      display: "flex", flexDirection: "column",
                      overflow: "hidden", animation: "slideIn .18s ease" }}>

          {/* header */}
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12,
                        padding: "20px 24px 16px",
                        borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
            <div style={{ fontSize: 28, lineHeight: 1 }}>{icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              {mode === "edit" ? (
                <input style={{ ...inputStyle, fontWeight: 700, fontSize: 15 }}
                       value={draft.title}
                       onChange={e => setDraft(d => ({ ...d, title: e.target.value }))} />
              ) : (
                <div style={{ fontWeight: 700, fontSize: 16, lineHeight: 1.3,
                              marginBottom: 6 }}>{product.title}</div>
              )}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap",
                            alignItems: "center", marginTop: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px",
                               borderRadius: 999,
                               background: "rgba(79,142,247,.15)",
                               color: "var(--accent)" }}>
                  {product.product_type}
                </span>
                <span style={{ fontSize: 12, color: "var(--muted)" }}>
                  {product.niche || "—"}
                </span>
                <span style={{ fontSize: 12, fontWeight: 600, color: statusColor }}>
                  {product.status}
                </span>
                {mode === "edit" ? (
                  <input style={{ ...inputStyle, width: 90, marginLeft: "auto" }}
                         type="number" step="0.5"
                         value={draft.price}
                         onChange={e => setDraft(d => ({ ...d, price: e.target.value }))} />
                ) : (
                  <span style={{ fontSize: 13, fontWeight: 700, marginLeft: "auto" }}>
                    ${product.price?.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
            <button onClick={onClose}
              style={{ background: "none", border: "none", color: "var(--muted)",
                       fontSize: 20, cursor: "pointer", padding: "0 4px",
                       lineHeight: 1, flexShrink: 0 }}>✕</button>
          </div>

          {/* description */}
          <div style={{ padding: "12px 24px",
                        borderBottom: "1px solid var(--border)",
                        fontSize: 13, color: "var(--muted)", lineHeight: 1.6,
                        flexShrink: 0, maxHeight: 130, overflowY: "auto" }}>
            {mode === "edit" ? (
              <textarea style={{ ...inputStyle, minHeight: 80, resize: "vertical" }}
                        value={draft.description}
                        onChange={e => setDraft(d => ({ ...d, description: e.target.value }))} />
            ) : (product.description || <em>No description</em>)}
          </div>

          {/* message */}
          {msg && (
            <div style={{ padding: "8px 24px", fontSize: 12, flexShrink: 0,
                          color: msg.ok ? "var(--ok)" : "var(--err)",
                          background: msg.ok ? "rgba(62,207,142,.06)" : "rgba(242,84,74,.06)",
                          borderBottom: "1px solid var(--border)" }}>
              {msg.text}
            </div>
          )}

          {/* action bar */}
          <div style={{ display: "flex", gap: 8, padding: "12px 24px",
                        borderBottom: "1px solid var(--border)", flexShrink: 0,
                        alignItems: "center", flexWrap: "wrap" }}>
            {mode === "edit" ? (
              <>
                {btn("Save changes", save, { primary: true, busyKey: "save" })}
                {btn("Cancel", () => setMode("view"))}
              </>
            ) : (
              <>
                {btn("✎ Edit", startEdit)}
                {canQA && btn("Run QA", runQA, { busyKey: "qa" })}
                {canPublish && btn("🚀 Publish", publish,
                                   { primary: true, busyKey: "publish" })}
                {hasFile && (
                  <a href={downloadUrl} target="_blank" rel="noreferrer"
                     style={{ color: "var(--accent)", fontSize: 13,
                              textDecoration: "none", fontWeight: 600,
                              padding: "8px 4px" }}>
                    ↓ Download
                  </a>
                )}
              </>
            )}
            <div style={{ fontSize: 12, color: "var(--muted)", marginLeft: "auto" }}>
              #{product.id} · {new Date(product.created_at).toLocaleDateString()}
            </div>
          </div>

          {/* mockup images */}
          {images.length > 0 && (
            <div style={{ display: "flex", gap: 10, padding: "12px 24px",
                          borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
              {images.map((_, i) => !imgErr[i] && (
                <img key={i}
                     src={`${apiBase()}/products/${product.id}/images/${i}${keyQ}`}
                     alt={`Mockup ${i + 1}`}
                     onError={() => setImgErr(e => ({ ...e, [i]: true }))}
                     style={{ height: 110, borderRadius: 8,
                              border: "1px solid var(--border)" }} />
              ))}
            </div>
          )}

          {/* preview iframe */}
          <div style={{ flex: 1, overflow: "hidden" }}>
            <iframe src={previewUrl} title={`Preview: ${product.title}`}
              style={{ width: "100%", height: "100%", border: "none",
                       background: "var(--bg)" }}
              sandbox="allow-scripts allow-same-origin" />
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from { transform: translateX(40px); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </>
  );
}
