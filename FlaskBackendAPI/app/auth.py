from functools import wraps
from flask import request, jsonify
from .config import get_config


# PUBLIC_INTERFACE
def require_api_key(view_func):
    """Decorator to enforce X-API-KEY header on protected routes."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        expected = get_config().API_KEY
        if not expected:
            # If API key is not configured, allow all (dev mode).
            return view_func(*args, **kwargs)

        provided = request.headers.get("X-API-KEY")
        if not provided or provided != expected:
            return jsonify({
                "error_code": "UNAUTHORIZED",
                "message": "Invalid or missing API key"
            }), 401
        return view_func(*args, **kwargs)
    return wrapper
