import os
from flask import Flask, jsonify
from flask_cors import CORS

# PUBLIC_INTERFACE
def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask app instance with CORS enabled and a health endpoint.
    """
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        """
        Health check endpoint.

        Returns:
            JSON response with service status and version.
        """
        return jsonify({"status": "ok", "service": "FlaskBackendAPI", "version": os.getenv("APP_VERSION", "0.1.0")})

    return app


if __name__ == "__main__":
    # For local dev only; production should run via gunicorn
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
