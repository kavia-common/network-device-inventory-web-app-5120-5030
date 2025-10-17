import os
from typing import List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Attempt to import pymongo to allow optional connectivity checks without requiring DB at boot
try:
    from pymongo import MongoClient  # type: ignore
except Exception:  # pragma: no cover - optional import
    MongoClient = None  # type: ignore


# PUBLIC_INTERFACE
def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Environment variables respected:
    - PORT: Port to bind (default 5000)
    - APP_VERSION: Version string for health output (default 0.1.0)
    - CORS_ALLOW_ORIGINS: Comma-separated list of allowed origins (default '*')
    - SECRET_KEY: Flask secret key (required in non-dev)
    - MONGODB_URI: Optional, used for health connectivity check when present
    - MONGODB_DB_NAME: Optional, used for health connectivity check when present

    Returns:
        Flask: The configured Flask app instance with CORS enabled and a health endpoint.
    """
    # Load .env if present for local dev
    load_dotenv(override=False)

    app = Flask(__name__)

    # Configure secret key if provided (do not hardcode)
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        app.config["SECRET_KEY"] = secret_key

    # Configure CORS
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
    allowlist: List[str] = [o.strip() for o in raw_origins.split(",") if o.strip()]
    origins: Optional[List[str]] = None if raw_origins.strip() == "*" else allowlist
    CORS(
        app,
        resources={r"/*": {"origins": origins or "*"}},
        supports_credentials=True,
    )

    @app.get("/health")
    def health():
        """
        Health check endpoint.

        Summary:
            Provides service liveness and optional MongoDB connectivity status.

        Returns:
            JSON response with service status, version, and optional db connectivity fields.
        """
        version = os.getenv("APP_VERSION", "0.1.0")
        response = {
            "status": "ok",
            "service": "FlaskBackendAPI",
            "version": version,
            "cors_origin": request.headers.get("Origin"),
        }

        # Optionally check Mongo connectivity if URI provided and dependency available
        mongo_uri = os.getenv("MONGODB_URI")
        mongo_db = os.getenv("MONGODB_DB_NAME")
        if mongo_uri and mongo_db and MongoClient is not None:
            try:
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)  # short timeout
                # Trigger server selection
                client.admin.command("ping")
                response["mongo"] = {"connected": True, "db": mongo_db}
            except Exception as e:  # pragma: no cover - external service
                response["mongo"] = {"connected": False, "error": str(e)}
            finally:
                try:
                    client.close()  # type: ignore
                except Exception:
                    pass

        return jsonify(response)

    return app


if __name__ == "__main__":
    # For local dev only; production should run via gunicorn
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
