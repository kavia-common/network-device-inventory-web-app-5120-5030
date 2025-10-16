"""Routes package initialization for Flask Backend API.

Exports route blueprints for easy imports and registration.
"""

from .health import blp as health_blp  # noqa: F401
from .devices import blp as devices_blp  # noqa: F401
from .status import blp as status_blp  # noqa: F401
