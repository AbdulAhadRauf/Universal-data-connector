from pydantic import BaseModel
from typing import Any, List, Optional, Dict
from enum import Enum
from datetime import datetime


# ----------------------------
# Existing Response Models
# ----------------------------
class Metadata(BaseModel):
    total_results: int
    returned_results: int
    data_freshness: str


class DataResponse(BaseModel):
    data: List[Any]
    metadata: Metadata


# ----------------------------
# NEW: LLM Query Models
# ----------------------------

class DataSource(str, Enum):
    crm = "crm"
    support = "support"
    analytics = "analytics"


class QueryMode(str, Enum):
    full = "full"
    voice = "voice"


class QueryRequest(BaseModel):
    source: DataSource
    mode: QueryMode = QueryMode.full
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    cursor: Optional[str] = None
    limit: Optional[int] = 10
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# class ErrorDetail(BaseModel):
#     code: str
#     message: str
#     details: Optional[Any] = None


# class ErrorResponse(BaseModel):
#     error: ErrorDetail