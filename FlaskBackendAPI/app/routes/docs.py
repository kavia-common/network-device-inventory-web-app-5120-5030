from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint(
    "Docs",
    "docs",
    url_prefix="/docs-info",
    description="API documentation helper and usage notes"
)

@blp.route("")
class DocsInfo(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """API documentation usage notes.
        No WebSocket endpoints are exposed in this project. All routes are RESTful.
        Visit /docs for Swagger UI and /docs/openapi.json for the raw OpenAPI document.
        """
        return {
            "message": "See /docs for Swagger UI and /docs/openapi.json for OpenAPI JSON. No WebSockets are used."
        }
