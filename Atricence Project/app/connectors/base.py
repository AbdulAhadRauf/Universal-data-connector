"""
Abstract base class for all data connectors.
Every connector must implement fetch(), search(), get_by_id() and provide
a schema description so the LLM knows how to call it.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.models.common import DataType


class BaseConnector(ABC):
    """Interface that every data source connector must satisfy."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of this data source (e.g. 'CRM')."""
        ...

    @property
    @abstractmethod
    def data_type(self) -> DataType:
        """Primary data type this connector returns."""
        ...

    @abstractmethod
    def fetch(
        self,
        *,
        limit: int = 10,
        page: int = 1,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        **filters: Any,
    ) -> Dict[str, Any]:
        """
        Retrieve records with pagination, sorting and arbitrary filters.

        Returns a dict with keys:
            items  – list of records
            total  – total matching count (before pagination)
        """
        ...

    @abstractmethod
    def search(self, query: str, *, limit: int = 10) -> Dict[str, Any]:
        """Free-text search across relevant fields."""
        ...

    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Return one record by its primary key, or None."""
        ...

    @abstractmethod
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return OpenAI-compatible tool/function definitions
        that the LLM can invoke against this connector.
        """
        ...
