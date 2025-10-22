import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError

# Simple validators based on provided schema patterns
_ipv4_regex = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
_mac_regex = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def _validate_ip(ip: str) -> None:
    if not isinstance(ip, str) or not _ipv4_regex.match(ip or ""):
        raise ValueError("Invalid IPv4 address format")
    parts = ip.split(".")
    if any(int(p) > 255 or int(p) < 0 for p in parts):
        raise ValueError("IPv4 octets must be between 0 and 255")


def _validate_mac(mac: str) -> None:
    if not isinstance(mac, str) or not _mac_regex.match(mac or ""):
        raise ValueError("Invalid MAC address format (expected XX:XX:XX:XX:XX:XX)")


def _now() -> datetime:
    return datetime.utcnow()


class _DBClient:
    """
    Internal DB client wrapper for MongoDB using PyMongo.
    Manages connection and provides collections access with ensured indexes.
    """

    def __init__(self):
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "device_inventory")
        devices_coll = os.getenv("MONGODB_COLLECTION_DEVICES", os.getenv("MONGODB_COLLECTION_DEVICES".replace("MONGODB_COLLECTION_DEVICES", "MONGODB_COLLECTION_DEVICES"), "devices"))
        logs_coll = os.getenv("MONGODB_COLLECTION_LOGS", os.getenv("MONGODB_COLLECTION_LOGS".replace("MONGODB_COLLECTION_LOGS", "MONGODB_COLLECTION_LOGS"), "logs"))

        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.devices: Collection = self.db[devices_coll]
        self.logs: Collection = self.db[logs_coll]
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.devices.create_index([("mac_address", ASCENDING)], unique=True, name="uniq_mac")
            self.devices.create_index([("ip_address", ASCENDING)], name="idx_ip")
            self.devices.create_index([("device_type", ASCENDING)], name="idx_type")
            self.devices.create_index([("location", ASCENDING), ("device_type", ASCENDING)], name="idx_location_type")
            self.logs.create_index([("device_id", ASCENDING)], name="idx_log_device")
            self.logs.create_index([("timestamp", ASCENDING)], name="idx_log_ts")
        except PyMongoError:
            # Failing to create indexes should not bring the app down.
            pass


_db_instance: Optional[_DBClient] = None


def _get_client() -> _DBClient:
    global _db_instance
    if _db_instance is None:
        _db_instance = _DBClient()
    return _db_instance


def _serialize_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out and isinstance(out["_id"], ObjectId):
        out["id"] = str(out["_id"])
        del out["_id"]
    return out


# PUBLIC_INTERFACE
def create_device(payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    """
    Create a device document.

    Returns: (device_doc, error_message, http_status)
    """
    try:
        name = payload.get("name")
        ip = payload.get("ip_address")
        mac = payload.get("mac_address")
        location = payload.get("location")
        device_type = payload.get("type") or payload.get("device_type")

        if not all([name, ip, mac, location, device_type]):
            return None, "Missing required fields", 400

        _validate_ip(ip)
        _validate_mac(mac)

        doc = {
            "name": name,
            "ip_address": ip,
            "mac_address": mac,
            "location": location,
            "device_type": device_type,
            "created_at": _now(),
            "updated_at": _now(),
        }
        client = _get_client()
        res = client.devices.insert_one(doc)
        doc["_id"] = res.inserted_id
        return _serialize_id(doc), None, 201
    except DuplicateKeyError:
        return None, "MAC address must be unique", 400
    except ValueError as ve:
        return None, str(ve), 400
    except PyMongoError as e:
        return None, f"DB error: {e}", 500


# PUBLIC_INTERFACE
def list_devices() -> Tuple[List[Dict[str, Any]], Optional[str], int]:
    """
    List all devices.

    Returns: (devices, error_message, http_status)
    """
    try:
        client = _get_client()
        docs = list(client.devices.find({}))
        return [_serialize_id(d) for d in docs], None, 200
    except PyMongoError as e:
        return [], f"DB error: {e}", 500


# PUBLIC_INTERFACE
def get_device_by_id(device_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    """
    Get a single device by its string ObjectId.

    Returns: (device, error_message, http_status)
    """
    try:
        oid = ObjectId(device_id)
    except Exception:
        return None, "Invalid device ID", 400

    client = _get_client()
    doc = client.devices.find_one({"_id": oid})
    if not doc:
        return None, "Device not found", 404
    return _serialize_id(doc), None, 200


# PUBLIC_INTERFACE
def update_device(device_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    """
    Update a device by id with provided payload.

    Returns: (updated_device, error_message, http_status)
    """
    try:
        oid = ObjectId(device_id)
    except Exception:
        return None, "Invalid device ID", 400

    try:
        name = payload.get("name")
        ip = payload.get("ip_address")
        mac = payload.get("mac_address")
        location = payload.get("location")
        device_type = payload.get("type") or payload.get("device_type")

        if not all([name, ip, mac, location, device_type]):
            return None, "Missing required fields", 400

        _validate_ip(ip)
        _validate_mac(mac)

        update_doc = {
            "name": name,
            "ip_address": ip,
            "mac_address": mac,
            "location": location,
            "device_type": device_type,
            "updated_at": _now(),
        }
        client = _get_client()
        result = client.devices.update_one({"_id": oid}, {"$set": update_doc})
        if result.matched_count == 0:
            return None, "Device not found", 404
        doc = client.devices.find_one({"_id": oid})
        return _serialize_id(doc), None, 200
    except DuplicateKeyError:
        return None, "MAC address must be unique", 400
    except ValueError as ve:
        return None, str(ve), 400
    except PyMongoError as e:
        return None, f"DB error: {e}", 500


# PUBLIC_INTERFACE
def delete_device(device_id: str) -> Tuple[bool, Optional[str], int]:
    """
    Delete a device by id.

    Returns: (deleted, error_message, http_status)
    """
    try:
        oid = ObjectId(device_id)
    except Exception:
        return False, "Invalid device ID", 400

    try:
        client = _get_client()
        result = client.devices.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return False, "Device not found", 404
        return True, None, 204
    except PyMongoError as e:
        return False, f"DB error: {e}", 500


# PUBLIC_INTERFACE
def list_logs(device_id: Optional[str] = None, limit: int = 100) -> Tuple[List[Dict[str, Any]], Optional[str], int]:
    """
    List logs, optionally filtered by device_id.

    Returns: (logs, error_message, http_status)
    """
    try:
        client = _get_client()
        query: Dict[str, Any] = {}
        if device_id:
            try:
                query["device_id"] = ObjectId(device_id)
            except Exception:
                return [], "Invalid device ID", 400
        docs = list(client.logs.find(query).sort("timestamp", ASCENDING).limit(limit))
        return [_serialize_id(d) for d in docs], None, 200
    except PyMongoError as e:
        return [], f"DB error: {e}", 500


# PUBLIC_INTERFACE
def create_log(device_id: str, action: str, details: Optional[Dict[str, Any]] = None, user: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    """
    Create a log entry linked to a device.

    Returns: (log_doc, error_message, http_status)
    """
    try:
        oid = ObjectId(device_id)
    except Exception:
        return None, "Invalid device ID", 400

    try:
        client = _get_client()
        log = {
            "device_id": oid,
            "action": action,
            "details": details or {},
            "user": user,
            "timestamp": _now(),
        }
        res = client.logs.insert_one(log)
        log["_id"] = res.inserted_id
        return _serialize_id(log), None, 201
    except PyMongoError as e:
        return None, f"DB error: {e}", 500
