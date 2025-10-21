# network-device-inventory-web-app-5120-5030

This workspace contains the Flask backend API for the Network Device Inventory and a frontend API client stub for integration.

- Backend root: FlaskBackendAPI
- Frontend API client stub (for integration reference): ReactFrontend/src/api/devices.js

Run backend (development):
1) cd FlaskBackendAPI
2) python -m venv .venv && source .venv/bin/activate
3) pip install --upgrade pip && pip install -r requirements.txt
4) cp .env.example .env
   - Set MONGODB_URI and MONGODB_DB_NAME in .env to enable CRUD
   - Optionally set CORS_ALLOW_ORIGINS=http://localhost:3000 for local React dev
5) python app.py

Key backend endpoints:
- GET /health
- GET /api/spec
- POST /api/devices
- GET /api/devices
- GET /api/devices/<id>
- PUT /api/devices/<id>
- DELETE /api/devices/<id>
- DELETE /api/devices (bulk: { "ids": ["..."] })
- POST /api/devices/<id>/ping
- GET /api/devices/stream (SSE)

Environment variables (set in FlaskBackendAPI/.env):
- MONGODB_URI, MONGODB_DB_NAME (required for DB ops)
- MONGODB_COLLECTION_DEVICES (default: devices)
- PORT (default 3001), APP_VERSION, LOG_LEVEL, SECRET_KEY, CORS_ALLOW_ORIGINS
