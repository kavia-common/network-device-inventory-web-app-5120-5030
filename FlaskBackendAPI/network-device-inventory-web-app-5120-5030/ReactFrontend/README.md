# React Frontend (stub)

This directory holds minimal API client code for integration with the Flask backend.

API client:
- src/api/devices.js
- src/api/statusStream.js (SSE device status stream)

Usage:
- Import functions like createDevice, listDevices, getDevice, updateDevice, deleteDevice, bulkDelete, pingDevice.
- Subscribe to real-time device status updates via Server-Sent Events.

Environment configuration for API base:
- Prefer VITE_API_BASE_URL (for Vite projects) or fallback to REACT_APP_API_BASE_URL
  - VITE_API_BASE_URL (e.g., http://localhost:3001)
  - REACT_APP_API_BASE_URL (e.g., http://localhost:3001)

SSE example:
import { createStatusStream } from "./src/api/statusStream";

const s = createStatusStream(); // or createStatusStream(deviceId)
const off = s.onStatus((evt) => {
  console.log("deviceStatus:", evt);
});
// later
off();
s.close();
