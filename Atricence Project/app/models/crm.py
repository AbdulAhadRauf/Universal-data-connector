"""
CRM data models.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Customer(BaseModel):
    """Represents a single CRM customer record."""
    customer_id: int
    name: str
    email: str
    created_at: datetime
    status: str = Field(..., description="active | inactive")
