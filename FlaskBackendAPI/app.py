import os

from app import create_app

if __name__ == "__main__":
    # For local dev only; production should run via gunicorn
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3001")))
