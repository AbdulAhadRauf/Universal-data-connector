"""
CRM data connector – reads customer data from JSON and supports
filtering by status, search by name/email, sorting and pagination.
"""

import json, logging, math
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.connectors.base import BaseConnector
from app.models.common import DataType

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/customers.json")


class CRMConnector(BaseConnector):

    source_name = "CRM"
    data_type = DataType.TABULAR

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #
    def _load(self) -> List[Dict[str, Any]]:
        with open(DATA_PATH) as f:
            return json.load(f)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
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

        # ── filter by status ────────────────────────────────────────
        status = filters.get("status")
        if status:
            data = [r for r in data if r["status"] == status]

        # ── sort ────────────────────────────────────────────────────
        if sort_by and data and sort_by in data[0]:
            data.sort(key=lambda r: r.get(sort_by, ""), reverse=(sort_order == "desc"))

        total = len(data)
        start = (page - 1) * limit
        items = data[start : start + limit]

        logger.info("CRM fetch: %d total, returning page %d (%d items)", total, page, len(items))
        return {"items": items, "total": total}

    def search(self, query: str, *, limit: int = 10) -> Dict[str, Any]:
        q = query.lower()
        data = self._load()
        hits = [
            r for r in data
            if q in r["name"].lower() or q in r["email"].lower()
        ]
        return {"items": hits[:limit], "total": len(hits)}

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        for r in self._load():
            if r["customer_id"] == record_id:
                return r
        return None

    # ------------------------------------------------------------------ #
    #  LLM tool definitions                                                #
    # ------------------------------------------------------------------ #
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_customers",
                    "description": (
                        "Search CRM customers by name or email. "
                        "Use this when the user asks about a specific customer."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Name or email to search for",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results (default 5)",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_customers",
                    "description": (
                        "Retrieve a list of CRM customers. Can filter by status "
                        "(active/inactive) and paginate. Use when user asks about "
                        "customers, how many customers there are, or wants to see "
                        "customer data."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["active", "inactive"],
                                "description": "Filter by customer status",
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
                    "name": "get_customer_by_id",
                    "description": "Get details of a specific customer by their ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "integer",
                                "description": "The customer ID",
                            },
                        },
                        "required": ["customer_id"],
                    },
                },
            },
        ]
