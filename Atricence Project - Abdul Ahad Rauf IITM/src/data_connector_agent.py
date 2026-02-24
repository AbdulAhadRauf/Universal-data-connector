"""
Data Connector Agent — LangGraph agent with business data tools.
All data access is delegated to app/connectors/.
"""

import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from loguru import logger
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector
from app.config import settings

crm = CRMConnector()
support = SupportConnector()
analytics = AnalyticsConnector()


def _int(value: str, default: int) -> int:
    try:
        return int(value) if value and value.strip() else default
    except (ValueError, TypeError):
        return default


# ── CRM Tools ──────────────────────────────────────────────────────────

@tool
def search_customers(query: str, limit: str = "5") -> str:
    """Search CRM customers by name or email."""
    result = crm.search(query, limit=_int(limit, 5))
    return json.dumps(result)

@tool
def get_customers(status: str = "", limit: str = "5") -> str:
    """List CRM customers. Filter by status (active/inactive)."""
    result = crm.fetch(limit=_int(limit, 5), status=status or None)
    return json.dumps(result)

@tool
def get_customer_by_id(customer_id: str) -> str:
    """Get a specific customer by ID."""
    c = crm.get_by_id(_int(customer_id, 0))
    return json.dumps(c if c else {"error": f"Customer {customer_id} not found"})


# ── Support Tools ──────────────────────────────────────────────────────

@tool
def get_support_tickets(priority: str = "", status: str = "", customer_id: str = "", limit: str = "5") -> str:
    """Retrieve support tickets. Filter by priority, status, customer_id."""
    result = support.fetch(
        limit=_int(limit, 5),
        priority=priority or None,
        status=status or None,
        customer_id=_int(customer_id, 0) if customer_id else None,
    )
    return json.dumps(result)

@tool
def get_ticket_by_id(ticket_id: str) -> str:
    """Get a specific support ticket by ID."""
    t = support.get_by_id(_int(ticket_id, 0))
    return json.dumps(t if t else {"error": f"Ticket {ticket_id} not found"})


# ── Analytics Tools ────────────────────────────────────────────────────

@tool
def get_analytics(metric: str = "", days: str = "7", limit: str = "10") -> str:
    """Retrieve analytics metrics. Filter by metric name and time range (days)."""
    result = analytics.fetch(limit=_int(limit, 10), metric=metric or None, days=_int(days, 7))
    return json.dumps(result)

@tool
def get_analytics_summary(metric: str = "", days: str = "7") -> str:
    """Summarized analytics: average, min, max, trend. Best for voice."""
    return json.dumps(analytics.get_summary(metric=metric or None, days=_int(days, 7)))


# ── Agent ──────────────────────────────────────────────────────────────

tools = [search_customers, get_customers, get_customer_by_id,
         get_support_tickets, get_ticket_by_id, get_analytics, get_analytics_summary]

agent = create_react_agent(
    model=ChatGroq(model=settings.GROQ_LLM_MODEL, max_tokens=512),
    tools=tools,
    checkpointer=InMemorySaver(),
    prompt=(
        "You are a friendly, concise AI assistant for a SaaS company. "
        "You help users query their business data (CRM customers, support tickets, "
        "and analytics) through voice conversations.\n\n"
        "Guidelines:\n"
        "• Keep responses SHORT and conversational — the user is listening via voice.\n"
        "• Summarise data rather than reading out raw records.\n"
        "• When presenting numbers, round them and say 'about' or 'around'.\n"
        "• If there are many results, highlight the most important ones.\n"
        "• Always mention the data source you used.\n"
        "• If a query is ambiguous, ask a brief clarifying question.\n"
        "• Use natural spoken language — avoid markdown formatting.\n"
    ),
)

agent_config = {"configurable": {"thread_id": "default_user"}}
