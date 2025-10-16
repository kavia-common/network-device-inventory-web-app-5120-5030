from flask import Flask, jsonify
from flask_cors import CORS
from flask_smorest import Api
from .config import get_config
from .routes.health import blp as health_blp
from .routes.devices import blp as devices_blp
from .routes.status import blp as status_blp
from .routes.docs import blp as docs_blp


app = Flask(__name__)
app.url_map.strict_slashes = False

# Load config
cfg = get_config()

# CORS setup
if cfg.CORS_ALLOWED_ORIGINS == ["*"]:
    CORS(app, resources={r"/*": {"origins": "*"}})
else:
    CORS(app, resources={r"/*": {"origins": cfg.CORS_ALLOWED_ORIGINS}})

# OpenAPI metadata
app.config["API_TITLE"] = "Network Device Inventory REST API"
app.config["API_VERSION"] = "1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

# Global error handlers to align with ErrorResponse schema
@app.errorhandler(400)
def handle_400(e):
    return jsonify({"error_code": "BAD_REQUEST", "message": "Bad request"}), 400


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error_code": "NOT_FOUND", "message": "Not found"}), 404


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error_code": "SERVER_ERROR", "message": "Internal server error"}), 500


# Register blueprints
api.register_blueprint(health_blp)
api.register_blueprint(devices_blp)
api.register_blueprint(status_blp)
api.register_blueprint(docs_blp)
