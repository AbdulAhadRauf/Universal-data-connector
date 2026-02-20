from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, HTTPException

from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector

from app.services.voice_optimizer import summarize_if_large, generate_voice_highlights
from app.services.data_identifier import identify_data_type
from app.models.common import DataResponse, Metadata, QueryRequest

router = APIRouter()


def _get_connector(source: str):
    connector_map = {
        "crm": CRMConnector(),
        "support": SupportConnector(),
        "analytics": AnalyticsConnector(),
    }
    return connector_map.get(source)


# ----------------------------
# GET /data/{source} (kept)
# ----------------------------
@router.get("/data/{source}", response_model=DataResponse)
def get_data(
    source: str,
    limit: int = Query(10, ge=1, le=100),
    cursor: str | None = Query(default=None),
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    metric: str | None = Query(default=None),
):
    connector = _get_connector(source)
    if not connector:
        return DataResponse(
            data=[],
            metadata=Metadata(
                total_results=0,
                returned_results=0,
                data_freshness="unknown",
            ),
        )

    filters: Dict[str, Any] = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if metric:
        filters["metric"] = metric

    result = connector.fetch(query=q, filters=filters, cursor=cursor, limit=limit)

    items = result["items"]
    total = result["total"]
    as_of = result["as_of"]
    next_cursor = result.get("next_cursor")

    optimized = summarize_if_large(items)

    freshness_text = f"Data as of {as_of.isoformat()}"
    if next_cursor:
        freshness_text += f" | next_cursor={next_cursor}"

    metadata = Metadata(
        total_results=total,
        returned_results=len(optimized),
        data_freshness=freshness_text,
    )

    return DataResponse(data=optimized, metadata=metadata)


# ----------------------------
# POST /v1/query
# ----------------------------
@router.post("/v1/query")
def universal_query(req: QueryRequest):
    connector = _get_connector(req.source.value)
    if not connector:
        raise HTTPException(status_code=400, detail="Unknown source")

    # default voice limit
    limit = req.limit or (10 if req.mode.value == "voice" else 50)

    result = connector.fetch(
        query=req.query,
        filters=req.filters,
        cursor=req.cursor,
        limit=limit,
        start_time=req.start_time,
        end_time=req.end_time,
    )

    items = result["items"]
    total = result["total"]
    as_of = result["as_of"]
    next_cursor = result.get("next_cursor")

    data_type = identify_data_type(items)

    # freshness + staleness
    now = datetime.now(timezone.utc)
    age_seconds = int((now - as_of).total_seconds())
    stale_after_seconds = 7200
    stale = age_seconds > stale_after_seconds

    # voice optimization
    payload_items = items
    summary = f"Showing {len(items)} of {total} results."
    highlights = []

    if req.mode.value == "voice":
        payload_items = summarize_if_large(items)
        highlights = generate_voice_highlights(items, req.source.value)

    return {
        "source": req.source.value,
        "mode": req.mode.value,
        "data_type": data_type,
        "freshness": {
            "as_of": as_of.isoformat(),
            "age_seconds": age_seconds,
            "stale": stale,
            "stale_after_seconds": stale_after_seconds,
        },
        "page": {
            "returned": len(items),
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "message": summary,
        },
        "summary": summary,
        "highlights": highlights,
        "items": payload_items,
        "available_filters": result.get("available_filters", {}),
        "suggested_followups": [
            "Refine filters",
            "Ask for next page using next_cursor",
            "Switch to full mode for more fields",
        ],
    }
