"""
Analytics / metrics connector.
Supports filtering by metric name, date range, and aggregation.
"""

import json, logging
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from statistics import mean

from app.connectors.base import BaseConnector
from app.models.common import DataType

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/analytics.json")


class AnalyticsConnector(BaseConnector):

    source_name = "Analytics"
    data_type = DataType.TIME_SERIES

    def _load(self) -> List[Dict[str, Any]]:
        with open(DATA_PATH) as f:
            return json.load(f)

    def fetch(
        self,
        *,
        limit: int = 10,
        page: int = 1,
        sort_by: Optional[str] = "date",
        sort_order: str = "desc",
        **filters: Any,
    ) -> Dict[str, Any]:
        data = self._load()

        # ── filter by metric name ───────────────────────────────────
        metric = filters.get("metric")
        if metric:
            data = [r for r in data if r["metric"] == metric]

        # ── filter by date range (days back from today) ─────────────
        days = filters.get("days")
        if days:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=int(days))).date().isoformat()
            data = [r for r in data if r["date"] >= cutoff]

        # ── sort ────────────────────────────────────────────────────
        if sort_by and data and sort_by in data[0]:
            data.sort(key=lambda r: r.get(sort_by, ""), reverse=(sort_order == "desc"))

        total = len(data)
        start = (page - 1) * limit
        items = data[start : start + limit]

        logger.info("Analytics fetch: %d total, returning page %d (%d items)", total, page, len(items))
        return {"items": items, "total": total}

    def search(self, query: str, *, limit: int = 10) -> Dict[str, Any]:
        q = query.lower()
        data = self._load()
        hits = [r for r in data if q in r["metric"].lower()]
        return {"items": hits[:limit], "total": len(hits)}

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Analytics doesn't have a single-record ID; return None."""
        return None

    def get_summary(self, *, metric: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """
        Aggregate analytics into a voice-friendly summary.
        Returns average, min, max, latest value, and trend.
        """
        result = self.fetch(limit=999, metric=metric, days=days)
        items = result["items"]
        if not items:
            return {"summary": "No data available for the requested period."}

        values = [r["value"] for r in items]
        latest = items[0] if items else {}

        # simple trend: compare first half vs second half
        mid = len(values) // 2
        first_half_avg = mean(values[:mid]) if mid else 0
        second_half_avg = mean(values[mid:]) if values[mid:] else 0
        trend = "up" if second_half_avg > first_half_avg else "down" if second_half_avg < first_half_avg else "flat"

        return {
            "metric": metric or "all",
            "period_days": days,
            "data_points": len(values),
            "average": round(mean(values), 1),
            "min": min(values),
            "max": max(values),
            "latest_value": latest.get("value"),
            "latest_date": latest.get("date"),
            "trend": trend,
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_analytics",
                    "description": (
                        "Retrieve analytics metrics. Can filter by metric name "
                        "(e.g. 'daily_active_users') and time range (days). "
                        "Use when user asks about metrics, stats, DAU, trends, or analytics."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "Metric name, e.g. 'daily_active_users'",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back (default 7)",
                                "default": 7,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max data points to return (default 10)",
                                "default": 10,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_analytics_summary",
                    "description": (
                        "Get a summarized overview of analytics metrics including "
                        "average, min, max, trend. Best for voice conversations — "
                        "gives a concise spoken summary instead of raw data."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "Metric name, e.g. 'daily_active_users'",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back (default 7)",
                                "default": 7,
                            },
                        },
                        "required": [],
                    },
                },
            },
        ]
