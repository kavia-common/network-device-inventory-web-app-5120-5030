const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:3001";

/**
 * INTERNAL: Build URL for API endpoints.
 * @param {string} path
 * @returns {string}
 */
function url(path) {
  const base = API_BASE.replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * INTERNAL: Handle JSON responses with error propagation.
 * @param {Response} res
 */
async function handle(res) {
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const err = new Error((data && data.error) || res.statusText);
    err.status = res.status;
    err.details = data && data.details;
    throw err;
  }
  return data;
}

// PUBLIC_INTERFACE
export async function createDevice(payload) {
  /** Create a device.
   * @param {Object} payload
   * @returns {Promise<Object>} Created device
   */
  const res = await fetch(url("/api/devices"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

// PUBLIC_INTERFACE
export async function listDevices(params = {}) {
  /** List devices with filters/pagination.
   * @param {Object} params
   * @returns {Promise<{items: Object[], total: number, page: number, pageSize: number}>}
   */
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && `${v}`.length) q.append(k, v);
  }
  const res = await fetch(url(`/api/devices?${q.toString()}`), {
    method: "GET",
  });
  return handle(res);
}

// PUBLIC_INTERFACE
export async function getDevice(id) {
  /** Get a device by id.
   * @param {string} id
   * @returns {Promise<Object>}
   */
  const res = await fetch(url(`/api/devices/${encodeURIComponent(id)}`), {
    method: "GET",
  });
  return handle(res);
}

// PUBLIC_INTERFACE
export async function updateDevice(id, payload) {
  /** Update a device by id.
   * @param {string} id
   * @param {Object} payload
   * @returns {Promise<Object>}
   */
  const res = await fetch(url(`/api/devices/${encodeURIComponent(id)}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

// PUBLIC_INTERFACE
export async function deleteDevice(id) {
  /** Delete a device by id.
   * @param {string} id
   * @returns {Promise<void>}
   */
  const res = await fetch(url(`/api/devices/${encodeURIComponent(id)}`), {
    method: "DELETE",
  });
  if (res.status === 204) return;
  return handle(res);
}

// PUBLIC_INTERFACE
export async function bulkDelete(ids) {
  /** Bulk delete devices.
   * @param {string[]} ids
   * @returns {Promise<{deletedCount: number}>}
   */
  const res = await fetch(url(`/api/devices`), {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
  return handle(res);
}

// PUBLIC_INTERFACE
export async function pingDevice(id) {
  /** Ping device (stubbed).
   * @param {string} id
   * @returns {Promise<{status: string, message: string}>}
   */
  const res = await fetch(url(`/api/devices/${encodeURIComponent(id)}/ping`), {
    method: "POST",
  });
  return handle(res);
}
