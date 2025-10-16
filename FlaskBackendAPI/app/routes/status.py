from datetime import datetime
from bson import ObjectId
from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint

from ..config import get_config
from ..db import get_db
from ..schemas import DeviceStatusSchema

blp = Blueprint(
    "Status",
    "status",
    url_prefix="/devices",
    description="Device status endpoints"
)


def _ping(ip: str) -> bool:
    cfg = get_config()
    if not cfg.PYTHONPING_ENABLED:
        return False
    try:
        from pythonping import ping
        resp = ping(ip, count=1, timeout=1)
        return resp.success()
    except Exception:
        return False


@blp.route("/<string:device_id>/status")
class DeviceStatus(MethodView):
    # PUBLIC_INTERFACE
    def get(self, device_id: str):
        """Get device online/offline status."""
        try:
            oid = ObjectId(device_id)
        except Exception:
            return jsonify({"error_code": "INVALID_ID", "message": "Invalid device ID"}), 400

        devices_col, _ = get_db()
        doc = devices_col.find_one({"_id": oid})
        if not doc:
            return jsonify({"error_code": "NOT_FOUND", "message": "Device not found"}), 404

        ip = doc.get("ip_address")
        online = _ping(ip)
        status_payload = {
            "id": str(doc["_id"]),
            "status": "online" if online else "offline",
            "last_checked": datetime.utcnow(),
        }
        return DeviceStatusSchema().dump(status_payload), 200
