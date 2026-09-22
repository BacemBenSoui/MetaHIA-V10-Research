"""Runs P8.4 for real against the live Kev-0.8B server: 4 hand-controlled
integration checks, only 2 distinct real HTTP calls (the proposal cache
in `run_integration_checks` reuses one JEV call across the 2 check pairs
that share the same independent text). LABELED's FROZEN baseline
configuration (original criteria order + original instructions -- see
`m7_jev_m4_integration_v0_1.py`'s module docstring for why the
separately-measured "best" order/wording are not combined here).

Usage: python scripts/run_p8_4_m4_integration_v0_1.py
Env:   KEV_BASE_URL (default http://192.168.1.11:8009)
Output: validation/jev_m4_integration_v0_1_results_<date>.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from m7_jev_m4_integration_v0_1 import CHECKS, outcome_to_dict, run_integration_checks  # noqa: E402
from m7_jev_relation_choice_v0_1 import JevKevSystemOneClient  # noqa: E402

KEV_BASE_URL = os.environ.get("KEV_BASE_URL", "http://192.168.1.11:8009")


def main() -> int:
    client = JevKevSystemOneClient(KEV_BASE_URL)
    if not client.reachable():
        print(f"Kev server not reachable at {KEV_BASE_URL} -- aborting, no partial run.", file=sys.stderr)
        return 1

    print(f"Running {len(CHECKS)} integration checks (2 distinct real HTTP calls expected) against {KEV_BASE_URL} ...")
    outcomes = run_integration_checks(client)

    rows = [outcome_to_dict(o) for o in outcomes]
    result = {
        "experiment": "P8.4 -- LABELED to M4 integration (does M4 contain a known LABELED misclassification?)",
        "date_utc": date.today().isoformat(),
        "kev_base_url": KEV_BASE_URL,
        "n_checks": len(outcomes),
        "checks": rows,
    }

    out_path = REPO_ROOT / "validation" / f"jev_m4_integration_v0_1_results_{result['date_utc']}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}")

    print("\n--- per-check result ---")
    header = f"{'check_id':<36} {'candidate':<10} {'jev_says':<10} {'default':<13} {'prov_aware':<13} {'correct':<13} {'default_ok':<11} {'prov_ok'}"
    print(header)
    for row in rows:
        print(
            f"{row['check_id']:<36} {row['structural_candidate_relation']:<10} "
            f"{str(row['jev_classified_relation']):<10} {row['default_final_state']:<13} "
            f"{row['provenance_aware_final_state']:<13} {row['correct_final_state']:<13} "
            f"{str(row['default_matches_ground_truth']):<11} {row['provenance_aware_matches_ground_truth']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
