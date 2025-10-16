from app import app
from app.config import get_config

if __name__ == "__main__":
    cfg = get_config()
    app.run(host=cfg.FLASK_RUN_HOST, port=cfg.FLASK_RUN_PORT)
