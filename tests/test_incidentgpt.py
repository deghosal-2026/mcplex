import json
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
    result = await handle_query_active({})
    data = json.loads(result)
    assert len(data["incidents"]) == len(ACTIVE_INCIDENTS)


@pytest.mark.asyncio
async def test_query_active_filters_by_service():
    result = await handle_query_active({"service": "payment-service"})
    data = json.loads(result)
    assert all(i["service"] == "payment-service" for i in data["incidents"])
    assert len(data["incidents"]) == 1


@pytest.mark.asyncio
async def test_query_active_filters_by_severity():
    result = await handle_query_active({"severity": "sev2"})
    data = json.loads(result)
    assert all(i["severity"] == "sev2" for i in data["incidents"])
    assert len(data["incidents"]) == 2


@pytest.mark.asyncio
async def test_query_active_filters_by_both():
    result = await handle_query_active({"service": "auth-service", "severity": "sev3"})
    data = json.loads(result)
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["id"] == "INC-2026-148"


@pytest.mark.asyncio
async def test_query_active_no_match():
    result = await handle_query_active({"service": "nonexistent"})
    data = json.loads(result)
    assert data["incidents"] == []


@pytest.mark.asyncio
async def test_query_history_returns_all():
    result = await handle_query_history({})
    data = json.loads(result)
    assert len(data["incidents"]) == len(HISTORICAL_INCIDENTS)


@pytest.mark.asyncio
async def test_query_history_filters_by_service():
    result = await handle_query_history({"service": "payment-service"})
    data = json.loads(result)
    assert all(i["service"] == "payment-service" for i in data["incidents"])


@pytest.mark.asyncio
async def test_query_history_filters_by_days():
    result = await handle_query_history({"days": 7})
    data = json.loads(result)
    assert all("2026-07" in i["date"] for i in data["incidents"])


@pytest.mark.asyncio
async def test_query_history_service_no_match():
    result = await handle_query_history({"service": "nonexistent"})
    data = json.loads(result)
    assert data["incidents"] == []


@pytest.mark.asyncio
async def test_query_history_resolved_field():
    result = await handle_query_history({})
    data = json.loads(result)
    assert all(i["resolved"] is True for i in data["incidents"])


@pytest.mark.asyncio
async def test_get_timeline_found():
    result = await handle_get_timeline({"incident_id": "INC-2026-142"})
    data = json.loads(result)
    assert "events" in data
    assert "correlated_deploys" in data
    assert len(data["events"]) == 6
    assert data["correlated_deploys"][0]["service"] == "payment-service"


@pytest.mark.asyncio
async def test_get_timeline_not_found():
    result = await handle_get_timeline({"incident_id": "FAKE-001"})
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_get_timeline_no_correlated_deploys():
    result = await handle_get_timeline({"incident_id": "INC-2026-150"})
    data = json.loads(result)
    assert data["correlated_deploys"] == []


@pytest.mark.asyncio
async def test_get_timeline_event_structure():
    result = await handle_get_timeline({"incident_id": "INC-2026-142"})
    data = json.loads(result)
    event = data["events"][0]
    assert "timestamp" in event
    assert "type" in event
    assert "description" in event
    assert "actor" in event
