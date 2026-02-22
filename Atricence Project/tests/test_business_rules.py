"""
Tests for business rules engine.
"""

import pytest
from app.services.business_rules import (
    apply_voice_limits,
    sort_by_priority,
    sort_by_recency,
    generate_context_string,
    freshness_label,
)


class TestApplyVoiceLimits:

    def test_limits_results(self):
        data = [{"id": i} for i in range(50)]
        result = apply_voice_limits(data, limit=5)
        assert len(result["items"]) == 5
        assert result["total"] == 50
        assert result["total_pages"] == 10

    def test_pagination(self):
        data = [{"id": i} for i in range(20)]
        page1 = apply_voice_limits(data, limit=5, page=1)
        page2 = apply_voice_limits(data, limit=5, page=2)
        assert page1["items"][0]["id"] == 0
        assert page2["items"][0]["id"] == 5

    def test_empty_data(self):
        result = apply_voice_limits([], limit=5)
        assert result["items"] == []
        assert result["total"] == 0


class TestSortByPriority:

    def test_sorts_high_first(self):
        data = [
            {"priority": "low"},
            {"priority": "high"},
            {"priority": "medium"},
        ]
        sorted_data = sort_by_priority(data)
        assert sorted_data[0]["priority"] == "high"
        assert sorted_data[1]["priority"] == "medium"
        assert sorted_data[2]["priority"] == "low"

    def test_no_priority_field(self):
        data = [{"name": "a"}, {"name": "b"}]
        result = sort_by_priority(data)
        assert result == data


class TestSortByRecency:

    def test_sorts_newest_first(self):
        data = [
            {"created_at": "2025-01-01"},
            {"created_at": "2025-06-01"},
            {"created_at": "2025-03-01"},
        ]
        sorted_data = sort_by_recency(data)
        assert sorted_data[0]["created_at"] == "2025-06-01"


class TestContextString:

    def test_basic_context(self):
        result = generate_context_string("CRM", 50, 10)
        assert "10 of 50" in result

    def test_with_filters(self):
        result = generate_context_string("CRM", 20, 5, filters={"status": "active"})
        assert "status=active" in result


class TestFreshnessLabel:

    def test_returns_string(self):
        label = freshness_label()
        assert "Data as of" in label
