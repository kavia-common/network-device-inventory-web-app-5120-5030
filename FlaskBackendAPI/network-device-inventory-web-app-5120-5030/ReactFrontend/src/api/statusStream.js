const API_BASE = process.env.REACT_APP_API_BASE_URL || import.meta?.env?.VITE_API_BASE_URL || "http://localhost:3001";

/**
 * INTERNAL: Normalize base URL and build path.
 * @param {string} path
 * @returns {string}
 */
function url(path) {
  const base = (API_BASE || "").replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * PUBLIC_INTERFACE
 * Subscribe to device status SSE stream.
 * 
 * This returns an object with:
 *  - addEventListener(type, handler)
 *  - removeEventListener(type, handler)
 *  - close()
 *  - onStatus(callback): convenience that subscribes to 'deviceStatus'
 * 
 * Optionally filter by a specific device id using filterId.
 */
export function createStatusStream(filterId) {
  /** Subscribe to SSE stream for device status updates. */
  const es = new EventSource(url("/api/devices/stream"), { withCredentials: false });

  function onStatus(cb) {
    const handler = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (!filterId || data.id === String(filterId)) {
          cb(data);
        }
      } catch (e) {
        // ignore malformed data
      }
    };
    es.addEventListener("deviceStatus", handler);
    return () => es.removeEventListener("deviceStatus", handler);
  }

  return {
    addEventListener: es.addEventListener.bind(es),
    removeEventListener: es.removeEventListener.bind(es),
    close: () => es.close(),
    onStatus,
    _raw: es,
  };
}

/**
 * PUBLIC_INTERFACE
 * React hook style helper that abstracts subscription lifecycle.
 * Returns { events, last, close } and starts listening on mount-like callsite.
 */
export function useDeviceStatusStream(filterId) {
  /** Minimal hook-like function for non-React projects; in React, wrap with useEffect. */
  const state = { events: [], last: null };
  const stream = createStatusStream(filterId);
  const unsubscribe = stream.onStatus((evt) => {
    state.events.push(evt);
    state.last = evt;
  });
  function close() {
    unsubscribe();
    stream.close();
  }
  return { events: state.events, last: state.last, close, stream };
}
