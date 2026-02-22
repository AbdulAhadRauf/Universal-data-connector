"""
Support ticket connector – reads ticket data from JSON.
Supports filtering by priority, status, customer_id, sorting and pagination.
"""

import json, logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.connectors.base import BaseConnector
from app.models.common import DataType

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/support_tickets.json")


class SupportConnector(BaseConnector):

    source_name = "Support Tickets"
    data_type = DataType.TABULAR

    def _load(self) -> List[Dict[str, Any]]:
        with open(DATA_PATH) as f:
            return json.load(f)

    def fetch(
        self,
        *,
        limit: int = 10,
        page: int = 1,
        sort_by: Optional[str] = "created_at",
        sort_order: str = "desc",
        **filters: Any,
    ) -> Dict[str, Any]:
        data = self._load()

        # ── filters ─────────────────────────────────────────────────
        if filters.get("priority"):
            data = [r for r in data if r["priority"] == filters["priority"]]
        if filters.get("status"):
            data = [r for r in data if r["status"] == filters["status"]]
        if filters.get("customer_id"):
            cid = int(filters["customer_id"])
            data = [r for r in data if r["customer_id"] == cid]

        # ── sort ────────────────────────────────────────────────────
        if sort_by and data and sort_by in data[0]:
            data.sort(key=lambda r: r.get(sort_by, ""), reverse=(sort_order == "desc"))

        total = len(data)
        start = (page - 1) * limit
        items = data[start : start + limit]

        logger.info("Support fetch: %d total, returning page %d (%d items)", total, page, len(items))
        return {"items": items, "total": total}

    def search(self, query: str, *, limit: int = 10) -> Dict[str, Any]:
        q = query.lower()
        data = self._load()
        hits = [r for r in data if q in r["subject"].lower()]
        return {"items": hits[:limit], "total": len(hits)}

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        for r in self._load():
            if r["ticket_id"] == record_id:
                return r
        return None

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_support_tickets",
                    "description": (
                        "Retrieve support tickets. Can filter by priority "
                        "(high/medium/low), status (open/closed), and customer_id. "
                        "Use when user asks about tickets, issues, or support requests."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Filter by ticket priority",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["open", "closed"],
                                "description": "Filter by ticket status",
                            },
                            "customer_id": {
                                "type": "integer",
                                "description": "Filter by customer ID",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Results per page (default 5)",
                                "default": 5,
                            },
                            "page": {
                                "type": "integer",
                                "description": "Page number (default 1)",
                                "default": 1,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_ticket_by_id",
                    "description": "Get details of a specific support ticket by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "integer",
                                "description": "The ticket ID",
                            },
                        },
                        "required": ["ticket_id"],
                    },
                },
            },
        ]
