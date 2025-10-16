import json
import os
from app import app, api  # import your Flask app and Api instance

# Ensure spec includes API key security scheme and global security
with app.app_context():
    spec_dict = api.spec.to_dict()

    # Inject ApiKeyAuth scheme if not present
    components = spec_dict.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-KEY"
    }

    # Global security (except health route which is public)
    spec_dict["security"] = [{"ApiKeyAuth": []}]

    # Tag health route as public (no security)
    paths = spec_dict.get("paths", {})
    root_get = paths.get("/", {}).get("get")
    if root_get is not None:
        root_get["security"] = []

    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(spec_dict, f, indent=2)
