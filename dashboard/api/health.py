#!/usr/bin/env python3
"""Repository health snapshot collector.

The collector is intentionally dependency-free and read-only. CI systems may
write additional JSON evidence to dashboard/data; missing evidence is reported
as unknown rather than converted into a misleading passing score.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("ZEAZ_ROOT", Path(__file__).resolve().parents[2])).resolve()
DATA = Path(os.environ.get("DASHBOARD_DATA", ROOT / "dashboard" / "data")).resolve()
REPORT_NAMES = ("ci", "coverage", "security", "performance", "infrastructure", "agents")
REPORT_STATUSES = {"pass", "fail", "unknown", "not_applicable"}


def _positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ("git", "-C", str(ROOT), *args),
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _report(name: str) -> dict[str, Any]:
    path = DATA / f"{name}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Report must be a JSON object")
        required = {
            "schemaVersion": int,
            "status": str,
            "summary": str,
            "generatedAt": str,
        }
        if any(not isinstance(value.get(key), kind) for key, kind in required.items()):
            raise ValueError("Report is missing required typed fields")
        if value["schemaVersion"] != 1 or value["status"] not in REPORT_STATUSES:
            raise ValueError("Unsupported report schema or status")
        generated = datetime.fromisoformat(value["generatedAt"].replace("Z", "+00:00"))
        if generated.utcoffset() is None:
            raise ValueError("Report generatedAt must include a timezone")
        current = datetime.now(timezone.utc)
        if generated > current + timedelta(minutes=5):
            raise ValueError("Report generatedAt is too far in the future")
        ttl_hours = _positive_int("DASHBOARD_EVIDENCE_TTL_HOURS", 24)
        if generated < current - timedelta(hours=ttl_hours):
            return {**value, "status": "unknown", "reason": "Published evidence is stale"}
        return value
    except FileNotFoundError:
        return {"status": "unknown", "reason": "No report published"}
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        return {"status": "invalid", "reason": str(error)}


def _tracked(pattern: str) -> int:
    output = _git("ls-files", pattern)
    return len(output.splitlines()) if output else 0


def _percent(values: list[bool]) -> int:
    return round(sum(values) * 100 / len(values)) if values else 0


def _report_score(name: str, report: dict[str, Any]) -> float:
    if report.get("status") != "pass":
        return 0
    if name == "coverage":
        value = report.get("metrics", {}).get("percent", 0)
        return max(0, min(100, float(value))) if isinstance(value, (int, float)) else 0
    return 100


def snapshot() -> dict[str, Any]:
    reports = {name: _report(name) for name in REPORT_NAMES}
    checks = {
        "ci": (ROOT / ".github/workflows/validate.yml").is_file(),
        "tests": any((ROOT / "tests").glob("test_*.py")),
        "docker": (ROOT / "dashboard/Dockerfile").is_file(),
        "kubernetes": (ROOT / "deploy/kubernetes/kustomization.yaml").is_file(),
        "openapi": (ROOT / "docs/openapi.yaml").is_file(),
        "operations": (ROOT / "OPERATIONS.md").is_file(),
        "security": (ROOT / "SECURITY.md").is_file(),
    }
    changed = _git("status", "--short")
    commit_lines = _git(
        "log", "-8", "--date=iso-strict", "--pretty=format:%h%x09%ad%x09%s"
    )
    commits = []
    for line in commit_lines.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    applicable = {
        name: report.get("status", "unknown")
        for name, report in reports.items()
        if report.get("status") != "not_applicable"
    }
    confirmed = [status for status in applicable.values() if status in {"pass", "fail"}]
    quality_names = ("ci", "coverage")
    readiness_names = ("ci", "security", "performance", "infrastructure")
    quality = round(
        sum(_report_score(name, reports[name]) for name in quality_names)
        / len(quality_names)
    )
    readiness_controls = round(
        sum(_report_score(name, reports[name]) for name in readiness_names)
        / len(readiness_names)
    )
    readiness = min(quality, readiness_controls)
    repository_health = round(
        sum(_report_score(name, reports[name]) for name in applicable)
        / len(applicable)
    ) if applicable else 100
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "name": os.environ.get("ZEAZ_REPOSITORY", ROOT.name),
            "branch": _git("branch", "--show-current")
            or os.environ.get("ZEAZ_BRANCH", "detached"),
            "revision": _git("rev-parse", "--short", "HEAD")
            or os.environ.get("ZEAZ_REVISION", "unknown"),
            "dirty": bool(changed),
            "changedFiles": len(changed.splitlines()) if changed else 0,
            "trackedFiles": _tracked("*"),
        },
        "scores": {
            "repositoryHealth": repository_health,
            "quality": quality,
            "productionReadiness": readiness,
            "evidenceCoverage": round(len(confirmed) * 100 / len(applicable)) if applicable else 100,
        },
        "checks": checks,
        "reports": reports,
        "commits": commits,
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
