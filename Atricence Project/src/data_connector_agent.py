"""
Data Connector Agent — LangGraph agent with business data tools.

Uses ChatGroq (Llama 4 Scout) and LangGraph to create an agent
that can query CRM, Support, and Analytics data through tool calling.
This follows the same pattern as simple_math_agent.py from
fastrtc-groq-voice-agent-main.
"""

import json, sys, os
from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from loguru import logger
from langchain_core.tools import tool

from dotenv import load_dotenv
load_dotenv()

# ── Resolve data directory (relative to project root, not src/) ────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def _safe_int(value: str, default: int) -> int:
    """Safely parse a string to int, returning default if empty or invalid."""
    if not value or not value.strip():
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════════════
#  Data loading helpers
# ═══════════════════════════════════════════════════════════════════════

def _load_customers():
    with open(DATA_DIR / "customers.json") as f:
        return json.load(f)

def _load_tickets():
    with open(DATA_DIR / "support_tickets.json") as f:
        return json.load(f)

def _load_analytics():
    with open(DATA_DIR / "analytics.json") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════
#  CRM Tools
# ═══════════════════════════════════════════════════════════════════════

@tool
def search_customers(query: str, limit: str = "5") -> str:
    """Search CRM customers by name or email. Use when the user asks about a specific customer."""
    q = query.lower()
    lim = _safe_int(limit, 5)
    data = _load_customers()
    hits = [r for r in data if q in r["name"].lower() or q in r["email"].lower()]
    results = hits[:lim]
    total = len(hits)
    logger.info(f"🔍 CRM search '{query}': {total} hits, returning {len(results)}")
    return json.dumps({"items": results, "total": total, "showing": len(results)})


@tool
def get_customers(status: str = "", limit: str = "5") -> str:
    """Retrieve a list of CRM customers. Can filter by status (active/inactive). Use when user asks about customers or how many customers there are."""
    lim = _safe_int(limit, 5)
    data = _load_customers()
    if status:
        data = [r for r in data if r["status"] == status]
    total = len(data)
    items = data[:lim]
    active = sum(1 for r in data if r["status"] == "active")
    logger.info(f"👥 CRM fetch: {total} total, {active} active, returning {len(items)}")
    return json.dumps({"items": items, "total": total, "active_count": active, "showing": len(items)})


@tool
def get_customer_by_id(customer_id: str) -> str:
    """Get details of a specific customer by their ID."""
    cid = _safe_int(customer_id, 0)
    for r in _load_customers():
        if r["customer_id"] == cid:
            logger.info(f"👤 Found customer {cid}: {r['name']}")
            return json.dumps(r)
    logger.info(f"👤 Customer {cid} not found")
    return json.dumps({"error": f"Customer {cid} not found"})


# ═══════════════════════════════════════════════════════════════════════
#  Support Ticket Tools
# ═══════════════════════════════════════════════════════════════════════

@tool
def get_support_tickets(priority: str = "", status: str = "", customer_id: str = "", limit: str = "5") -> str:
    """Retrieve support tickets. Can filter by priority (high/medium/low), status (open/closed), and customer_id. Use when user asks about tickets, issues, or support requests."""
    lim = _safe_int(limit, 5)
    data = _load_tickets()

    if priority:
        data = [r for r in data if r["priority"] == priority]
    if status:
        data = [r for r in data if r["status"] == status]
    if customer_id:
        cid = _safe_int(customer_id, 0)
        data = [r for r in data if r["customer_id"] == cid]

    # Sort by priority: high > medium > low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    data.sort(key=lambda r: priority_order.get(r.get("priority", ""), 99))

    total = len(data)
    items = data[:lim]
    open_count = sum(1 for r in data if r["status"] == "open")
    high_count = sum(1 for r in data if r["priority"] == "high")
    logger.info(f"🎫 Support fetch: {total} total, {open_count} open, {high_count} high, returning {len(items)}")
    return json.dumps({
        "items": items, "total": total, "showing": len(items),
        "open_count": open_count, "high_priority_count": high_count
    })


@tool
def get_ticket_by_id(ticket_id: str) -> str:
    """Get details of a specific support ticket by ID."""
    tid = _safe_int(ticket_id, 0)
    for r in _load_tickets():
        if r["ticket_id"] == tid:
            logger.info(f"🎫 Found ticket {tid}: {r['subject']}")
            return json.dumps(r)
    logger.info(f"🎫 Ticket {tid} not found")
    return json.dumps({"error": f"Ticket {tid} not found"})


# ═══════════════════════════════════════════════════════════════════════
#  Analytics Tools
# ═══════════════════════════════════════════════════════════════════════

@tool
def get_analytics(metric: str = "", days: str = "7", limit: str = "10") -> str:
    """Retrieve analytics metrics. Can filter by metric name (e.g. 'daily_active_users') and time range (days). Use when user asks about metrics, stats, DAU, trends, or analytics."""
    from datetime import datetime, timedelta, timezone

    lim = _safe_int(limit, 10)
    d = _safe_int(days, 7)
    data = _load_analytics()

    if metric:
        data = [r for r in data if r["metric"] == metric]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=d)).date().isoformat()
    data = [r for r in data if r["date"] >= cutoff]
    data.sort(key=lambda r: r["date"], reverse=True)

    total = len(data)
    items = data[:lim]
    logger.info(f"📊 Analytics fetch: {total} points in last {d} days, returning {len(items)}")
    return json.dumps({"items": items, "total": total, "showing": len(items)})


@tool
def get_analytics_summary(metric: str = "", days: str = "7") -> str:
    """Get a summarized overview of analytics metrics including average, min, max, trend. Best for voice conversations — gives a concise spoken summary instead of raw data."""
    from datetime import datetime, timedelta, timezone
    from statistics import mean

    d = _safe_int(days, 7)
    data = _load_analytics()

    if metric:
        data = [r for r in data if r["metric"] == metric]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=d)).date().isoformat()
    data = [r for r in data if r["date"] >= cutoff]
    data.sort(key=lambda r: r["date"], reverse=True)

    if not data:
        return json.dumps({"summary": "No data available for the requested period."})

    values = [r["value"] for r in data]
    latest = data[0]

    # Simple trend: compare first half vs second half
    mid = len(values) // 2
    first_half_avg = mean(values[:mid]) if mid else 0
    second_half_avg = mean(values[mid:]) if values[mid:] else 0
    trend = "up" if second_half_avg > first_half_avg else "down" if second_half_avg < first_half_avg else "flat"

    summary = {
        "metric": metric or "all",
        "period_days": d,
        "data_points": len(values),
        "average": round(mean(values), 1),
        "min": min(values),
        "max": max(values),
        "latest_value": latest.get("value"),
        "latest_date": latest.get("date"),
        "trend": trend,
    }
    logger.info(f"📊 Analytics summary: avg={summary['average']}, trend={trend}")
    return json.dumps(summary)


# ═══════════════════════════════════════════════════════════════════════
#  LangGraph Agent (same pattern as simple_math_agent.py)
# ═══════════════════════════════════════════════════════════════════════

model = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens=512,
)

tools = [
    search_customers,
    get_customers,
    get_customer_by_id,
    get_support_tickets,
    get_ticket_by_id,
    get_analytics,
    get_analytics_summary,
]

memory = InMemorySaver()

agent = create_react_agent(
    model=model,
    tools=tools,
    checkpointer=memory,
    prompt=(
        "You are a friendly, concise AI assistant for a SaaS company. "
        "You help users query their business data (CRM customers, support tickets, "
        "and analytics) through voice conversations.\n\n"
        "Guidelines:\n"
        "• Keep responses SHORT and conversational — the user is listening via voice.\n"
        "• Summarise data rather than reading out raw records wherever possible.\n"
        "• When presenting numbers, round them and say 'about' or 'around'.\n"
        "• If there are many results, highlight the most important ones and mention "
        "how many more exist.\n"
        "• Always mention the data source you used (CRM, Support, Analytics).\n"
        "• If a query is ambiguous, ask a brief clarifying question.\n"
        "• Use natural spoken language — avoid bullet-point or markdown formatting.\n"
    ),
)

agent_config = {"configurable": {"thread_id": "default_user"}}
