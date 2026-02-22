"""
Analytics / metrics data models.
"""

from pydantic import BaseModel
from datetime import date


class MetricEntry(BaseModel):
    """A single analytics data point."""
    metric: str
    date: date
    value: float
