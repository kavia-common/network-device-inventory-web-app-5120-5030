import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

ALLOWED_DEVICE_TYPES = {"router", "switch", "server", "other"}
IPV4_REGEX = re.compile(
    r"^((25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(25[0-5]|2[0-4]\d|1?\d?\d)$"
)

# Basic max lengths
MAX_LEN = {
    "deviceName": 200,
    "ipAddress": 50,
    "macAddress": 50,
    "location": 200,
    "deviceType": 50,
    "notes": 2000,
    "status": 50,
}

ALLOWED_FIELDS = {
    "deviceName",
    "ipAddress",
    "macAddress",
    "location",
    "deviceType",
    "notes",
    "status",
}


def _truncate(value: str, field: str) -> str:
    limit = MAX_LEN.get(field)
    if limit and isinstance(value, str) and len(value) > limit:
        return value[:limit]
    return value


def validate_ipv4(ip: str) -> bool:
    return bool(IPV4_REGEX.match(ip))


def normalize_device_type(value: str) -> str:
    v = (value or "").strip().lower()
    return v if v in ALLOWED_DEVICE_TYPES else "other"


def sanitize_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Remove unknown fields and truncate long strings.
    Returns (sanitized_payload, unknown_fields_detected)
    """
    unknown = [k for k in payload.keys() if k not in ALLOWED_FIELDS]
    sanitized: Dict[str, Any] = {}
    for k in ALLOWED_FIELDS:
        if k in payload:
            val = payload[k]
            if isinstance(val, str):
                val = _truncate(val, k)
            sanitized[k] = val
    return sanitized, unknown


def validate_create(payload: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate a create request.
    Returns (ok, errors, cleaned_payload)
    """
    cleaned, unknown = sanitize_payload(payload)
    errors: List[str] = []

    # Required
    if not cleaned.get("deviceName"):
        errors.append("deviceName is required")
    if not cleaned.get("ipAddress"):
        errors.append("ipAddress is required")

    # IPv4
    if cleaned.get("ipAddress") and not validate_ipv4(str(cleaned["ipAddress"])):
        errors.append("ipAddress must be valid IPv4")

    # deviceType normalization
    if "deviceType" in cleaned:
        cleaned["deviceType"] = normalize_device_type(str(cleaned["deviceType"]))
    else:
        cleaned["deviceType"] = "other"

    # Unknown fields warning (treated as error)
    if unknown:
        errors.append(f"Unknown fields: {', '.join(unknown)}")

    # Timestamps
    now = datetime.utcnow().isoformat()
    cleaned["createdAt"] = now
    cleaned["updatedAt"] = now

    return len(errors) == 0, errors, cleaned


def validate_update(payload: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate an update request (partial allowed).
    Returns (ok, errors, cleaned_payload)
    """
    cleaned, unknown = sanitize_payload(payload)
    errors: List[str] = []

    if "ipAddress" in cleaned and not validate_ipv4(str(cleaned["ipAddress"])):
        errors.append("ipAddress must be valid IPv4")

    if "deviceType" in cleaned:
        cleaned["deviceType"] = normalize_device_type(str(cleaned["deviceType"]))

    if unknown:
        errors.append(f"Unknown fields: {', '.join(unknown)}")

    cleaned["updatedAt"] = datetime.utcnow().isoformat()

    return len(errors) == 0, errors, cleaned
