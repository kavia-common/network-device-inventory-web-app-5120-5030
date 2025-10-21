import logging
from typing import Any, Dict, List, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, request
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

from ..db import get_devices_collection
from ..validation import (
    validate_create,
    validate_update,
)

logger = logging.getLogger(__name__)

devices_bp = Blueprint("devices", __name__)


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise ValueError("Invalid id")


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def _parse_sort(sort_by: str, sort_dir: str) -> Tuple[str, int]:
    field_map = {
        "deviceName": "deviceName",
        "ipAddress": "ipAddress",
        "createdAt": "createdAt",
        "updatedAt": "updatedAt",
    }
    key = field_map.get(sort_by, "createdAt")
    direction = ASCENDING if sort_dir.lower() == "asc" else DESCENDING
    return key, direction


@devices_bp.post("")
def create_device():
    """
    Create a device.

    Summary:
        POST /api/devices
    Request Body:
        JSON with fields: deviceName (required), ipAddress (required), optional macAddress, location, deviceType, notes, status
    Returns:
        201 with created document or errors with appropriate status codes.
    """
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    ok, errors, cleaned = validate_create(payload)
    if not ok:
        return jsonify({"error": "Validation error", "details": errors}), 422

    try:
        col = get_devices_collection()
        res = col.insert_one(cleaned)
        saved = col.find_one({"_id": res.inserted_id})
        return jsonify(_serialize(saved or cleaned)), 201
    except DuplicateKeyError as e:
        return jsonify({"error": "Duplicate key", "details": "ipAddress must be unique"}), 409
    except PyMongoError as e:
        logger.exception("Create device DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@devices_bp.get("")
def list_devices():
    """
    List devices with optional filters, sorting, and pagination.

    Summary:
        GET /api/devices
    Query Params:
        search (in deviceName or ipAddress), type (deviceType), location,
        sortBy (deviceName|ipAddress|createdAt|updatedAt), sortDir (asc|desc),
        page (1-based), pageSize
    Returns:
        200 with { items: [...], total: <int>, page, pageSize }
    """
    args = request.args

    search = (args.get("search") or "").strip()
    device_type = (args.get("type") or "").strip().lower()
    location = (args.get("location") or "").strip()

    sort_by = (args.get("sortBy") or "createdAt").strip()
    sort_dir = (args.get("sortDir") or "desc").strip()
    page = max(1, int(args.get("page", "1")))
    page_size = min(200, max(1, int(args.get("pageSize", "20"))))

    q: Dict[str, Any] = {}
    if search:
        q["$or"] = [
            {"deviceName": {"$regex": search, "$options": "i"}},
            {"ipAddress": {"$regex": search, "$options": "i"}},
        ]
    if device_type:
        q["deviceType"] = device_type
    if location:
        q["location"] = {"$regex": location, "$options": "i"}

    try:
        col = get_devices_collection()
        total = col.count_documents(q)
        key, direction = _parse_sort(sort_by, sort_dir)
        cursor = (
            col.find(q)
            .sort(key, direction)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_serialize(doc) for doc in cursor]
        return jsonify({"items": items, "total": total, "page": page, "pageSize": page_size}), 200
    except PyMongoError as e:
        logger.exception("List devices DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@devices_bp.get("/<id>")
def get_device(id: str):
    """
    Get a single device by ID.

    Summary:
        GET /api/devices/<id>
    Returns:
        200 with device json or 404 if not found.
    """
    try:
        col = get_devices_collection()
        doc = col.find_one({"_id": _oid(id)})
        if not doc:
            return jsonify({"error": "Not found"}), 404
        return jsonify(_serialize(doc)), 200
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400
    except PyMongoError as e:
        logger.exception("Get device DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@devices_bp.put("/<id>")
def update_device(id: str):
    """
    Update a device by ID (partial update allowed).

    Summary:
        PUT /api/devices/<id>
    Request Body:
        JSON with updatable fields (see create)
    Returns:
        200 with updated device, or relevant error codes.
    """
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    ok, errors, cleaned = validate_update(payload)
    if not ok:
        return jsonify({"error": "Validation error", "details": errors}), 422

    if not cleaned:
        return jsonify({"error": "No valid fields provided"}), 400

    try:
        col = get_devices_collection()
        res = col.find_one_and_update(
            {"_id": _oid(id)},
            {"$set": cleaned},
            return_document=True,  # type: ignore
        )
        if not res:
            return jsonify({"error": "Not found"}), 404
        return jsonify(_serialize(res)), 200
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400
    except DuplicateKeyError:
        return jsonify({"error": "Duplicate key", "details": "ipAddress must be unique"}), 409
    except PyMongoError as e:
        logger.exception("Update device DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@devices_bp.delete("/<id>")
def delete_device(id: str):
    """
    Delete a single device by ID.

    Summary:
        DELETE /api/devices/<id>
    Returns:
        204 on success, 404 if not found.
    """
    try:
        col = get_devices_collection()
        res = col.delete_one({"_id": _oid(id)})
        if res.deleted_count == 0:
            return jsonify({"error": "Not found"}), 404
        return "", 204
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400
    except PyMongoError as e:
        logger.exception("Delete device DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@devices_bp.delete("")
def bulk_delete():
    """
    Bulk delete devices.

    Summary:
        DELETE /api/devices
    Request Body:
        { "ids": [ "<ObjectId>", ... ] }
    Returns:
        200 with {deletedCount: N}
    """
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    ids = payload.get("ids")
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "Validation error", "details": "ids must be a non-empty list"}), 422

    try:
        oid_list = []
        for s in ids:
            oid_list.append(_oid(str(s)))
        col = get_devices_collection()
        res = col.delete_many({"_id": {"$in": oid_list}})
        return jsonify({"deletedCount": res.deleted_count}), 200
    except ValueError:
        return jsonify({"error": "Invalid id in ids list"}), 400
    except PyMongoError as e:
        logger.exception("Bulk delete DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@devices_bp.post("/<id>/ping")
def ping_device(id: str):
    """
    Ping a device using pythonping and return status/latency metrics.

    Summary:
        POST /api/devices/<id>/ping
    Returns:
        200 with JSON:
        {
            "status": "online"|"offline",
            "rttMs": <float|null>,
            "sent": <int>,
            "received": <int>,
            "loss": <float>,  # 0..100
        }
        404 if device not found
        400 if invalid id
        501 if ping is disabled via env
    """
    import os
    from datetime import datetime

    try:
        from pythonping import ping as py_ping  # lazy import
    except Exception as e:
        # If library missing or import fails unexpectedly, surface server error
        logger.exception("pythonping import error")
        return jsonify({"error": "Server error", "details": str(e)}), 500

    # Env configuration with defaults
    ping_enabled = (os.getenv("PING_ENABLED", "true") or "true").lower() == "true"
    if not ping_enabled:
        return (
            jsonify({"error": "Not Implemented", "details": "Ping is disabled by configuration (PING_ENABLED=false)."}),
            501,
        )

    try:
        col = get_devices_collection()
        doc = col.find_one({"_id": _oid(id)})
        if not doc:
            return jsonify({"error": "Not found"}), 404
        ip = str(doc.get("ipAddress") or "").strip()
        if not ip:
            return jsonify({"error": "Device has no ipAddress"}), 422
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400
    except PyMongoError as e:
        logger.exception("Ping device DB error")
        return jsonify({"error": "Database error", "details": str(e)}), 500

    count = max(1, int(os.getenv("PING_COUNT", "2")))
    timeout_ms = max(1, int(os.getenv("PING_TIMEOUT_MS", "800")))
    ttl = max(1, int(os.getenv("PING_TTL", "64")))
    timeout_sec = timeout_ms / 1000.0

    sent = count
    received = 0
    avg_rtt_ms = None
    loss_pct = 100.0
    status = "offline"

    try:
        result = py_ping(ip, count=count, timeout=timeout_sec, ttl=ttl, verbose=False, size=56)
        # pythonping ResponseList provides stats
        rtts_ms = [resp.time_elapsed_ms for resp in result._responses if getattr(resp, "success", False)]
        received = len(rtts_ms)
        loss_pct = round((1 - (received / float(sent))) * 100.0, 2)
        if received > 0:
            avg_rtt_ms = round(sum(rtts_ms) / len(rtts_ms), 2)
            status = "online"
        else:
            avg_rtt_ms = None
            status = "offline"
    except Exception as e:
        # Treat any exception as offline; include detail
        logger.warning("Ping error for %s: %s", ip, e)
        avg_rtt_ms = None
        received = 0
        loss_pct = 100.0
        status = "offline"

    payload = {
        "status": status,
        "rttMs": avg_rtt_ms,
        "sent": sent,
        "received": received,
        "loss": loss_pct,
    }

    # Emit SSE event for subscribers
    try:
        from ..sse import sse_publish  # local import to avoid circular at import-time
        sse_publish(
            {
                "type": "deviceStatus",
                "id": str(id),
                "ipAddress": ip,
                "status": status,
                "rttMs": avg_rtt_ms,
                "sent": sent,
                "received": received,
                "loss": loss_pct,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
    except Exception as e:
        logger.debug("Failed to publish SSE event: %s", e)

    return jsonify(payload), 200
