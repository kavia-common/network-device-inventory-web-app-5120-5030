import json
import logging
import queue
import threading
import time
from datetime import datetime
from typing import Dict, Generator, List, Optional

from flask import Blueprint, Response, current_app, stream_with_context

logger = logging.getLogger(__name__)

sse_bp = Blueprint("sse", __name__)

# Thread-safe list of subscriber queues
_subscribers_lock = threading.Lock()
_subscribers: List[queue.Queue] = []


def _add_subscriber() -> queue.Queue:
    """Add a new subscriber queue and return it."""
    q: queue.Queue = queue.Queue()
    with _subscribers_lock:
        _subscribers.append(q)
        logger.debug("SSE subscriber added; total=%d", len(_subscribers))
    return q


def _remove_subscriber(q: queue.Queue) -> None:
    """Remove a subscriber queue."""
    with _subscribers_lock:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass
        logger.debug("SSE subscriber removed; total=%d", len(_subscribers))


# PUBLIC_INTERFACE
def sse_publish(event_dict: Dict) -> None:
    """Publish an event to all current SSE subscribers."""
    payload = json.dumps(event_dict)
    with _subscribers_lock:
        targets = list(_subscribers)
    # Non-blocking put with timeout so a slow client doesn't block publisher
    for q in targets:
        try:
            q.put_nowait(payload)
        except Exception:
            # If queue is full or any unexpected issue, best-effort skip
            logger.debug("Skipping subscriber due to full queue or error.")


def _event_stream(q: queue.Queue) -> Generator[str, None, None]:
    """Generator that yields events for a single subscriber until disconnect."""
    try:
        # Send a comment to establish the stream quickly
        yield ": connected {}\n\n".format(datetime.utcnow().isoformat())
        while True:
            try:
                # Use timeout to allow graceful stop checks periodically
                data: Optional[str] = q.get(timeout=10.0)
            except queue.Empty:
                # Keep connection alive with a heartbeat comment
                yield ": heartbeat {}\n\n".format(int(time.time()))
                continue

            if data is None:
                break

            # Send event: deviceStatus
            yield "event: deviceStatus\n"
            yield f"data: {data}\n\n"
    finally:
        _remove_subscriber(q)


@sse_bp.get("/devices/stream")
def devices_stream() -> Response:
    """
    Server-Sent Events stream for device status updates.

    Summary:
        GET /api/devices/stream
    Description:
        Opens a long-lived HTTP connection that streams events when device status
        pings complete. Events are sent with type 'deviceStatus' and JSON payload.
    Returns:
        text/event-stream response; clients should use EventSource on the frontend.
    """
    q = _add_subscriber()

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # Allow CORS as app-level CORS is configured for /api/*
        # Some proxies require explicit X-Accel-Buffering to disable buffering
        "X-Accel-Buffering": "no",
    }

    return Response(
        stream_with_context(_event_stream(q)),
        headers=headers,
        status=200,
        mimetype="text/event-stream",
    )
