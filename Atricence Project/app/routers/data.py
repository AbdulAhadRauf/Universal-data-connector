"""
Data access endpoints – provides a unified REST API for querying
CRM, Support, and Analytics data with voice-optimised responses.
Also includes a /tools/schema endpoint for LLM function definitions.
"""

import math, logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException

from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector
from app.services.business_rules import (
    sort_by_priority,
    sort_by_recency,
    generate_context_string,
    freshness_label,
)
from app.services.voice_optimizer import generate_voice_summary, generate_voice_hint
from app.services.data_identifier import identify_data_type
from app.models.common import DataResponse, Metadata
from app.services.llm_service import get_all_tool_definitions
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data"])

# ── Connector instances ────────────────────────────────────────────────
crm = CRMConnector()
support = SupportConnector()
analytics = AnalyticsConnector()


# ═══════════════════════════════════════════════════════════════════════
#  CRM
# ═══════════════════════════════════════════════════════════════════════

@router.get("/data/crm", response_model=DataResponse, summary="Query CRM customers")
def get_crm_data(
    status: Optional[str] = Query(None, description="active or inactive"),
    search: Optional[str] = Query(None, description="Search by name/email"),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    if search:
        result = crm.search(search, limit=limit)
    else:
        result = crm.fetch(limit=limit, page=page, status=status)

    items = result["items"]
    total = result["total"]
    total_pages = max(1, math.ceil(total / limit))
    data_type = identify_data_type(items)

    voice_summary = generate_voice_summary("CRM", items, total)
    voice_hint = generate_voice_hint("CRM", total, len(items))
    context = generate_context_string("CRM", total, len(items), filters={"status": status, "search": search})

    return DataResponse(
        data=items,
        metadata=Metadata(
            total_results=total,
            returned_results=len(items),
            page=page,
            total_pages=total_pages,
            data_type=data_type,
            data_freshness=freshness_label(),
            voice_hint=voice_hint or None,
            query_context=context,
        ),
        voice_summary=voice_summary,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Support Tickets
# ═══════════════════════════════════════════════════════════════════════

@router.get("/data/support", response_model=DataResponse, summary="Query support tickets")
def get_support_data(
    priority: Optional[str] = Query(None, description="high, medium, or low"),
    status: Optional[str] = Query(None, description="open or closed"),
    customer_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    result = support.fetch(
        limit=limit,
        page=page,
        priority=priority,
        status=status,
        customer_id=customer_id,
    )

    items = sort_by_priority(result["items"])
    total = result["total"]
    total_pages = max(1, math.ceil(total / limit))
    data_type = identify_data_type(items)

    voice_summary = generate_voice_summary("Support Tickets", items, total)
    voice_hint = generate_voice_hint("Support Tickets", total, len(items))
    context = generate_context_string(
        "Support Tickets", total, len(items),
        filters={"priority": priority, "status": status, "customer_id": customer_id},
    )

    return DataResponse(
        data=items,
        metadata=Metadata(
            total_results=total,
            returned_results=len(items),
            page=page,
            total_pages=total_pages,
            data_type=data_type,
            data_freshness=freshness_label(),
            voice_hint=voice_hint or None,
            query_context=context,
        ),
        voice_summary=voice_summary,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Analytics
# ═══════════════════════════════════════════════════════════════════════

@router.get("/data/analytics", response_model=DataResponse, summary="Query analytics metrics")
def get_analytics_data(
    metric: Optional[str] = Query(None, description="e.g. daily_active_users"),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    result = analytics.fetch(limit=limit, page=page, metric=metric, days=days)

    items = result["items"]
    total = result["total"]
    total_pages = max(1, math.ceil(total / limit))
    data_type = identify_data_type(items)

    voice_summary = generate_voice_summary("Analytics", items, total)
    voice_hint = generate_voice_hint("Analytics", total, len(items))

    return DataResponse(
        data=items,
        metadata=Metadata(
            total_results=total,
            returned_results=len(items),
            page=page,
            total_pages=total_pages,
            data_type=data_type,
            data_freshness=freshness_label(),
            voice_hint=voice_hint or None,
            query_context=f"Analytics: {metric or 'all metrics'}, last {days} days",
        ),
        voice_summary=voice_summary,
    )


@router.get("/data/analytics/summary", summary="Get analytics summary (voice-friendly)")
def get_analytics_summary(
    metric: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=365),
):
    summary_data = analytics.get_summary(metric=metric, days=days)
    voice_summary = generate_voice_summary("Analytics", [summary_data], 1)

    return {
        "data": summary_data,
        "metadata": {
            "data_freshness": freshness_label(),
            "query_context": f"Summary of {metric or 'all metrics'}, last {days} days",
        },
        "voice_summary": voice_summary,
    }


# ═══════════════════════════════════════════════════════════════════════
#  Generic source endpoint (backward compat)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/data/{source}", response_model=DataResponse, summary="Generic data query")
def get_data(
    source: str,
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    connector_map = {
        "crm": crm,
        "support": support,
        "analytics": analytics,
    }

    connector = connector_map.get(source)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Unknown data source: {source}")

    result = connector.fetch(limit=limit, page=page)
    items = result["items"]
    total = result["total"]
    total_pages = max(1, math.ceil(total / limit))
    data_type = identify_data_type(items)

    voice_summary = generate_voice_summary(connector.source_name, items, total)

    return DataResponse(
        data=items,
        metadata=Metadata(
            total_results=total,
            returned_results=len(items),
            page=page,
            total_pages=total_pages,
            data_type=data_type,
            data_freshness=freshness_label(),
            query_context=f"{connector.source_name} data, page {page}",
        ),
        voice_summary=voice_summary,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Tool Schema endpoint
# ═══════════════════════════════════════════════════════════════════════

@router.get("/tools/schema", summary="LLM function calling tool definitions")
def get_tool_schema():
    """Return all OpenAI-compatible tool/function definitions."""
    return {
        "tools": get_all_tool_definitions(),
        "description": (
            "These are the available tools for querying business data. "
            "Pass them as the 'tools' parameter in an OpenAI chat completion request."
        ),
    }
