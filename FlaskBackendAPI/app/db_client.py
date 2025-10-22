"""
MongoDB client and CRUD helpers for devices and logs using PyMongo.

This module centralizes database access for the Flask backend and provides:
- A lazy MongoClient factory, configured via environment variables
- Safe ObjectId validation and conversion
- CRUD functions for devices and logs
- Automatic created_at and updated_at timestamps
- Index initialization for performance and constraints

Environment variables:
- MONGODB_URI: MongoDB connection string (required if not providing separate credentials)
- MONGODB_DB_NAME: Database name (default: device_inventory)
- MONGODB_DEVICES_COLLECTION: Devices collection name (default: devices)
- MONGODB_LOGS_COLLECTION: Logs collection name (default: logs)
- MONGODB_TLS: "true"/"false" to enable TLS/SSL (optional)
- MONGODB_USERNAME: Username (optional if URI contains credentials)
- MONGODB_PASSWORD: Password (optional if URI contains credentials)

Notes:
- Do not modify routes here; integration will be done in a separate step.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


def _env_bool(name: str, default: Optional[bool] = None) -> Optional[bool]:
    """Convert environment variable to boolean if set."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def _now() -> datetime:
    """UTC now for timestamps."""
    return datetime.utcnow()


def _to_object_id(value: str) -> ObjectId:
    """Validate and convert a string to ObjectId, raising ValueError if invalid."""
    try:
        return ObjectId(value)
    except Exception as e:
        raise ValueError("Invalid ObjectId") from e


def _serialize(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert a MongoDB document to an API-friendly dict (stringify _id to id)."""
    if not doc:
        return doc
    out = dict(doc)
    _id = out.pop("_id", None)
    if isinstance(_id, ObjectId):
        out["id"] = str(_id)
    elif _id is not None:
        out["id"] = str(_id)
    return out


class _MongoContext:
    """Internal context holding client, db, and collections; ensures indexes."""

    def __init__(self):
        # Build client config from env
        uri = os.getenv("MONGODB_URI")
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")
        tls = _env_bool("MONGODB_TLS")

        client_kwargs: Dict[str, Any] = {}
        if tls is not None:
            client_kwargs["tls"] = tls

        if uri:
            self.client = MongoClient(uri, **client_kwargs)
        else:
            # If URI is not provided, allow username/password based initialization on localhost defaults.
            host = os.getenv("MONGODB_HOST", "localhost")
            port = int(os.getenv("MONGODB_PORT", "27017"))
            if username and password:
                self.client = MongoClient(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    **client_kwargs,
                )
            else:
                # Fall back to unauthenticated local connection
                self.client = MongoClient(host=host, port=port, **client_kwargs)

        db_name = os.getenv("MONGODB_DB_NAME", "device_inventory")
        devices_coll = os.getenv("MONGODB_DEVICES_COLLECTION", "devices")
        logs_coll = os.getenv("MONGODB_LOGS_COLLECTION", "logs")

        self.db = self.client[db_name]
        self.devices: Collection = self.db[devices_coll]
        self.logs: Collection = self.db[logs_coll]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create indexes to improve performance and enforce constraints."""
        try:
            # Devices indexes
            self.devices.create_index([("mac_address", ASCENDING)], unique=True, name="uniq_mac")
            self.devices.create_index([("ip_address", ASCENDING)], name="idx_ip")
            self.devices.create_index([("device_type", ASCENDING)], name="idx_type")
            self.devices.create_index([("location", ASCENDING), ("device_type", ASCENDING)], name="idx_location_type")
            # Logs indexes
            self.logs.create_index([("device_id", ASCENDING)], name="idx_log_device")
            self.logs.create_index([("timestamp", ASCENDING)], name="idx_log_ts")
        except PyMongoError:
            # Do not crash app if index creation fails; operations will still be attempted.
            pass


_ctx: Optional[_MongoContext] = None


# PUBLIC_INTERFACE
def get_client() -> MongoClient:
    """Return the underlying MongoClient instance for advanced usage."""
    global _ctx
    if _ctx is None:
        _ctx = _MongoContext()
    return _ctx.client


def _get_context() -> _MongoContext:
    """Return the internal Mongo context, initializing on first use."""
    global _ctx
    if _ctx is None:
        _ctx = _MongoContext()
    return _ctx


# PUBLIC_INTERFACE
def create_device(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a device document and return the inserted document with id as string.

    Required fields: name, ip_address, mac_address, location, device_type (or type)
    Raises:
        ValueError: If required fields are missing or id conversion fails.
        PyMongoError: On database operation errors.
        DuplicateKeyError: If mac_address is not unique.
    """
    name = data.get("name")
    ip = data.get("ip_address")
    mac = data.get("mac_address")
    location = data.get("location")
    device_type = data.get("device_type") or data.get("type")

    if not all([name, ip, mac, location, device_type]):
        raise ValueError("Missing required fields")

    # Basic field normalization
    doc = {
        "name": name,
        "ip_address": ip,
        "mac_address": mac,
        "location": location,
        "device_type": device_type,
        "created_at": _now(),
        "updated_at": _now(),
    }

    ctx = _get_context()
    res = ctx.devices.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _serialize(doc)  # type: ignore[return-value]


# PUBLIC_INTERFACE
def list_devices(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Return a list of device documents as dicts with string ids.

    Args:
        filter: Optional Mongo-style filter dict.
    """
    ctx = _get_context()
    q = filter or {}
    docs = list(ctx.devices.find(q))
    return [_serialize(d) for d in docs]  # type: ignore[list-item]


# PUBLIC_INTERFACE
def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a device by string ObjectId. Returns None if not found.

    Raises:
        ValueError: If device_id is not a valid ObjectId.
    """
    oid = _to_object_id(device_id)
    ctx = _get_context()
    doc = ctx.devices.find_one({"_id": oid})
    return _serialize(doc)


# PUBLIC_INTERFACE
def update_device(device_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a device by id and return the updated document, or None if not found.

    Required fields in data: name, ip_address, mac_address, location, device_type (or type)
    Raises:
        ValueError: If device_id is invalid or required fields are missing.
        DuplicateKeyError: If mac_address violates the unique index.
        PyMongoError: On db errors.
    """
    oid = _to_object_id(device_id)

    name = data.get("name")
    ip = data.get("ip_address")
    mac = data.get("mac_address")
    location = data.get("location")
    device_type = data.get("device_type") or data.get("type")

    if not all([name, ip, mac, location, device_type]):
        raise ValueError("Missing required fields")

    update_doc = {
        "name": name,
        "ip_address": ip,
        "mac_address": mac,
        "location": location,
        "device_type": device_type,
        "updated_at": _now(),
    }

    ctx = _get_context()
    result = ctx.devices.update_one({"_id": oid}, {"$set": update_doc})
    if result.matched_count == 0:
        return None
    doc = ctx.devices.find_one({"_id": oid})
    return _serialize(doc)


# PUBLIC_INTERFACE
def delete_device(device_id: str) -> bool:
    """Delete a device by id. Returns True if a document was deleted.

    Raises:
        ValueError: If device_id is invalid.
        PyMongoError: On db errors.
    """
    oid = _to_object_id(device_id)
    ctx = _get_context()
    res = ctx.devices.delete_one({"_id": oid})
    return res.deleted_count > 0


# PUBLIC_INTERFACE
def create_log(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a log entry and return the inserted document with string id.

    Required fields:
        - device_id (str): as string ObjectId
        - action (str)

    Optional fields:
        - details (dict)
        - user (str)

    Raises:
        ValueError: If device_id is invalid or required fields missing.
        PyMongoError: On db errors.
    """
    if "device_id" not in data or "action" not in data:
        raise ValueError("Missing required fields: device_id, action")

    oid = _to_object_id(data["device_id"])
    log = {
        "device_id": oid,
        "action": data["action"],
        "details": data.get("details") or {},
        "user": data.get("user"),
        "timestamp": _now(),
        "created_at": _now(),
        "updated_at": _now(),
    }
    ctx = _get_context()
    res = ctx.logs.insert_one(log)
    log["_id"] = res.inserted_id
    return _serialize(log)  # type: ignore[return-value]


# PUBLIC_INTERFACE
def list_logs(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Return list of logs, optionally filtered.

    If filter contains device_id as string, it will be converted to ObjectId.
    """
    q: Dict[str, Any] = dict(filter or {})
    if "device_id" in q and isinstance(q["device_id"], str):
        q["device_id"] = _to_object_id(q["device_id"])

    ctx = _get_context()
    docs = list(ctx.logs.find(q).sort("timestamp", ASCENDING))
    return [_serialize(d) for d in docs]  # type: ignore[list-item]
