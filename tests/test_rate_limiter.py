"""Unit tests for the rate limiter."""

from mcplex.rate_limiter import RateLimiter


def test_no_limit_configured_allows_all():
    """Without a configured limit, all calls are allowed."""
    rl = RateLimiter()
    for _ in range(200):
        allowed, msg = rl.check("any_tool")
        assert allowed
        assert msg == ""


def test_per_tool_limit_enforced():
    """A per-tool limit blocks calls after the threshold."""
    rl = RateLimiter({"my_tool": {"max_requests": 3, "window_seconds": 60}})
    for i in range(3):
        allowed, _ = rl.check("my_tool")
        assert allowed
    allowed, msg = rl.check("my_tool")
    assert not allowed
    assert "Rate limit exceeded" in msg


def test_per_agent_limit():
    """Per-agent limits are tracked independently."""
    rl = RateLimiter({"tool": {"max_requests": 2, "window_seconds": 60, "per_agent": True}})
    assert rl.check("tool", "agent_a")[0]
    assert rl.check("tool", "agent_a")[0]
    assert not rl.check("tool", "agent_a")[0]
    assert rl.check("tool", "agent_b")[0]
    assert rl.check("tool", "agent_b")[0]


def test_different_tools_independent():
    """Rate limits for different tools don't interfere."""
    rl = RateLimiter({
        "tool_a": {"max_requests": 1, "window_seconds": 60},
        "tool_b": {"max_requests": 1, "window_seconds": 60},
    })
    assert rl.check("tool_a")[0]
    assert not rl.check("tool_a")[0]
    assert rl.check("tool_b")[0]


def test_no_agent_id_uses_tool_bucket():
    """Without agent_id, per-agent config falls back to per-tool bucket."""
    rl = RateLimiter({"tool": {"max_requests": 2, "window_seconds": 60, "per_agent": True}})
    assert rl.check("tool")[0]
    assert rl.check("tool")[0]
    assert not rl.check("tool")[0]
