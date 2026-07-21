"""
E2E test — Launches MCP Inspector, connects to MCPlex, tests all 9 tools.

Self-contained: launches the Inspector, drives the UI via Playwright,
clicks "List Tools" to fetch the catalog, then exercises every tool.
Asserts the response contains expected keys.

Screenshots are saved to ``tests/e2e/screenshots/`` alongside the
test plan and results (``tests/e2e/README.md``).

Run::

    python3 tests/e2e/test_inspector_e2e.py

Exit: 0 if all 9 tools pass, 1 otherwise.
"""

import json
import asyncio
import subprocess
import time
import sys
import os
import signal
import re
import urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

MCP_SERVER_URL = "http://localhost:8080/mcp"
INSPECTOR_URL = "http://localhost:6274"
INSPECTOR_PORT = "6274"
PROXY_PORT = "6277"

SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

TOOLS_TO_TEST = [
    {"tool": "guardian_check_policy", "args": {"repo": "my-org/payment-service", "pr_number": "42"},
     "expect_keys": ["passed", "rules"]},
    {"tool": "guardian_get_coverage", "args": {"repo": "my-org/payment-service"},
     "expect_keys": ["coverage_pct", "total_prs"]},
    {"tool": "ci_diagnose_failure", "args": {"repo": "my-org/payment-service", "run_id": "123"},
     "expect_keys": ["root_cause", "suggested_fix"]},
    {"tool": "ci_get_pipeline_history", "args": {"repo": "my-org/payment-service", "days": "30"},
     "expect_keys": ["total_runs", "pass_rate"]},
    {"tool": "dora_get_metrics", "args": {"scope": "platform-team", "days": "30"},
     "expect_keys": ["deploy_frequency", "lead_time"]},
    {"tool": "dora_get_trend", "args": {"scope": "platform-team", "days": "90"},
     "expect_keys": ["weekly"]},
    {"tool": "incident_query_active", "args": {"severity": "sev2"},
     "expect_keys": ["incidents"]},
    {"tool": "incident_query_history", "args": {"service": "payment-service", "days": "30"},
     "expect_keys": ["incidents"]},
    {"tool": "incident_get_timeline", "args": {"incident_id": "INC-2026-142"},
     "expect_keys": ["events"]},
]


def launch_inspector():
    """Start the MCP Inspector with auth disabled."""
    env = os.environ.copy()
    env["DANGEROUSLY_OMIT_AUTH"] = "true"
    proc = subprocess.Popen(
        ["npx", "@modelcontextprotocol/inspector",
         "--transport", "http", "--server-url", MCP_SERVER_URL],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(30):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"http://localhost:{INSPECTOR_PORT}/", timeout=2)
            return proc
        except Exception:
            continue
    return proc


def screenshot_path(name):
    return str(SCREENSHOT_DIR / name)


async def wait_visible(page, selectors, timeout=5000):
    """Try multiple selectors, return the first visible one."""
    for sel in selectors:
        loc = page.locator(sel).first
        try:
            if await loc.is_visible(timeout=min(timeout, 1500)):
                return loc
        except Exception:
            continue
    return None


async def click_combobox_option(page, dropdown, option_text):
    """Open a combobox and click an option by text."""
    await dropdown.click()
    await page.wait_for_timeout(400)
    option = page.locator(f"[role='option']:has-text('{option_text}')").first
    if not await option.is_visible(timeout=2000):
        option = page.locator(f"text={option_text}").first
    await option.click()
    await page.wait_for_timeout(200)


async def fill_arg(page, key, value):
    """Fill a tool argument input by key name."""
    # Try id, name, placeholder
    for sel in [f"input#{key}", f"input[name='{key}']",
                f"input[placeholder*='{key}']",
                f"textarea#{key}", f"textarea[name='{key}']"]:
        loc = page.locator(sel).first
        if await loc.is_visible(timeout=800):
            await loc.fill(str(value))
            return True
    # Try via label
    lbl = page.locator(f"label[for='{key}']").first
    if await lbl.is_visible(timeout=500):
        inp = page.locator(f"#{key}").first
        if await inp.is_visible(timeout=500):
            await inp.fill(str(value))
            return True
    return False


def extract_json_from_text(text):
    """Extract a JSON object from rendered page text."""
    # The Inspector renders JSON as a tree with colons, not raw JSON.
    # Look for "Tool Result:" section and parse the tree.
    # Fallback: try to find raw JSON with regex.
    match = re.search(r'\{[^{}]*"passed"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # Try finding any {...} block
    for m in re.finditer(r'\{.*?\}', text, re.DOTALL):
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
    return None


async def run():
    print("=" * 70)
    print("MCPlex E2E Test — MCP Inspector UI")
    print("Screenshots → docs/user-guide/screenshots/")
    print("=" * 70)

    # 1. Launch Inspector
    print("\n[1/7] Launching MCP Inspector...")
    inspector_proc = launch_inspector()
    print(f"   Inspector PID: {inspector_proc.pid}")
    await asyncio.sleep(3)

    results = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1400, "height": 1000})

            # 2. Open Inspector UI
            print(f"\n[2/7] Opening {INSPECTOR_URL}")
            await page.goto(INSPECTOR_URL, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=screenshot_path("01-landing.png"))

            # 3. Select Streamable HTTP transport
            print("\n[3/7] Selecting Streamable HTTP transport...")
            transport_dd = page.locator("button[role='combobox']").first
            await transport_dd.is_visible(timeout=5000)
            await click_combobox_option(page, transport_dd, "Streamable HTTP")
            print("   ✓ Selected Streamable HTTP")
            await page.screenshot(path=screenshot_path("02-transport-selected.png"))

            # 4. Enter server URL
            print("\n[4/7] Entering server URL...")
            url_input = await wait_visible(page, [
                "input#sse-url-input",
                "input[id*='url']",
                "input[placeholder*='URL']",
                "#command-input",
            ], timeout=3000)
            if url_input:
                await url_input.fill(MCP_SERVER_URL)
                print(f"   ✓ Entered URL: {MCP_SERVER_URL}")
            await page.screenshot(path=screenshot_path("03-url-entered.png"))

            # 5. Click Connect
            print("\n[5/7] Connecting...")
            connect_btn = page.locator("button:has-text('Connect')").first
            await connect_btn.click()
            await page.wait_for_timeout(5000)

            body = await page.locator("body").inner_text()
            if "Connected" in body:
                print("   ✓ Connected to MCPlex")
            await page.screenshot(path=screenshot_path("04-connected.png"))

            # 6. Load tools catalog
            print("\n[6/7] Loading tools catalog...")
            # Click Tools tab
            tools_tab = page.locator("button:has-text('Tools')").first
            await tools_tab.click()
            await page.wait_for_timeout(500)
            # Click List Tools
            list_btn = page.locator("button:has-text('List Tools')").first
            await list_btn.click()
            await page.wait_for_timeout(3000)

            body = await page.locator("body").inner_text()
            tool_count = sum(1 for t in TOOLS_TO_TEST if t["tool"] in body)
            print(f"   ✓ {tool_count}/{len(TOOLS_TO_TEST)} tools visible")
            await page.screenshot(path=screenshot_path("05-tools-listed.png"))

            # 7. Test each tool
            print(f"\n[7/7] Testing {len(TOOLS_TO_TEST)} tools...")
            print("-" * 70)

            for i, t in enumerate(TOOLS_TO_TEST):
                tool_name = t["tool"]
                args = t["args"]
                expect_keys = t["expect_keys"]
                label = f"[{i+1}/{len(TOOLS_TO_TEST)}]"

                print(f"\n{label} {tool_name}")
                result = {"tool": tool_name, "args": args, "status": "fail", "response": ""}

                try:
                    # Click the tool name in the list
                    tool_elem = page.locator(f"text={tool_name}").first
                    if not await tool_elem.is_visible(timeout=5000):
                        print(f"   ✗ Tool not found in UI")
                        result["response"] = "Tool not found"
                        results.append(result)
                        continue

                    await tool_elem.click()
                    await page.wait_for_timeout(800)
                    print(f"   ✓ Selected tool")

                    # Fill args
                    for key, value in args.items():
                        ok = await fill_arg(page, key, value)
                        if ok:
                            print(f"   ✓ {key} = {value}")
                        else:
                            print(f"   ~ {key} input not found")

                    # Click "Run Tool"
                    run_btn = page.locator("button:has-text('Run Tool')").first
                    if not await run_btn.is_visible(timeout=2000):
                        run_btn = page.locator("button:has-text('Call Tool')").first
                    if await run_btn.is_visible(timeout=1000):
                        await run_btn.click()
                        print(f"   ✓ Ran tool")
                        await page.wait_for_timeout(3000)
                    else:
                        print(f"   ✗ No Run button")

                    # Capture response from "Tool Result:" section
                    body = await page.locator("body").inner_text()

                    # Check for success/error indicator
                    if "Tool Result: Success" in body:
                        result_section = body.split("Tool Result: Success")[1].split("History")[0]
                        print(f"   ✓ Got result")
                    elif "Tool Result:" in body:
                        result_section = body.split("Tool Result:")[1].split("History")[0]
                        print(f"   ~ Got result (status unclear)")
                    else:
                        result_section = body[-800:]
                        print(f"   ~ No clear result section")

                    await page.screenshot(
                        path=screenshot_path(f"06-{(i+1):02d}-{tool_name}.png"))

                    # Validate: check expected keys appear in the result text
                    found_keys = [k for k in expect_keys if k in result_section]
                    missing = [k for k in expect_keys if k not in result_section]

                    if not missing:
                        print(f"   ✓ PASS — keys found: {found_keys}")
                        result["status"] = "pass"
                        result["response"] = result_section.strip()[:500]
                    else:
                        print(f"   ✗ FAIL — missing: {missing}")
                        print(f"     Result (200): {result_section[:200]}")
                        result["response"] = f"Missing: {missing}"

                except Exception as e:
                    print(f"   ✗ ERROR — {e}")
                    result["response"] = str(e)
                    await page.screenshot(
                        path=screenshot_path(f"06-{(i+1):02d}-{tool_name}-error.png"))

                results.append(result)

            # Final screenshot — tools list overview
            await page.screenshot(path=screenshot_path("07-final-overview.png"),
                                  full_page=True)
            await browser.close()

    finally:
        print("\nCleaning up Inspector...")
        try:
            os.killpg(os.getpgid(inspector_proc.pid), signal.SIGTERM)
        except Exception:
            inspector_proc.terminate()
        inspector_proc.wait(timeout=5)

    # Summary
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")

    for r in results:
        icon = {"pass": "✓", "fail": "✗"}.get(r["status"], "?")
        print(f"  {icon} {r['tool']:30s} {r['status'].upper()}")

    print(f"\n  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    print(f"  Screenshots: {SCREENSHOT_DIR}")
    print("=" * 70)

    with open(SCREENSHOT_DIR.parent / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    asyncio.run(run())
