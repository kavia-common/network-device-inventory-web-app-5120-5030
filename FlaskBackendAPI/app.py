import os
import logging
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
    - PORT: Port to bind (default 3001 to match platform)
    - APP_VERSION: Version string for health output (default 0.1.0)
    - CORS_ALLOW_ORIGINS: Comma-separated list of allowed origins (default '*')
    - SECRET_KEY: Flask secret key (required in non-dev)
    - LOG_LEVEL: Logging level (default INFO)
    - MONGODB_URI: Optional, used for health connectivity check when present
    - MONGODB_DB_NAME: Optional, used for health connectivity check when present

    Returns:
        Flask: The configured Flask app instance with CORS enabled and a health endpoint.
    """
    # Load .env if present for local dev
    load_dotenv(override=False)

    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    logger = logging.getLogger(__name__)
    logger.debug("Initializing Flask app")

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
        port = int(os.getenv("PORT", "3001"))
        response = {
            "status": "ok",
            "service": "FlaskBackendAPI",
            "version": version,
            "port": port,
            "cors_origin": request.headers.get("Origin"),
        }

        # Optionally check Mongo connectivity if URI provided and dependency available
        mongo_uri = os.getenv("MONGODB_URI")
        mongo_db = os.getenv("MONGODB_DB_NAME")
        if mongo_uri and mongo_db and MongoClient is not None:
            try:
                client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "2000")),
                    socketTimeoutMS=int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "20000")),
                    maxPoolSize=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
                    tls=os.getenv("MONGODB_TLS", "false").lower() == "true",
                    tlsCAFile=os.getenv("MONGODB_TLS_CA_FILE") or None,
                )
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
        else:
            # Report configuration status to aid diagnostics without failing startup
            response["mongo"] = {
                "configured": bool(mongo_uri and mongo_db),
                "connected": False if (mongo_uri or mongo_db) else None,
                "message": "Set MONGODB_URI and MONGODB_DB_NAME to enable connectivity check.",
            }

        return jsonify(response)

    return app


if __name__ == "__main__":
    # For local dev only; production should run via gunicorn
    app = create_app()
    # Bind to 0.0.0.0 and default port 3001 to satisfy platform preview expectations
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3001")))
