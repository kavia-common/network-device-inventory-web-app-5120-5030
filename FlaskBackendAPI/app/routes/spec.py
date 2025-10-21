from flask import Blueprint, jsonify

spec_bp = Blueprint("spec", __name__)


@spec_bp.get("/spec")
def openapi_spec():
    """
    Return a minimal OpenAPI-like JSON for the API.

    Summary:
        GET /api/spec
    Returns:
        200 with JSON documenting endpoints and parameters.
    """
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Network Device Inventory API",
            "version": "0.1.0",
            "description": "CRUD API for managing network devices.",
        },
        "paths": {
            "/api/devices": {
                "get": {
                    "summary": "List devices",
                    "parameters": [
                        {"name": "search", "in": "query", "schema": {"type": "string"}},
                        {"name": "type", "in": "query", "schema": {"type": "string"}},
                        {"name": "location", "in": "query", "schema": {"type": "string"}},
                        {"name": "sortBy", "in": "query", "schema": {"type": "string", "enum": ["deviceName", "ipAddress", "createdAt", "updatedAt"]}},
                        {"name": "sortDir", "in": "query", "schema": {"type": "string", "enum": ["asc", "desc"]}},
                        {"name": "page", "in": "query", "schema": {"type": "integer"}},
                        {"name": "pageSize", "in": "query", "schema": {"type": "integer"}},
                    ],
                },
                "post": {
                    "summary": "Create device",
                },
                "delete": {
                    "summary": "Bulk delete devices",
                },
            },
            "/api/devices/{id}": {
                "get": {
                    "summary": "Get device by id",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                },
                "put": {
                    "summary": "Update device by id",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                },
                "delete": {
                    "summary": "Delete device by id",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                },
            },
            "/api/devices/{id}/ping": {
                "post": {
                    "summary": "Ping device",
                    "description": "Ping a device using ICMP (pythonping) and return status/latency metrics.",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                }
            },
            "/api/devices/stream": {
                "get": {
                    "summary": "Device status SSE stream",
                    "description": "Server-Sent Events stream with event: deviceStatus and JSON payload on ping completion."
                }
            },
            "/health": {
                "get": {"summary": "Health check"},
            },
        },
    }
    return jsonify(spec)
