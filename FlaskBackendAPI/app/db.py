from typing import Tuple
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from .config import get_config


class Database:
    """MongoDB database manager for the app."""

    def __init__(self):
        cfg = get_config()
        self.client = MongoClient(cfg.MONGODB_URI)
        self.db = self.client[cfg.MONGODB_DB_NAME]
        self.devices: Collection = self.db[cfg.MONGODB_COLLECTION_DEVICES]
        self.logs: Collection = self.db[cfg.MONGODB_COLLECTION_LOGS]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for performance and constraints."""
        try:
            # Unique mac_address
            self.devices.create_index([("mac_address", ASCENDING)], unique=True, name="uniq_mac")
            # Lookup indexes
            self.devices.create_index([("ip_address", ASCENDING)], name="idx_ip")
            self.devices.create_index([("device_type", ASCENDING)], name="idx_type")
            self.devices.create_index([("location", ASCENDING), ("device_type", ASCENDING)], name="idx_location_type")
            # Logs indexes
            self.logs.create_index([("device_id", ASCENDING)], name="idx_log_device")
            self.logs.create_index([("timestamp", ASCENDING)], name="idx_log_ts")
        except PyMongoError:
            # Avoid hard crash on startup; routes will still handle errors.
            pass


_db_instance: Database = None


# PUBLIC_INTERFACE
def get_db() -> Tuple[Collection, Collection]:
    """Get Mongo collections (devices, logs) as a tuple."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance.devices, _db_instance.logs
