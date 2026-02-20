from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from app.services.business_rules import paginate_data


class SupportConnector(BaseConnector):
    """
    Support Ticket Connector
    Returns dict:
      {
        "items": [...],
        "total": int,
        "next_cursor": str|None,
        "as_of": datetime,
        "available_filters": {...}
      }
    """

    def fetch(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        with open(Path("data/support_tickets.json"), encoding="utf-8") as f:
            raw = json.load(f)

        # JSON might be list OR dict
        if isinstance(raw, list):
            tickets: List[Dict[str, Any]] = raw
            as_of = datetime.now(timezone.utc)
        else:
            tickets = raw.get("data") or raw.get("tickets") or []
            as_of_str = raw.get("as_of")
            as_of = datetime.fromisoformat(as_of_str) if as_of_str else datetime.now(timezone.utc)

        filters = filters or {}

        # Filter: status
        status = filters.get("status")
        if status:
            tickets = [
                t for t in tickets
                if str(t.get("status", "")).lower() == str(status).lower()
            ]

        # Filter: priority
        priority = filters.get("priority")
        if priority:
            tickets = [
                t for t in tickets
                if str(t.get("priority", "")).lower() == str(priority).lower()
            ]

        # Query search (title/description/id)
        if query:
            q = query.strip().lower()
            tickets = [
                t for t in tickets
                if q in str(t.get("title", "")).lower()
                or q in str(t.get("description", "")).lower()
                or q in str(t.get("ticket_id", "")).lower()
            ]

        # Sort newest first (by created_at if present)
        tickets = sorted(tickets, key=lambda t: str(t.get("created_at") or ""), reverse=True)

        # Pagination
        page_data, next_cursor, total = paginate_data(tickets, cursor=cursor, limit=limit)

        return {
            "items": page_data,
            "total": total,
            "next_cursor": next_cursor,
            "as_of": as_of,
            "available_filters": {
                "status": "open|closed|pending",
                "priority": "low|medium|high"
            },
        }
