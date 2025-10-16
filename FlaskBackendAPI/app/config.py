import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv

# Load .env from project root or container root
load_dotenv()


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    # Server
    FLASK_RUN_PORT: int = int(os.getenv("FLASK_RUN_PORT", "3001"))
    FLASK_RUN_HOST: str = os.getenv("FLASK_RUN_HOST", "0.0.0.0")

    # Security
    API_KEY: Optional[str] = os.getenv("API_KEY")
    RATE_LIMIT: Optional[str] = os.getenv("RATE_LIMIT")

    # Mongo
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "device_inventory")
    MONGODB_COLLECTION_DEVICES: str = os.getenv("MONGODB_COLLECTION_DEVICES", "devices")
    MONGODB_COLLECTION_LOGS: str = os.getenv("MONGODB_COLLECTION_LOGS", "logs")

    # Features
    PYTHONPING_ENABLED: bool = os.getenv("PYTHONPING_ENABLED", "false").lower() in ("1", "true", "yes")
    CORS_ALLOWED_ORIGINS: List[str] = None  # populated below

    def __post_init__(self):
        cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
        if cors_origins.strip() == "*":
            self.CORS_ALLOWED_ORIGINS = ["*"]
        else:
            self.CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(",") if o.strip()]


# PUBLIC_INTERFACE
def get_config() -> AppConfig:
    """Return loaded application configuration."""
    return AppConfig()
