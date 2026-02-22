"""
LLM service – collects tool definitions from all connectors
for the /tools/schema REST endpoint.

Note: The actual LLM integration for voice uses LangGraph in src/data_connector_agent.py,
not this service. This service only provides tool schema for documentation.
"""

import logging
from typing import Any, Dict, List

from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector

logger = logging.getLogger(__name__)

# ── Initialise connectors ──────────────────────────────────────────────
crm = CRMConnector()
support = SupportConnector()
analytics = AnalyticsConnector()

# ── Collect all tool definitions ───────────────────────────────────────
ALL_TOOLS: List[Dict[str, Any]] = (
    crm.get_tool_definitions()
    + support.get_tool_definitions()
    + analytics.get_tool_definitions()
)


def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """Return the full list of tool definitions for documentation / schema endpoint."""
    return ALL_TOOLS
