#!/usr/bin/env python3
"""Generate machine-readable engineering evidence for the dashboard."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
import trace
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(os.environ.get("DASHBOARD_DATA", ROOT / "dashboard" / "data"))
sys.path.insert(0, str(ROOT))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_report(
    name: str,
    status: str,
    summary: str,
    metrics: dict[str, Any] | None = None,
    details: list[dict[str, Any]] | None = None,
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": 1,
        "status": status,
        "summary": summary,
        "generatedAt": now(),
        "metrics": metrics or {},
        "details": details or [],
    }
    temporary = OUTPUT / f".{name}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT / f"{name}.json")


def run(command: list[str]) -> tuple[int, str, str, float]:
    started = time.monotonic()
    try:
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        return (
            process.returncode,
            process.stdout,
            process.stderr,
            round(time.monotonic() - started, 3),
        )
    except OSError as error:
        return 127, "", str(error), round(time.monotonic() - started, 3)


def _output(stdout: str, stderr: str) -> str:
    return (stdout + stderr)[-8000:]


def _npm_audit_vulnerabilities(output: str) -> dict[str, Any]:
    result = json.loads(output)
    if not isinstance(result, dict):
        raise ValueError("npm audit output must be an object")
    vulnerabilities = result["metadata"]["vulnerabilities"]
    if not isinstance(vulnerabilities, dict):
        raise ValueError("npm audit vulnerabilities must be an object")
    return vulnerabilities


def _python_audit_count(output: str) -> int:
    result = json.loads(output)
    if not isinstance(result, dict) or not isinstance(
        result.get("dependencies"), list
    ):
        raise ValueError("pip-audit output must contain a dependencies list")
    return sum(
        len(item.get("vulns", []))
        for item in result["dependencies"]
        if isinstance(item, dict) and isinstance(item.get("vulns", []), list)
    )


def security() -> int:
    pip_python = sys.executable
    if importlib.util.find_spec("pip") is None and (ROOT / ".venv/bin/python").is_file():
        pip_python = str(ROOT / ".venv/bin/python")
    pip_code, pip_stdout, pip_stderr, pip_seconds = run([pip_python, "-m", "pip", "check"])
    audit_code, audit_stdout, audit_stderr, audit_seconds = run(
        [
            pip_python,
            "-m",
            "pip_audit",
            "--requirement",
            str(ROOT / "requirements.txt"),
            "--format",
            "json",
            "--progress-spinner",
            "off",
            "--strict",
        ]
    )
    npm_code, npm_stdout, npm_stderr, npm_seconds = run(
        ["npm", "audit", "--audit-level=moderate", "--json"]
    )
    vulnerabilities: dict[str, Any] = {}
    try:
        vulnerabilities = _npm_audit_vulnerabilities(npm_stdout)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        npm_code = npm_code or 1
    try:
        python_vulnerabilities = _python_audit_count(audit_stdout)
    except (TypeError, ValueError, json.JSONDecodeError):
        python_vulnerabilities = 0
        audit_code = audit_code or 1
    status = "pass" if pip_code == audit_code == npm_code == 0 else "fail"
    write_report(
        "security",
        status,
        "Dependency security checks passed." if status == "pass" else "Dependency checks found errors or vulnerabilities.",
        {
            "pythonVulnerabilities": python_vulnerabilities,
            "npmVulnerabilities": vulnerabilities,
        },
        [
            {"check": "pip check", "exitCode": pip_code, "durationSeconds": pip_seconds, "output": _output(pip_stdout, pip_stderr)},
            {"check": "pip-audit runtime requirements", "exitCode": audit_code, "durationSeconds": audit_seconds, "output": _output(audit_stdout, audit_stderr)},
            {"check": "npm audit all dependencies", "exitCode": npm_code, "durationSeconds": npm_seconds, "output": _output(npm_stdout, npm_stderr)},
        ],
    )
    return 0 if status == "pass" else 1


def coverage() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix, sys.base_prefix])
    thread_tracer = trace.Trace(
        count=True, trace=False, ignoredirs=[sys.prefix, sys.base_prefix]
    )
    previous_thread_trace = threading.gettrace()
    threading.settrace(thread_tracer.globaltrace)
    try:
        result = tracer.runfunc(runner.run, suite)
    finally:
        threading.settrace(previous_thread_trace)
    counts = Counter(tracer.results().counts)
    counts.update(thread_tracer.results().counts)
    source_files = [
        ROOT / "app.py",
        *sorted((ROOT / "dashboard").rglob("*.py")),
        *sorted((ROOT / "migrations").glob("*.py")),
    ]
    executable = covered = 0
    by_file = []
    for path in source_files:
        lines = set(trace._find_executable_linenos(str(path)))
        hit = {line for filename, line in counts if Path(filename).resolve() == path.resolve()}
        executable += len(lines)
        covered += len(lines & hit)
        by_file.append(
            {
                "file": str(path.relative_to(ROOT)),
                "executable": len(lines),
                "covered": len(lines & hit),
                "percent": round(len(lines & hit) * 100 / len(lines), 2) if lines else 100,
            }
        )
    percent = round(covered * 100 / executable, 2) if executable else 0
    threshold = float(os.environ.get("PYTHON_COVERAGE_MIN", "56"))
    passed = result.wasSuccessful() and percent >= threshold
    test_metrics = {
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }
    summary = (
        f"Python line coverage is {percent}% (minimum {threshold}%)."
        if result.wasSuccessful()
        else f"Coverage run had {len(result.failures)} failures and {len(result.errors)} errors; measured {percent}%."
    )
    write_report(
        "coverage",
        "pass" if passed else "fail",
        summary,
        {"language": "python", "coveredLines": covered, "executableLines": executable, "percent": percent, "minimumPercent": threshold, **test_metrics},
        by_file,
    )
    return 0 if passed else 1


def performance() -> int:
    bundle_limit = int(os.environ.get("JS_BUNDLE_MAX_BYTES", "225000"))
    image_limit = int(os.environ.get("HERO_IMAGE_MAX_BYTES", "2000000"))
    bundles = sorted((ROOT / "apps/web/dist/assets").glob("*.js"))
    hero = ROOT / "web/images/moopiew-hero.png"
    largest_bundle = max((path.stat().st_size for path in bundles), default=0)
    hero_size = hero.stat().st_size if hero.exists() else 0
    checks = {
        "bundleWithinBudget": bool(bundles) and largest_bundle <= bundle_limit,
        "heroWithinBudget": hero.exists() and hero_size <= image_limit,
    }
    status = "pass" if all(checks.values()) else "fail"
    write_report(
        "performance",
        status,
        "Static asset budgets passed." if status == "pass" else "One or more static asset budgets failed.",
        {"largestJavaScriptBytes": largest_bundle, "javascriptBudgetBytes": bundle_limit, "heroImageBytes": hero_size, "heroImageBudgetBytes": image_limit, **checks},
    )
    return 0 if status == "pass" else 1


def infrastructure() -> int:
    required = [
        ROOT / "Dockerfile",
        ROOT / "dashboard/Dockerfile",
        ROOT / "dashboard/compose.yml",
        ROOT / "deploy/kubernetes/kustomization.yaml",
        ROOT / "deploy/kubernetes/application.yaml",
        ROOT / "deploy/kubernetes/network-policy.yaml",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    manifests = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "deploy/kubernetes").glob("*.yaml")
    )
    image_evidence = Path(
        os.environ.get("IMAGE_EVIDENCE_FILE", "/tmp/zeaz-image-ids")
    )
    try:
        image_ids = [
            line.strip()
            for line in image_evidence.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError:
        image_ids = []
    images_built = (
        len(image_ids) == 2
        and all(
            len(identifier) == 71
            and identifier.startswith("sha256:")
            and all(character in "0123456789abcdef" for character in identifier[7:])
            for identifier in image_ids
        )
    )
    schema_evidence = Path(
        os.environ.get(
            "KUBERNETES_SCHEMA_EVIDENCE_FILE",
            "/tmp/zeaz-kubernetes-schema.sha256",
        )
    )
    try:
        schema_digest = schema_evidence.read_text(encoding="utf-8").strip()
    except OSError:
        schema_digest = ""
    schema_validated = len(schema_digest) == 64 and all(
        character in "0123456789abcdef" for character in schema_digest
    )
    policies = {
        "singleReplicaSQLite": "replicas: 1" in manifests and "type: Recreate" in manifests,
        "numericNonRootIdentity": manifests.count("runAsUser: 10001") >= 2
        and manifests.count("runAsGroup: 10001") >= 2,
        "persistentVolumeOwnership": "fsGroup: 10001" in manifests
        and "fsGroupChangePolicy: OnRootMismatch" in manifests,
        "readOnlyRootFilesystem": "readOnlyRootFilesystem: true" in manifests,
        "noServiceAccountTokens": "automountServiceAccountToken: false" in manifests,
        "resourceLimits": "limits:" in manifests and "requests:" in manifests,
        "healthProbes": "livenessProbe:" in manifests and "readinessProbe:" in manifests,
        "defaultDenyNetwork": "name: default-deny" in manifests,
        "controllerScopedIngress": manifests.count(
            "app.kubernetes.io/name: ingress-nginx"
        )
        >= 2,
        "authenticatedDashboardIngress": "auth-secret: dashboard-basic-auth"
        in manifests,
        "noLatestImages": ":latest" not in manifests,
        "noInlineSecret": "\nkind: Secret\n" not in f"\n{manifests}\n",
        "imagesBuilt": images_built,
        "kubernetesSchemaValidated": schema_validated,
    }
    status = "pass" if not missing and all(policies.values()) else "fail"
    write_report(
        "infrastructure",
        status,
        "Container builds and Kubernetes policy checks passed." if status == "pass" else "Deployment definitions or image validation are incomplete.",
        {"requiredFiles": len(required), "missingFiles": len(missing), **policies},
        [{"missing": item} for item in missing]
        + [{"failedPolicy": name} for name, passed in policies.items() if not passed],
    )
    return 0 if status == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    report = subparsers.add_parser("report")
    report.add_argument("name")
    report.add_argument("status", choices=("pass", "fail", "unknown", "not_applicable"))
    report.add_argument("summary")
    for name in ("security", "coverage", "performance", "infrastructure"):
        subparsers.add_parser(name)
    args = parser.parse_args()
    if args.command == "report":
        write_report(args.name, args.status, args.summary)
        return 0
    return globals()[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
