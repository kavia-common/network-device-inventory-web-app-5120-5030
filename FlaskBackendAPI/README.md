# FlaskBackendAPI

Minimal Flask app initialized for dependency upgrade.

Setup:
- python -m venv .venv && source .venv/bin/activate
- pip install --upgrade pip
- pip install -r requirements.txt
- python app.py

Endpoints:
- GET /health -> {"status":"ok","service":"FlaskBackendAPI","version":"0.1.0"}

Environment variables:
- PORT (default 5000)
- APP_VERSION (optional)

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
