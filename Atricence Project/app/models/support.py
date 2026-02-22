"""
Support ticket data models.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class SupportTicket(BaseModel):
    """Represents a single support ticket."""
    ticket_id: int
    customer_id: int
    subject: str
    priority: str = Field(..., description="high | medium | low")
    created_at: datetime
    status: str = Field(..., description="open | closed")
