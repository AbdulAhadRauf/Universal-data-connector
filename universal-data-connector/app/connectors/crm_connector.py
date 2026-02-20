from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from app.services.business_rules import paginate_data


class CRMConnector(BaseConnector):
    """
    CRM Connector (mock JSON file)

    IMPORTANT:
    This fetch() always returns a dict:
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
        with open(Path("data/customers.json"), encoding="utf-8") as f:
            raw = json.load(f)

        # customers.json may be list OR dict
        if isinstance(raw, list):
            customers: List[Dict[str, Any]] = raw
            as_of = datetime.now(timezone.utc)
        else:
            customers = raw.get("data") or raw.get("customers") or []
            as_of_str = raw.get("as_of")
            as_of = datetime.fromisoformat(as_of_str) if as_of_str else datetime.now(timezone.utc)

        filters = filters or {}

        # Filter: status
        status = filters.get("status")
        if status:
            customers = [
                c for c in customers
                if str(c.get("status", "")).lower() == str(status).lower()
            ]

        # Query: search name/email/id
        if query:
            q = query.strip().lower()
            customers = [
                c for c in customers
                if q in str(c.get("name", "")).lower()
                or q in str(c.get("email", "")).lower()
                or q in str(c.get("customer_id", "")).lower()
            ]

        # Sort newest first (best effort)
        customers = sorted(customers, key=lambda c: str(c.get("created_at") or ""), reverse=True)

        # Pagination
        page_data, next_cursor, total = paginate_data(customers, cursor=cursor, limit=limit)

        return {
            "items": page_data,
            "total": total,
            "next_cursor": next_cursor,
            "as_of": as_of,
            "available_filters": {"status": "active|inactive"},
        }
