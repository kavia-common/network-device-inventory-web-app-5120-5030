# FlaskBackendAPI

Flask app providing CRUD API for network device inventory with MongoDB.

Setup:
1) Create and activate a virtualenv
- python -m venv .venv && source .venv/bin/activate
2) Install dependencies
- pip install --upgrade pip
- pip install -r requirements.txt
3) Configure environment
- cp .env.example .env
- Edit .env as needed (PORT, APP_VERSION, CORS_ALLOW_ORIGINS, SECRET_KEY, Mongo settings, PING_* settings)
4) Run
- python app.py

Core Endpoints:
- GET /health
- GET /api/spec (minimal OpenAPI-like spec)
- POST /api/devices
- GET /api/devices
- GET /api/devices/<id>
- PUT /api/devices/<id>
- DELETE /api/devices/<id>
- DELETE /api/devices   (bulk delete: { "ids": ["..."] })
- POST /api/devices/<id>/ping (ICMP via pythonping)
- GET /api/devices/stream (SSE: deviceStatus events)

Ping endpoint:
- POST /api/devices/<id>/ping
  - Looks up the device by MongoDB _id and reads its ipAddress.
  - Performs ICMP echo using pythonping with env-configured parameters.
  - Returns JSON:
    {
      "status": "online" | "offline",
      "rttMs": <float|null>,
      "sent": <int>,
      "received": <int>,
      "loss": <float>   // percentage 0..100
    }
  - 404 if device not found; 400 if invalid id; 501 if PING_ENABLED=false.

SSE status stream:
- GET /api/devices/stream
  - Server-Sent Events stream that emits an event after each ping completes.
  - Event name: deviceStatus
  - Headers: text/event-stream, Cache-Control: no-cache, Connection: keep-alive
  - Example payload (event data):
    {
      "type": "deviceStatus",
      "id": "<deviceId>",
      "ipAddress": "192.168.1.10",
      "status": "online"|"offline",
      "rttMs": 23.5|null,
      "sent": 2,
      "received": 2,
      "loss": 0.0,
      "timestamp": "2024-01-01T12:00:00Z"
    }

Validation:
- Required: deviceName, ipAddress
- IPv4 validation (IPv4 regex)
- deviceType normalized to router|switch|server|other (default other)
- Unknown fields rejected (422)
- Field length limits enforced (truncated)
- createdAt/updatedAt set on create; updatedAt on update

Filtering & Pagination (GET /api/devices):
- search: name or ip contains (case-insensitive)
- type: deviceType filter
- location: case-insensitive contains
- sortBy: deviceName|ipAddress|createdAt|updatedAt (default createdAt)
- sortDir: asc|desc (default desc)
- page (1-based), pageSize (default 20, max 200)
Returns: { items, total, page, pageSize }

MongoDB Indexes (auto-created on startup if DB available):
- Unique index on ipAddress (returns 409 on duplicate)
- Text/ascending index on deviceName

Environment variables:
- PORT (default 3001)
- APP_VERSION (optional)
- CORS_ALLOW_ORIGINS (optional; default '*', set to http://localhost:3000 in dev)
- SECRET_KEY (recommended in non-dev)
- LOG_LEVEL (default INFO)
- MONGODB_URI
- MONGODB_DB_NAME
- MONGODB_COLLECTION_DEVICES (default devices)
- Optional TLS/tuning: MONGODB_TLS, MONGODB_TLS_CA_FILE, MONGODB_CONNECT_TIMEOUT_MS, MONGODB_SOCKET_TIMEOUT_MS, MONGODB_MAX_POOL_SIZE

Ping configuration:
- PING_ENABLED (default true): if false, POST /api/devices/<id>/ping returns 501 Not Implemented
- PING_COUNT (default 2): number of echo requests sent
- PING_TIMEOUT_MS (default 800): per-request timeout in milliseconds
- PING_TTL (default 64): IP TTL for outgoing pings

CORS
- Enabled for /api/* routes; configure CORS_ALLOW_ORIGINS.

Notes
- Use gunicorn for production (e.g., gunicorn 'app:create_app()').
- Duplicate ipAddress on create/update returns 409 Conflict.
- Bulk delete requires { "ids": ["ObjectIdString", ...] }.

Dependencies (pinned with safe upper bounds) remain as listed in requirements.txt.
