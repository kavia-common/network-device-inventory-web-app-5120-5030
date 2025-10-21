import os
from typing import Optional

from pymongo import ASCENDING, TEXT, MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError, ConnectionFailure, PyMongoError
from pymongo.database import Database

_client: Optional[MongoClient] = None


def mongo_client() -> MongoClient:
    """
    Create or return a singleton MongoClient using environment configuration.

    Environment variables:
    - MONGODB_URI: connection string (required for actual DB ops)
    - MONGODB_CONNECT_TIMEOUT_MS (default 2000)
    - MONGODB_SOCKET_TIMEOUT_MS (default 20000)
    - MONGODB_MAX_POOL_SIZE (default 100)
    - MONGODB_TLS (default false)
    - MONGODB_TLS_CA_FILE (optional)
    """
    global _client
    if _client is not None:
        return _client

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ConfigurationError("MONGODB_URI is not configured")

    _client = MongoClient(
        uri,
        serverSelectionTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "2000")),
        socketTimeoutMS=int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "20000")),
        maxPoolSize=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
        tls=os.getenv("MONGODB_TLS", "false").lower() == "true",
        tlsCAFile=os.getenv("MONGODB_TLS_CA_FILE") or None,
    )
    return _client


def get_db() -> Optional[Database]:
    """
    Return the configured database handle if environment is set; otherwise None.
    """
    db_name = os.getenv("MONGODB_DB_NAME")
    if not db_name:
        return None
    client = mongo_client()
    return client[db_name]


def get_devices_collection() -> Collection:
    """
    Get the devices collection from the configured database.

    Environment:
    - MONGODB_COLLECTION_DEVICES (default 'devices')
    """
    db = get_db()
    if db is None:
        raise ConfigurationError("MONGODB_DB_NAME is not configured")
    collection_name = os.getenv("MONGODB_COLLECTION_DEVICES", "devices")
    return db[collection_name]


def init_mongo_indexes() -> None:
    """
    Ensure indexes exist for devices collection:
    - ipAddress unique
    - deviceName text (fallback to regular ASCENDING index if text not desired)
    """
    try:
        col = get_devices_collection()
        # Unique index on ipAddress
        col.create_index([("ipAddress", ASCENDING)], unique=True, name="uniq_ip")
        # Text index for deviceName for search convenience (or use ASCENDING)
        try:
            col.create_index([("deviceName", TEXT)], name="idx_deviceName_text")
        except Exception:
            # Fallback to non-text index in environments where text index is restricted
            col.create_index([("deviceName", ASCENDING)], name="idx_deviceName")
    except (ConfigurationError, ConnectionFailure, PyMongoError):
        # Ignore at startup if DB isn't available; routes handle errors explicitly
        pass
