from typing import List, Dict


def identify_data_type(data: List[Dict]) -> str:
    """
    Determines dataset type dynamically.
    Used for LLM routing + voice summarization behavior.
    """

    if not data:
        return "empty"

    # Look at first non-empty dict
    sample = next((item for item in data if isinstance(item, dict)), None)

    if not sample:
        return "unknown"

    keys = set(sample.keys())

    # Time series detection
    if {"date", "value"}.issubset(keys):
        return "time_series"

    # Support tickets
    if {"ticket_id", "status"}.issubset(keys):
        return "tabular_support"

    # CRM customers
    if {"customer_id", "email"}.issubset(keys):
        return "tabular_crm"

    return "unknown"
