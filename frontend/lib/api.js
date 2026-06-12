const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

export function getApiKey() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("dashboard_api_key") || "";
}

export function setApiKey(key) {
  if (typeof window !== "undefined")
    window.localStorage.setItem("dashboard_api_key", key);
}

export function apiBase() { return BASE; }

async function request(path, options = {}) {
  const key = getApiKey();
  const resp = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(key ? { "X-API-Key": key } : {}),
      ...(options.headers || {}),
    },
  });
  if (resp.status === 401) {
    const err = new Error("unauthorized");
    err.unauthorized = true;
    throw err;
  }
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${body}`);
  }
  return resp.status === 204 ? null : resp.json();
}

export const api = {
  health:   () => request("/system/health"),
  summary:  () => request("/analytics/summary"),
  products: () => request("/products"),
  listings: () => request("/listings"),
  trends:   () => request("/trends"),
  events:   () => request("/system/events?limit=50"),
  agents:   () => request("/agents"),

  runAgent: (name, payload = {}) =>
    request(`/agents/${name}/run`, { method: "POST", body: JSON.stringify(payload) }),
  enqueueAgent: (name, payload = {}) =>
    request(`/agents/${name}/enqueue`, { method: "POST", body: JSON.stringify(payload) }),

  // products
  patchProduct: (id, body) =>
    request(`/products/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  publishProduct: (id) =>
    request(`/agents/publisher/run`, { method: "POST",
            body: JSON.stringify({ product_id: id }) }),
  runQA: (id) =>
    request(`/agents/qa/run`, { method: "POST",
            body: JSON.stringify({ product_id: id }) }),

  // listings
  patchListing: (id, body) =>
    request(`/listings/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  refreshListingStats: (id) =>
    request(`/listings/${id}/refresh-stats`, { method: "POST" }),

  // trends
  discoverTrends: (n = 5) => request(`/trends/discover?n=${n}`, { method: "POST" }),
  buildFromTrend: (trendId, productType = null) =>
    request(`/agents/orchestrator/run`, { method: "POST",
      body: JSON.stringify({ trend_id: trendId, skip_trends: true,
                             ...(productType ? { product_type: productType } : {}) }) }),

  // schedules
  schedules:      () => request("/schedules"),
  createSchedule: (body) =>
    request("/schedules", { method: "POST", body: JSON.stringify(body) }),
  updateSchedule: (id, body) =>
    request(`/schedules/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  toggleSchedule: (id) =>
    request(`/schedules/${id}/toggle`, { method: "PATCH" }),
  deleteSchedule: (id) =>
    request(`/schedules/${id}`, { method: "DELETE" }),
};

// SSE — EventSource can't set headers, so the key rides as a query param
export function openEventStream(onEvent, lastId = 0) {
  const key = getApiKey();
  const url = `${BASE}/system/events/stream?last_id=${lastId}`
            + (key ? `&api_key=${encodeURIComponent(key)}` : "");
  const es = new EventSource(url);
  es.onmessage = (e) => {
    try { onEvent(JSON.parse(e.data)); } catch {}
  };
  return es;
}
