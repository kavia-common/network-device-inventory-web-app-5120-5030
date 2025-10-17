# FlaskBackendAPI

Minimal Flask app initialized for dependency upgrade.

Setup:
1) Create and activate a virtualenv
- python -m venv .venv && source .venv/bin/activate
2) Install dependencies
- pip install --upgrade pip
- pip install -r requirements.txt
3) Configure environment (optional in dev)
- cp .env.example .env
- Edit .env as needed (PORT, APP_VERSION, CORS_ALLOW_ORIGINS, SECRET_KEY, Mongo placeholders)
4) Run
- python app.py

Endpoints:
- GET /health -> {"status":"ok","service":"FlaskBackendAPI","version":"0.1.0","port":3001,"cors_origin":"...","mongo":{...}}

Defaults and Ports:
- Binds host 0.0.0.0 and PORT=3001 by default to satisfy preview requirements.
- You can override PORT via environment variable.

Environment variables:
- PORT (default 3001)
- APP_VERSION (optional)
- CORS_ALLOW_ORIGINS (optional; defaults to allowing all via flask-cors; set to http://localhost:3000 for Vite dev)
- SECRET_KEY (required in non-dev; example value provided in .env.example)
- LOG_LEVEL (default INFO)

MongoDB configuration (used by health check and for future CRUD):
- MONGODB_URI
- MONGODB_DB_NAME
- MONGODB_COLLECTION_DEVICES
- MONGODB_COLLECTION_LOGS
- Optional TLS and tuning: MONGODB_TLS, MONGODB_TLS_CA_FILE, MONGODB_CONNECT_TIMEOUT_MS, MONGODB_SOCKET_TIMEOUT_MS, MONGODB_MAX_POOL_SIZE

CORS
- flask-cors is enabled globally in app.py.
- For local dev with Vite (React), set CORS_ALLOW_ORIGINS=http://localhost:3000 in your .env (or leave default permissive dev CORS).

Upgraded packages (pinned with safe upper bounds):
- Flask >=3.0.3,<3.2
- flask-cors >=5,<6
- pymongo >=4.8,<5
- motor >=3.6,<4
- pythonping >=1.1.5,<2
- pydantic >=2.9,<3
- typing-extensions >=4.12,<5
- gunicorn >=23,<24
- requests >=2.32,<3
- httpx >=0.27,<0.28
- python-dotenv >=1.0,<2
