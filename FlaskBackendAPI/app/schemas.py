import re
from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from marshmallow import Schema, fields, validates, ValidationError, post_dump


# Helpers
ipv4_regex = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
mac_regex = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


class ObjectIdField(fields.Field):
    """Custom field to serialize/deserialize MongoDB ObjectId."""

    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str):
            return value
        return None

    def _deserialize(self, value: Any, attr: str, data: Any, **kwargs):
        try:
            return ObjectId(value)
        except Exception as e:
            raise ValidationError("Invalid ObjectId") from e


class DeviceSchema(Schema):
    """Schema for a network device."""

    id = ObjectIdField(attribute="_id", dump_only=True, metadata={"description": "Unique device identifier"})
    name = fields.String(required=True, metadata={"description": "Device name"})
    ip_address = fields.String(required=True, metadata={"description": "Device IP address"})
    mac_address = fields.String(required=True, metadata={"description": "Device MAC address"})
    location = fields.String(required=True, metadata={"description": "Physical location"})
    type = fields.String(required=True, data_key="type", attribute="device_type",
                         metadata={"description": "Device type (router, switch, server, etc.)"})

    @validates("ip_address")
    def validate_ip(self, value: str):
        if not ipv4_regex.match(value):
            raise ValidationError("Invalid IPv4 address format")

        # Ensure each octet <= 255
        parts = value.split(".")
        if any(int(p) > 255 for p in parts):
            raise ValidationError("IPv4 octets must be between 0 and 255")

    @validates("mac_address")
    def validate_mac(self, value: str):
        if not mac_regex.match(value):
            raise ValidationError("Invalid MAC address format (expected XX:XX:XX:XX:XX:XX)")

    @post_dump
    def ensure_id_str(self, data: Dict[str, Any], many: bool, **kwargs):
        # Ensure id field is string for clients
        if "id" in data and data["id"] is not None:
            data["id"] = str(data["id"])
        return data


class DeviceStatusSchema(Schema):
    """Schema representing device online/offline status."""

    id = fields.String(required=True, metadata={"description": "Device ID"})
    status = fields.String(required=True, metadata={"description": "Device status: online or offline"})
    last_checked = fields.DateTime(required=True, metadata={"description": "Timestamp of last status check"})

    @post_dump
    def isoformat_last_checked(self, data: Dict[str, Any], many: bool, **kwargs):
        ts = data.get("last_checked")
        if isinstance(ts, datetime):
            data["last_checked"] = ts.isoformat()
        return data


class ErrorResponseSchema(Schema):
    """Standard error response payload."""

    error_code = fields.String(required=True)
    message = fields.String(required=True)
    details = fields.String(allow_none=True)
