from __future__ import annotations

import base64
import json
from typing import List, Dict, Optional

from app.config import settings


def apply_voice_limits(data: List[Dict], requested_limit: Optional[int] = None) -> List[Dict]:
    """
    Backwards-compatible voice limiter (older code may import this).
    """
    limit = requested_limit or settings.MAX_RESULTS
    return data[:limit]


def encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": offset}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    padded = cursor + "=" * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return int(json.loads(raw.decode("utf-8")).get("offset", 0))


def paginate_data(data: List[Dict], cursor: Optional[str], limit: int):
    """
    Returns: (page_data, next_cursor, total)
    """
    total = len(data)
    offset = decode_cursor(cursor)

    limit = int(limit)
    if limit <= 0:
        limit = settings.MAX_RESULTS

    page_data = data[offset: offset + limit]

    next_offset = offset + len(page_data)
    next_cursor = encode_cursor(next_offset) if next_offset < total else None

    return page_data, next_cursor, total
