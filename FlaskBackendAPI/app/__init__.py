import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from .db import init_mongo_indexes, mongo_client, get_db

# PUBLIC_INTERFACE
def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Environment variables respected:
    - PORT: Port to bind (default 3001)
    - APP_VERSION: Version string (default 0.1.0)
    - CORS_ALLOW_ORIGINS: Comma-separated list of allowed origins (default '*')
    - SECRET_KEY: Flask secret key (required in non-dev)
    - LOG_LEVEL: Logging level (default INFO)
    - MONGODB_URI: MongoDB connection string (optional in dev; required for CRUD)
    - MONGODB_DB_NAME: MongoDB database name
    - MONGODB_COLLECTION_DEVICES: Collection name for devices (default 'devices')

    Returns:
        Flask: Configured Flask app with CORS, health endpoint, and device routes.
    """
    # Load environment variables from .env for local development
    load_dotenv(override=False)

    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    logger = logging.getLogger(__name__)
    logger.debug("Initializing Flask app")

    app = Flask(__name__)

    # Secret Key
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        app.config["SECRET_KEY"] = secret_key

    # CORS
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
    allowlist: List[str] = [o.strip() for o in raw_origins.split(",") if o.strip()]
    origins: Optional[List[str]] = None if raw_origins.strip() == "*" else allowlist
    CORS(
        app,
        resources={r"/api/*": {"origins": origins or "*"}},
        supports_credentials=True,
    )

    # Register blueprints
    from .routes.devices import devices_bp  # noqa: WPS433
    from .routes.spec import spec_bp  # noqa: WPS433

    app.register_blueprint(devices_bp, url_prefix="/api/devices")
    app.register_blueprint(spec_bp, url_prefix="/api")

    # Health route
    @app.get("/health")
    def health():
        """
        Health check endpoint.

        Summary:
            Provides service liveness and optional MongoDB connectivity status.

        Returns:
            JSON response with service status, version, and db connectivity fields.
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

        # Mongo connectivity
        try:
            db = get_db()
            if db is not None:
                # a trivial ping-like call
                mongo_client().admin.command("ping")
                response["mongo"] = {"connected": True, "db": db.name}
            else:
                response["mongo"] = {
                    "configured": False,
                    "connected": None,
                    "message": "Set MONGODB_URI and MONGODB_DB_NAME to enable connectivity.",
                }
        except Exception as e:
            response["mongo"] = {"connected": False, "error": str(e)}

        return jsonify(response)

    # Initialize indexes at startup (safe to call more than once)
    try:
        init_mongo_indexes()
    except Exception as e:
        logger.warning("Failed to initialize MongoDB indexes: %s", e)

    return app
