"""
Business rules engine – applies voice-optimised transformations to data
before it is returned to the client.

Rules applied:
  1. Limit results to MAX_RESULTS (voice-friendly cap)
  2. Priority sorting (high → medium → low for tickets)
  3. Recency sorting (most recent first)
  4. Smart summarisation for large result sets
"""

import math, logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def apply_voice_limits(
    data: List[Dict[str, Any]],
    *,
    limit: int | None = None,
    page: int = 1,
) -> Dict[str, Any]:
    """
    Paginate and cap results for voice-friendly output.
    Returns dict with items, total, page, total_pages.
    """
    effective_limit = limit or settings.MAX_RESULTS
    total = len(data)
    total_pages = max(1, math.ceil(total / effective_limit))
    start = (page - 1) * effective_limit
    items = data[start : start + effective_limit]

    return {
        "items": items,
        "total": total,
        "page": page,
        "total_pages": total_pages,
    }


def sort_by_priority(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort records with a 'priority' field: high > medium > low."""
    if not data or "priority" not in data[0]:
        return data
    return sorted(data, key=lambda r: PRIORITY_ORDER.get(r.get("priority", ""), 99))


def sort_by_recency(data: List[Dict[str, Any]], date_field: str = "created_at") -> List[Dict[str, Any]]:
    """Sort records by a date field, most recent first."""
    if not data or date_field not in data[0]:
        return data
    return sorted(data, key=lambda r: r.get(date_field, ""), reverse=True)


def generate_context_string(
    source: str,
    total: int,
    returned: int,
    *,
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a human-readable context line, e.g.
    'Showing 5 of 47 CRM customers (filtered by status=active)'.
    """
    parts = [f"Showing {returned} of {total} {source} records"]
    if filters:
        active_filters = {k: v for k, v in filters.items() if v is not None}
        if active_filters:
            fstr = ", ".join(f"{k}={v}" for k, v in active_filters.items())
            parts.append(f"(filtered by {fstr})")
    return " ".join(parts)


def freshness_label() -> str:
    """Return a human-readable data freshness string."""
    return f"Data as of {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
