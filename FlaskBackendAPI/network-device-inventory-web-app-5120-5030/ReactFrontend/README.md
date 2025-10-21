# React Frontend (stub)

This directory holds minimal API client code for integration with the Flask backend.

API client:
- src/api/devices.js

Usage:
- Import functions like createDevice, listDevices, getDevice, updateDevice, deleteDevice, bulkDelete, pingDevice.
- Configure base URL via environment variable:
  - REACT_APP_API_BASE_URL (e.g., http://localhost:3001)

Example:
import { listDevices } from "./src/api/devices";
listDevices({ page: 1, pageSize: 20 }).then(console.log).catch(console.error);
