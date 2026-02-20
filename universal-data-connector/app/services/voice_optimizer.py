from __future__ import annotations

from typing import List, Dict


def summarize_if_large(data: List[Dict]) -> List[Dict]:
    """
    Voice-friendly summarization.

    If more than 10 records:
    - Return a short summary instead of dumping full list.
    - Mention how many found.
    """

    if not data:
        return []

    if len(data) > 10:
        return [{
            "summary": f"{len(data)} records found. Showing top 10 most relevant results."
        }]

    return data


def generate_voice_highlights(data: List[Dict], source: str) -> List[str]:
    """
    Generate short bullet-style highlights for voice response.
    """

    highlights = []

    if source == "crm":
        active_count = sum(1 for d in data if d.get("status") == "active")
        highlights.append(f"{active_count} active customers in this result set.")

    elif source == "support":
        open_count = sum(1 for d in data if d.get("status") == "open")
        highlights.append(f"{open_count} open tickets found.")

    elif source == "analytics":
        if data:
            latest = data[0]
            highlights.append(
                f"Latest value for {latest.get('metric')} is {latest.get('value')}."
            )

    return highlights
