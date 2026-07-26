"""
Unit tests for the native IncidentGPT connector handlers.

Covers querying active/historical incidents and fetching timelines.
"""

import json
from datetime import datetime, timezone

import pytest

from mcplex.connectors.incidentgpt import (
    handle_query_active,
    handle_query_history,
    handle_get_timeline,
    ACTIVE_INCIDENTS,
    HISTORICAL_INCIDENTS,
)


@pytest.mark.asyncio
async def test_query_active_returns_all():
    """Without filters, all active incidents are returned."""
    result = await handle_query_active({})
    data = json.loads(result)
    assert len(data["incidents"]) == len(ACTIVE_INCIDENTS)


@pytest.mark.asyncio
async def test_query_active_filters_by_service():
    """Filtering by service returns only matching incidents."""
    result = await handle_query_active({"service": "payment-service"})
    data = json.loads(result)
    assert all(i["service"] == "payment-service" for i in data["incidents"])
    assert len(data["incidents"]) == 1


@pytest.mark.asyncio
async def test_query_active_filters_by_severity():
    """Filtering by severity returns only matching incidents."""
    result = await handle_query_active({"severity": "sev2"})
    data = json.loads(result)
    assert all(i["severity"] == "sev2" for i in data["incidents"])
    assert len(data["incidents"]) == 2


@pytest.mark.asyncio
async def test_query_active_filters_by_both():
    """Combined service + severity filters work together."""
    result = await handle_query_active({"service": "auth-service", "severity": "sev3"})
    data = json.loads(result)
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["id"] == "INC-2026-148"


@pytest.mark.asyncio
async def test_query_active_no_match():
    """A filter that matches nothing returns an empty list."""
    result = await handle_query_active({"service": "nonexistent"})
    data = json.loads(result)
    assert data["incidents"] == []


@pytest.mark.asyncio
async def test_query_history_returns_all():
    """Without filters, all historical incidents are returned."""
    result = await handle_query_history({})
    data = json.loads(result)
    assert len(data["incidents"]) == len(HISTORICAL_INCIDENTS)


@pytest.mark.asyncio
async def test_query_history_filters_by_service():
    """Filtering history by service name works correctly."""
    result = await handle_query_history({"service": "payment-service"})
    data = json.loads(result)
    assert all(i["service"] == "payment-service" for i in data["incidents"])


@pytest.mark.asyncio
async def test_query_history_filters_by_days_int():
    """days as an int filters incidents within that window."""
    result = await handle_query_history({"days": 7})
    data = json.loads(result)
    cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(days=7)
    for i in data["incidents"]:
        incident_date = datetime.strptime(i["date"], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        assert incident_date >= cutoff


@pytest.mark.asyncio
async def test_query_history_filters_by_days_str():
    """days arriving as a string (as MCP client sends) is handled correctly."""
    result = await handle_query_history({"days": "7"})
    data = json.loads(result)
    cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(days=7)
    for i in data["incidents"]:
        incident_date = datetime.strptime(i["date"], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        assert incident_date >= cutoff


@pytest.mark.asyncio
async def test_query_history_service_no_match():
    """Filtering history by a non-existent service returns an empty list."""
    result = await handle_query_history({"service": "nonexistent"})
    data = json.loads(result)
    assert data["incidents"] == []


@pytest.mark.asyncio
async def test_query_history_resolved_field():
    """All historical incidents have resolved=True."""
    result = await handle_query_history({})
    data = json.loads(result)
    assert all(i["resolved"] is True for i in data["incidents"])


@pytest.mark.asyncio
async def test_get_timeline_found():
    """A known incident_id returns its timeline with events and deploys."""
    result = await handle_get_timeline({"incident_id": "INC-2026-142"})
    data = json.loads(result)
    assert "events" in data
    assert "correlated_deploys" in data
    assert len(data["events"]) == 6
    assert data["correlated_deploys"][0]["service"] == "payment-service"


@pytest.mark.asyncio
async def test_get_timeline_not_found():
    """An unknown incident_id returns an error."""
    result = await handle_get_timeline({"incident_id": "FAKE-001"})
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_get_timeline_no_correlated_deploys():
    """An incident with no correlated deploys returns an empty list."""
    result = await handle_get_timeline({"incident_id": "INC-2026-150"})
    data = json.loads(result)
    assert data["correlated_deploys"] == []


@pytest.mark.asyncio
async def test_get_timeline_event_structure():
    """Each event has the expected fields."""
    result = await handle_get_timeline({"incident_id": "INC-2026-142"})
    data = json.loads(result)
    event = data["events"][0]
    assert "timestamp" in event
    assert "type" in event
    assert "description" in event
    assert "actor" in event
