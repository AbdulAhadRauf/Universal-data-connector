from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from app.services.business_rules import paginate_data


class AnalyticsConnector(BaseConnector):
    """
    Analytics Connector
    Supports:
      - metric filter
      - date range filter
      - pagination
      - freshness
    """

    def fetch(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        with open(Path("data/analytics.json"), encoding="utf-8") as f:
            raw = json.load(f)

        # Handling file shape
        if isinstance(raw, list):
            metrics: List[Dict[str, Any]] = raw
            as_of = datetime.now(timezone.utc)
        else:
            metrics = raw.get("data") or []
            as_of_str = raw.get("as_of")
            as_of = datetime.fromisoformat(as_of_str) if as_of_str else datetime.now(timezone.utc)

        filters = filters or {}

        # -------------------
        # Metric filter
        # -------------------
        metric_name = filters.get("metric")
        if metric_name:
            metrics = [
                m for m in metrics
                if str(m.get("metric", "")).lower() == str(metric_name).lower()
            ]

        # -------------------
        # Generic search
        # -------------------
        if query:
            q = query.strip().lower()
            metrics = [
                m for m in metrics
                if q in str(m.get("metric", "")).lower()
            ]

        # -------------------
        # Date range filter
        # -------------------
        if start_time or end_time:
            filtered = []
            for m in metrics:
                date_str = m.get("date")
                if not date_str:
                    continue

                date_dt = datetime.fromisoformat(date_str)

                if start_time and date_dt < start_time:
                    continue
                if end_time and date_dt > end_time:
                    continue

                filtered.append(m)

            metrics = filtered

        # -------------------
        # Sort newest first
        # -------------------
        metrics = sorted(
            metrics,
            key=lambda m: str(m.get("date") or ""),
            reverse=True,
        )

        # -------------------
        # Pagination
        # -------------------
        page_data, next_cursor, total = paginate_data(metrics, cursor=cursor, limit=limit)

        return {
            "items": page_data,
            "total": total,
            "next_cursor": next_cursor,
            "as_of": as_of,
            "available_filters": {
                "metric": "daily_active_users"
            },
        }
