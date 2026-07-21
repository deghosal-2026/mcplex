# Test Bench Screenshots

Screenshots showing the all-mock topology (test-bench simulating all 4
backends) are captured via the E2E test at `tests/e2e/`.

When all 4 connectors point to test-bench (no real repos wired in),
the E2E test captures screenshots showing test-bench responses across
all 9 tools. See `tests/e2e/screenshots/` for the current run, which
now has ci-doctor wired to its real repo.
