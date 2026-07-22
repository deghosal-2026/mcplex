"""Test bench for MCPlex — simulates 4 backend APIs.

Run: python tests/test_bench.py
This starts 4 servers on ports 8001-8004 for mcplex to connect to.
"""

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


def make_bench(name: str, port: int, routes: list) -> Starlette:
    app = Starlette(debug=False, routes=routes)
    print(f"  {name} → http://localhost:{port}")
    return app


# ── Health check (all benches) ─────────────────────────────────

async def health_check(request):
    return JSONResponse({"status": "ok"})


# ── Guardian (:8001) ──────────────────────────────────────────

async def guardian_policy_check(request):
    body = await request.json()
    return JSONResponse({
        "passed": True,
        "repo": body.get("repo", "unknown"),
        "pr_number": body.get("pr_number", 0),
        "rules": [
            {"name": "hallucinated-apis", "passed": True, "evidence": "No hallucinated API calls detected"},
            {"name": "missing-error-handling", "passed": True, "evidence": "All error paths handled"},
            {"name": "hardcoded-secrets", "passed": True, "evidence": "No secrets in code"},
        ],
    })

async def guardian_stats(request):
    repo = request.query_params.get("repo", "unknown")
    return JSONResponse({
        "repo": repo,
        "coverage_pct": 87,
        "total_prs": 142,
        "reviewed_prs": 124,
        "trend": "+5% this month",
    })

guardian = make_bench("guardian", 8001, [
    Route("/api/policy/check", guardian_policy_check, methods=["POST"]),
    Route("/api/stats", guardian_stats, methods=["GET"]),
    Route("/health", health_check),
])


# ── CI-Doctor (:8002) ─────────────────────────────────────────

async def ci_diagnose(request):
    await request.json()
    return JSONResponse({
        "root_cause": "Flaky test: TestAuthRefresh timing out intermittently",
        "confidence": 0.89,
        "suggested_fix": "Increase timeout from 2s to 5s in auth_test.go:42",
        "similar_failures": [
            {"date": "2026-07-15", "cause": "TestAuthRefresh timeout", "fix": "Increased timeout"},
            {"date": "2026-07-10", "cause": "TestAuthRefresh timeout", "fix": "Increased timeout"},
        ],
    })

async def ci_history(request):
    repo = request.query_params.get("repo", "unknown")
    return JSONResponse({
        "repo": repo,
        "total_runs": 89,
        "pass_rate": 0.76,
        "failure_patterns": [
            {"pattern": "flakey test timeout", "frequency": 12, "last_seen": "2026-07-19"},
            {"pattern": "dependency download failure", "frequency": 4, "last_seen": "2026-07-17"},
        ],
    })

ci_doctor = make_bench("ci-doctor", 8002, [
    Route("/api/diagnose", ci_diagnose, methods=["POST"]),
    Route("/api/history", ci_history, methods=["GET"]),
    Route("/health", health_check),
])


# ── Sprint Intelligence (:8003) ────────────────────────────────

async def dora_metrics(request):
    scope = request.query_params.get("scope", "unknown")
    return JSONResponse({
        "scope": scope,
        "deploy_frequency": "daily",
        "lead_time": "4.2h",
        "mttr": "25min",
        "change_failure_rate": "0.08",
        "trend": "improving",
    })

async def dora_trend(request):
    scope = request.query_params.get("scope", "unknown")
    return JSONResponse({
        "scope": scope,
        "weekly": [
            {"week": "W29", "deploy_frequency": "daily", "lead_time": "4.2h", "mttr": "25min", "change_failure_rate": 0.08},
            {"week": "W28", "deploy_frequency": "daily", "lead_time": "5.1h", "mttr": "32min", "change_failure_rate": 0.11},
            {"week": "W27", "deploy_frequency": "daily", "lead_time": "6.0h", "mttr": "40min", "change_failure_rate": 0.15},
        ],
    })

sprint_intel = make_bench("sprint-intelligence", 8003, [
    Route("/api/dora/metrics", dora_metrics, methods=["GET"]),
    Route("/api/dora/trend", dora_trend, methods=["GET"]),
    Route("/health", health_check),
])


# ── Incident Commander (:8004) ─────────────────────────────────

ACTIVE = [
    {"id": "INC-2026-142", "title": "Payment service error rate spike", "severity": "sev2", "service": "payment-service", "started_at": "2026-07-20T14:23:00Z", "duration_minutes": 45, "responder": "alice@team", "status": "investigating"},
    {"id": "INC-2026-148", "title": "Auth service latency increase", "severity": "sev3", "service": "auth-service", "started_at": "2026-07-20T16:05:00Z", "duration_minutes": 12, "responder": "bob@team", "status": "monitoring"},
]

HISTORY = [
    {"id": "INC-2026-101", "title": "Database connection pool exhausted", "severity": "sev1", "service": "payment-service", "date": "2026-06-28", "root_cause": "Connection leak in order worker", "resolved": True},
    {"id": "INC-2026-105", "title": "Deploy caused 5xx spike", "severity": "sev1", "service": "api-gateway", "date": "2026-07-02", "root_cause": "Missing env var in new release", "resolved": True},
]

TIMELINES = {
    "INC-2026-142": {
        "events": [
            {"timestamp": "2026-07-20T14:23:00Z", "type": "detected", "description": "Error rate exceeded 5% threshold", "actor": "prometheus"},
            {"timestamp": "2026-07-20T14:45:00Z", "type": "action", "description": "Rolled back payment-service to v2.14.2", "actor": "alice@team"},
        ],
        "correlated_deploys": [{"id": "DEP-2026-891", "service": "payment-service", "time": "2026-07-20T14:00:00Z"}],
    },
}

async def incidents_active(request):
    service = request.query_params.get("service")
    severity = request.query_params.get("severity")
    results = ACTIVE
    if service:
        results = [i for i in results if i["service"] == service]
    if severity:
        results = [i for i in results if i["severity"] == severity]
    return JSONResponse({"incidents": results})

async def incidents_history(request):
    service = request.query_params.get("service")
    results = HISTORY
    if service:
        results = [i for i in results if i["service"] == service]
    return JSONResponse({"incidents": results})

async def incidents_timeline(request):
    incident_id = request.query_params.get("incident_id")
    timeline = TIMELINES.get(incident_id)
    if not timeline:
        return JSONResponse({"incidents": [], "events": [], "error": f"incident {incident_id} not found"})
    return JSONResponse(timeline)

incident_cmdr = make_bench("incident-commander", 8004, [
    Route("/api/incidents/active", incidents_active, methods=["GET"]),
    Route("/api/incidents/history", incidents_history, methods=["GET"]),
    Route("/api/incidents/timeline", incidents_timeline, methods=["GET"]),
    Route("/health", health_check),
])


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import multiprocessing

    benches = [
        ("guardian", 8001, guardian),
        ("ci-doctor", 8002, ci_doctor),
        ("sprint-intelligence", 8003, sprint_intel),
        ("incident-commander", 8004, incident_cmdr),
    ]

    procs = []
    for name, port, app in benches:
        p = multiprocessing.Process(target=uvicorn.run, args=(app,), kwargs={"host": "0.0.0.0", "port": port, "log_level": "warning"}, daemon=True)
        p.start()
        procs.append(p)

    print("Test bench running:")
    for name, port, _ in benches:
        print(f"  {name} → http://localhost:{port}")
    print("\nPress Ctrl+C to stop.")

    try:
        import signal
        signal.pause()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
