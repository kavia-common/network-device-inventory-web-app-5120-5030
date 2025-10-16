from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from pymongo.errors import DuplicateKeyError, PyMongoError

from ..auth import require_api_key
from ..db import get_db
from ..schemas import DeviceSchema

blp = Blueprint(
    "Devices",
    "devices",
    url_prefix="/devices",
    description="CRUD operations for network devices"
)


def _serialize_device(doc: Dict[str, Any]) -> Dict[str, Any]:
    return DeviceSchema().dump(doc)


@blp.route("")
class DevicesCollection(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """List all devices."""
        devices_col, _ = get_db()
        try:
            docs = list(devices_col.find({}))
            return [DeviceSchema().dump(d) for d in docs], 200
        except PyMongoError as e:
            return jsonify({"error_code": "DB_ERROR", "message": "Failed to fetch devices", "details": str(e)}), 500

    # PUBLIC_INTERFACE
    @require_api_key
    def post(self):
        """Create a new device."""
        payload = request.get_json(silent=True) or {}
        schema = DeviceSchema()
        try:
            data = schema.load(payload)
        except Exception as e:
            return jsonify({"error_code": "VALIDATION_ERROR", "message": "Invalid input", "details": str(e)}), 400

        device_doc = {
            "name": data["name"],
            "ip_address": data["ip_address"],
            "mac_address": data["mac_address"],
            "location": data["location"],
            "device_type": data["type"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        devices_col, _ = get_db()
        try:
            res = devices_col.insert_one(device_doc)
            device_doc["_id"] = res.inserted_id
            return schema.dump(device_doc), 201
        except DuplicateKeyError:
            return jsonify({"error_code": "DUPLICATE", "message": "MAC address must be unique"}), 400
        except PyMongoError as e:
            return jsonify({"error_code": "DB_ERROR", "message": "Failed to create device", "details": str(e)}), 500


@blp.route("/<string:device_id>")
class DeviceItem(MethodView):
    # PUBLIC_INTERFACE
    def get(self, device_id: str):
        """Get device by ID."""
        try:
            oid = ObjectId(device_id)
        except Exception:
            return jsonify({"error_code": "INVALID_ID", "message": "Invalid device ID"}), 400

        devices_col, _ = get_db()
        doc = devices_col.find_one({"_id": oid})
        if not doc:
            return jsonify({"error_code": "NOT_FOUND", "message": "Device not found"}), 404
        return DeviceSchema().dump(doc), 200

    # PUBLIC_INTERFACE
    @require_api_key
    def put(self, device_id: str):
        """Update device by ID."""
        try:
            oid = ObjectId(device_id)
        except Exception:
            return jsonify({"error_code": "INVALID_ID", "message": "Invalid device ID"}), 400

        payload = request.get_json(silent=True) or {}
        schema = DeviceSchema()
        try:
            data = schema.load(payload)
        except Exception as e:
            return jsonify({"error_code": "VALIDATION_ERROR", "message": "Invalid input", "details": str(e)}), 400

        update_doc = {
            "name": data["name"],
            "ip_address": data["ip_address"],
            "mac_address": data["mac_address"],
            "location": data["location"],
            "device_type": data["type"],
            "updated_at": datetime.utcnow(),
        }

        devices_col, _ = get_db()
        try:
            result = devices_col.update_one({"_id": oid}, {"$set": update_doc})
            if result.matched_count == 0:
                return jsonify({"error_code": "NOT_FOUND", "message": "Device not found"}), 404
            doc = devices_col.find_one({"_id": oid})
            return schema.dump(doc), 200
        except DuplicateKeyError:
            return jsonify({"error_code": "DUPLICATE", "message": "MAC address must be unique"}), 400
        except PyMongoError as e:
            return jsonify({"error_code": "DB_ERROR", "message": "Failed to update device", "details": str(e)}), 500

    # PUBLIC_INTERFACE
    @require_api_key
    def delete(self, device_id: str):
        """Delete device by ID."""
        try:
            oid = ObjectId(device_id)
        except Exception:
            return jsonify({"error_code": "INVALID_ID", "message": "Invalid device ID"}), 400

        devices_col, _ = get_db()
        try:
            result = devices_col.delete_one({"_id": oid})
            if result.deleted_count == 0:
                return jsonify({"error_code": "NOT_FOUND", "message": "Device not found"}), 404
            return "", 204
        except PyMongoError as e:
            return jsonify({"error_code": "DB_ERROR", "message": "Failed to delete device", "details": str(e)}), 500
