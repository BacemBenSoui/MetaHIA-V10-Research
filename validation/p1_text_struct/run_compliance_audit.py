#!/usr/bin/env python3
"""Command-line wrapper around compliance_audit.py (frozen at GEL 1, deliberately not modified).

Produces the three levels of the compliance report required by the project owner:
  1. static audit of the gateway source (compliance_audit.audit_gateway);
  2. negative tests (tests/test_p1_text_struct_*: deliberately non-compliant gateways must fail);
  3. manifest / execution environment: gateway fingerprint, imports actually loaded, Python version.
It states what was checked and what was not: a static audit is not a proof that no semantic
knowledge can exist in the gateway.

    python validation/p1_text_struct/run_compliance_audit.py validation/p1_text_struct/gateway_a.py [--report OUT.json]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ALLOWED_FILES = {"gateway_a.py"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("gateway", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    audit = _load(HERE / "compliance_audit.py", "p1ts_compliance_audit")
    static = audit.audit_gateway(args.gateway, ALLOWED_FILES)
    before = set(sys.modules)
    _load(args.gateway, "p1ts_gateway_under_audit")
    loaded = sorted(m for m in set(sys.modules) - before if not m.startswith("p1ts_"))
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            "tests/test_p1_text_struct_scorer_v0_1.py", "tests/test_p1_text_struct_gateway_a_v0_1.py",
                            "-k", "compliant or non_compliant or forbidden or contaminated or compliance_audit"],
                           cwd=ROOT, capture_output=True, text=True)
    report = {
        "level_1_static_audit": {"violations": static, "count": len(static)},
        "level_2_negative_tests": {"returncode": tests.returncode, "summary": tests.stdout.strip().splitlines()[-1:]},
        "level_3_manifest": {
            "gateway": str(args.gateway.relative_to(ROOT)) if args.gateway.is_absolute() else str(args.gateway),
            "gateway_sha256": hashlib.sha256(args.gateway.read_bytes()).hexdigest(),
            "modules_newly_loaded_by_import": loaded,
            "python": platform.python_version(),
        },
        "not_checked": [
            "semantic knowledge encoded in control flow or string literals inside functions (review only)",
            "correctness of the closed-class lists themselves (review only)",
        ],
        "compliant": not static and tests.returncode == 0,
    }
    text = json.dumps(report, indent=1, ensure_ascii=False)
    if args.report:
        args.report.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["compliant"] else 1


if __name__ == "__main__":
    sys.exit(main())
