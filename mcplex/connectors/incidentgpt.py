import json
from datetime import datetime, timedelta, timezone

# ── Mock data ──────────────────────────────────

ACTIVE_INCIDENTS = [
    {
        "id": "INC-2026-142",
        "title": "Payment service error rate spike",
        "severity": "sev2",
        "service": "payment-service",
        "started_at": "2026-07-20T14:23:00Z",
        "duration_minutes": 45,
        "responder": "alice@team",
        "status": "investigating",
    },
    {
        "id": "INC-2026-148",
        "title": "Auth service latency increase",
        "severity": "sev3",
        "service": "auth-service",
        "started_at": "2026-07-20T16:05:00Z",
        "duration_minutes": 12,
        "responder": "bob@team",
        "status": "monitoring",
    },
    {
        "id": "INC-2026-150",
        "title": "API gateway timeout on /checkout",
        "severity": "sev2",
        "service": "api-gateway",
        "started_at": "2026-07-20T17:30:00Z",
        "duration_minutes": 8,
        "responder": "carol@team",
        "status": "investigating",
    },
]

HISTORICAL_INCIDENTS = [
    {"id": "INC-2026-101", "title": "Database connection pool exhausted", "severity": "sev1", "service": "payment-service", "date": "2026-06-28", "root_cause": "Connection leak in order worker", "resolved": True},
    {"id": "INC-2026-102", "title": "Redis cluster failover", "severity": "sev2", "service": "auth-service", "date": "2026-06-30", "root_cause": "Memory pressure on primary node", "resolved": True},
    {"id": "INC-2026-105", "title": "Deploy caused 5xx spike", "severity": "sev1", "service": "api-gateway", "date": "2026-07-02", "root_cause": "Missing env var in new release", "resolved": True},
    {"id": "INC-2026-108", "title": "Certificate expiry alert", "severity": "sev3", "service": "api-gateway", "date": "2026-07-05", "root_cause": "Auto-renewal cron job failed", "resolved": True},
    {"id": "INC-2026-112", "title": "Payment timeout for high-value orders", "severity": "sev2", "service": "payment-service", "date": "2026-07-08", "root_cause": "Third-party provider rate limit hit", "resolved": True},
    {"id": "INC-2026-115", "title": "Auth tokens not refreshing", "severity": "sev2", "service": "auth-service", "date": "2026-07-10", "root_cause": "JWT library upgrade changed expiry behavior", "resolved": True},
    {"id": "INC-2026-120", "title": "API gateway memory leak", "severity": "sev3", "service": "api-gateway", "date": "2026-07-12", "root_cause": "Unbounded request logging", "resolved": True},
    {"id": "INC-2026-125", "title": "Payment service degraded after deploy", "severity": "sev2", "service": "payment-service", "date": "2026-07-15", "root_cause": "Config map not updated for new region", "resolved": True},
    {"id": "INC-2026-130", "title": "Auth DB migration rollback", "severity": "sev1", "service": "auth-service", "date": "2026-07-17", "root_cause": "Migration script had destructive ALTER", "resolved": True},
    {"id": "INC-2026-135", "title": "CI pipeline secret rotation failure", "severity": "sev3", "service": "api-gateway", "date": "2026-07-19", "root_cause": "Secret not rotated in all regions", "resolved": True},
]

INCIDENT_TIMELINES = {
    "INC-2026-142": {
        "events": [
            {"timestamp": "2026-07-20T14:23:00Z", "type": "detected", "description": "Error rate exceeded 5% threshold on payment-service", "actor": "prometheus"},
            {"timestamp": "2026-07-20T14:25:00Z", "type": "paged", "description": "Primary responder alice@team notified", "actor": "pagerduty"},
            {"timestamp": "2026-07-20T14:30:00Z", "type": "investigating", "description": "Alice identified recent deploy v2.14.3 as potential cause", "actor": "alice@team"},
            {"timestamp": "2026-07-20T14:45:00Z", "type": "action", "description": "Rolled back payment-service to v2.14.2", "actor": "alice@team"},
            {"timestamp": "2026-07-20T14:50:00Z", "type": "improving", "description": "Error rate dropping — 2% and decreasing", "actor": "prometheus"},
            {"timestamp": "2026-07-20T15:05:00Z", "type": "action", "description": "Root cause identified: null pointer in new order validation", "actor": "alice@team"},
        ],
        "correlated_deploys": [
            {"id": "DEP-2026-891", "service": "payment-service", "time": "2026-07-20T14:00:00Z"},
        ],
    },
    "INC-2026-148": {
        "events": [
            {"timestamp": "2026-07-20T16:05:00Z", "type": "detected", "description": "P99 latency for /auth/token increased from 200ms to 1200ms", "actor": "prometheus"},
            {"timestamp": "2026-07-20T16:08:00Z", "type": "paged", "description": "Primary responder bob@team notified", "actor": "pagerduty"},
            {"timestamp": "2026-07-20T16:15:00Z", "type": "investigating", "description": "Bob identified connection pool contention under load", "actor": "bob@team"},
            {"timestamp": "2026-07-20T16:20:00Z", "type": "action", "description": "Scaled auth-service replicas from 3 to 6", "actor": "bob@team"},
            {"timestamp": "2026-07-20T16:30:00Z", "type": "improving", "description": "Latency dropping — P99 at 450ms", "actor": "prometheus"},
        ],
        "correlated_deploys": [],
    },
    "INC-2026-150": {
        "events": [
            {"timestamp": "2026-07-20T17:30:00Z", "type": "detected", "description": "/checkout endpoint returning 504 for 2% of requests", "actor": "prometheus"},
            {"timestamp": "2026-07-20T17:32:00Z", "type": "paged", "description": "Primary responder carol@team notified", "actor": "pagerduty"},
            {"timestamp": "2026-07-20T17:38:00Z", "type": "investigating", "description": "Carol identified upstream payment service latency as bottleneck", "actor": "carol@team"},
        ],
        "correlated_deploys": [],
    },
}


# ── Handlers ───────────────────────────────────

async def handle_query_active(args: dict) -> str:
    service = args.get("service")
    severity = args.get("severity")
    results = ACTIVE_INCIDENTS
    if service:
        results = [i for i in results if i["service"] == service]
    if severity:
        results = [i for i in results if i["severity"] == severity]
    return json.dumps({"incidents": results})


async def handle_query_history(args: dict) -> str:
    service = args.get("service")
    days = args.get("days", 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = HISTORICAL_INCIDENTS
    if service:
        results = [i for i in results if i["service"] == service]
    results = [
        i for i in results
        if datetime.strptime(i["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc) >= cutoff
    ]
    return json.dumps({"incidents": results})


async def handle_get_timeline(args: dict) -> str:
    incident_id = args.get("incident_id")
    timeline = INCIDENT_TIMELINES.get(incident_id)
    if not timeline:
        return json.dumps({"error": f"incident {incident_id} not found"})
    return json.dumps(timeline)


# ── Registration ───────────────────────────────

def register(registry):
    registry.register_handler("incident_query_active", handle_query_active)
    registry.register_handler("incident_query_history", handle_query_history)
    registry.register_handler("incident_get_timeline", handle_get_timeline)
