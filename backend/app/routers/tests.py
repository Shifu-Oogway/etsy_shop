"""Test runner router — executes the pytest suite and returns structured results.

This endpoint is intentionally only available when ENVIRONMENT != 'production'
so it can never be accidentally exposed on a live server.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import get_settings

router = APIRouter(prefix="/tests", tags=["tests"])

# Root of the backend package (one level up from routers/)
_BACKEND_DIR = Path(__file__).parent.parent.parent


def _guard():
    if get_settings().environment == "production":
        raise HTTPException(403, "Test runner is disabled in production.")


@router.get("")
async def list_tests():
    """Collect test IDs without running them."""
    _guard()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q", "--no-header"],
        cwd=str(_BACKEND_DIR),
        capture_output=True,
        text=True,
    )
    lines = [l for l in result.stdout.splitlines() if "::" in l]
    tests = []
    for line in lines:
        parts = line.strip().split("::")
        tests.append({
            "id": line.strip(),
            "file": parts[0] if len(parts) > 0 else "",
            "name": "::".join(parts[1:]) if len(parts) > 1 else line.strip(),
        })
    return {"tests": tests, "count": len(tests)}


@router.post("/run")
async def run_tests(file: str | None = None):
    """Run the full test suite (or a single file) and stream JSON-lines results.

    Each line is one of:
      {"type": "start",  "total": N}
      {"type": "result", "id": "...", "status": "passed"|"failed"|"error",
                         "duration": 0.12, "message": "..."}
      {"type": "summary","passed": N, "failed": N, "errors": N,
                         "duration": 0.0, "output": "..."}
    """
    _guard()

    target = f"tests/{file}" if file else "tests/"

    def generate():
        cmd = [
            sys.executable, "-m", "pytest", target,
            "--tb=short", "--no-header", "-q",
            "--json-report", "--json-report-file=/tmp/pytest_report.json",
        ]
        # Install pytest-json-report if missing
        try:
            import pytest_jsonreport  # noqa
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pytest-json-report",
                 "--break-system-packages", "-q"],
                capture_output=True,
            )

        t0 = time.time()
        proc = subprocess.run(
            cmd, cwd=str(_BACKEND_DIR),
            capture_output=True, text=True,
        )
        duration = time.time() - t0

        # Parse JSON report
        report_path = Path("/tmp/pytest_report.json")
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text())
                tests = report.get("tests", [])
                total = len(tests)

                yield json.dumps({"type": "start", "total": total}) + "\n"

                for t in tests:
                    node = t.get("nodeid", "")
                    outcome = t.get("outcome", "unknown")  # passed / failed / error
                    dur = t.get("duration", 0.0)
                    # Extract failure message
                    msg = ""
                    call = t.get("call", {})
                    if call and call.get("longrepr"):
                        msg = str(call["longrepr"])[:500]
                    elif t.get("setup", {}).get("longrepr"):
                        msg = str(t["setup"]["longrepr"])[:500]

                    # Derive file + name from nodeid
                    parts = node.split("::")
                    yield json.dumps({
                        "type": "result",
                        "id": node,
                        "file": parts[0] if parts else "",
                        "name": "::".join(parts[1:]) if len(parts) > 1 else node,
                        "status": outcome,
                        "duration": round(dur, 3),
                        "message": msg,
                    }) + "\n"

                summary = report.get("summary", {})
                yield json.dumps({
                    "type": "summary",
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "errors": summary.get("error", 0),
                    "total": total,
                    "duration": round(duration, 2),
                    "output": proc.stdout[-3000:] if proc.stdout else "",
                }) + "\n"
                return
            except Exception as exc:
                pass  # fall through to plain-text parse

        # Fallback: parse pytest -q output without JSON report
        yield json.dumps({"type": "start", "total": 0}) + "\n"
        passed = failed = errors = 0
        for line in proc.stdout.splitlines():
            if " PASSED" in line or " passed" in line:
                passed += 1
            elif " FAILED" in line or " failed" in line:
                failed += 1
            elif " ERROR" in line:
                errors += 1
        yield json.dumps({
            "type": "summary",
            "passed": passed, "failed": failed, "errors": errors,
            "total": passed + failed + errors,
            "duration": round(duration, 2),
            "output": proc.stdout[-3000:],
        }) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
