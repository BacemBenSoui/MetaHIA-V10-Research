"""Runs P8.3a for real against the live Kev-0.8B server: LABELED only,
13 criteria orders (3 designed + 10 random seeds) x 39 cases = 507 real
HTTP calls. See `m7_jev_label_order_ablation_v0_1.py` for why this is
LABELED-only and why the original (unpermuted) P8.1 order is not
re-run here -- its result already exists, real and saved, in
`validation/jev_benchmark_v0_2_results_2026-09-22.json`.

Usage: python scripts/run_p8_3a_label_order_ablation_v0_1.py
Env:   KEV_BASE_URL (default http://192.168.1.11:8009)
Output: validation/jev_label_order_ablation_v0_1_results_<date>.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from m7_jev_benchmark_v0_2 import load_corpus, report_to_dict  # noqa: E402
from m7_jev_label_order_ablation_v0_1 import (  # noqa: E402
    LabelOrderedCondition,
    build_aucune_first_label_order,
    build_label_seed_orders,
    build_separated_label_order,
    run_label_order_ablation,
)
from m7_jev_order_ablation_v0_1 import summarize_order_ablation, summary_to_dict  # noqa: E402
from m7_jev_relation_choice_v0_1 import JevKevSystemOneClient  # noqa: E402

KEV_BASE_URL = os.environ.get("KEV_BASE_URL", "http://192.168.1.11:8009")
SEEDS = tuple(range(1, 11))  # 10 seeds, same convention as P8.2


def main() -> int:
    client = JevKevSystemOneClient(KEV_BASE_URL)
    if not client.reachable():
        print(f"Kev server not reachable at {KEV_BASE_URL} -- aborting, no partial run.", file=sys.stderr)
        return 1

    vocabulary, _demonstration_set, cases = load_corpus()
    designed = (
        LabelOrderedCondition(label="LABELED_separated", relations=build_separated_label_order(vocabulary)),
        LabelOrderedCondition(label="LABELED_aucune_first", relations=build_aucune_first_label_order(vocabulary)),
        LabelOrderedCondition(label="LABELED_reversed", relations=tuple(reversed(vocabulary))),
    )
    seed_conditions = build_label_seed_orders(vocabulary, seeds=SEEDS)
    orders = designed + seed_conditions

    n_calls = len(orders) * len(cases)
    print(f"Running {len(orders)} orders x {len(cases)} cases = {n_calls} real HTTP calls against {KEV_BASE_URL} ...")
    started = time.monotonic()
    reports = run_label_order_ablation(client, orders)
    elapsed = time.monotonic() - started
    print(f"Done in {elapsed:.1f}s ({elapsed / n_calls:.2f}s/call).")

    designed_reports = reports[: len(designed)]
    seed_reports = reports[len(designed):]
    seed_summary = summarize_order_ablation(seed_reports)

    result = {
        "experiment": "P8.3a -- LABELED criteria-order ablation",
        "date_utc": date.today().isoformat(),
        "kev_base_url": KEV_BASE_URL,
        "n_orders": len(orders),
        "n_cases_per_order": len(cases),
        "n_calls": n_calls,
        "elapsed_seconds": elapsed,
        "seeds": list(SEEDS),
        "baseline_reference": {
            "note": (
                "The original (unpermuted, ['EPOUX_DE','EPOUSE_DE','MERE_DE','PERE_DE','AUCUNE']) "
                "P8.1 LABELED order is not re-run here -- see "
                "validation/jev_benchmark_v0_2_results_2026-09-22.json for its already-saved "
                "real result (overall=0.744, positive=0.750, adversarial=0.737, brier=0.377, "
                "ece=0.137; 4/4 EPOUX_DE predicted EPOUSE_DE)."
            ),
        },
        "designed_reports": [report_to_dict(r) for r in designed_reports],
        "seed_reports": [report_to_dict(r) for r in seed_reports],
        "seed_summary": summary_to_dict(seed_summary),
    }

    out_path = REPO_ROOT / "validation" / f"jev_label_order_ablation_v0_1_results_{result['date_utc']}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}")

    print("\n--- seed summary (10 random criteria orders) ---")
    print(json.dumps(summary_to_dict(seed_summary), indent=2, ensure_ascii=False))
    print("\n--- designed orders (separated / aucune_first / reversed) ---")
    for r in designed_reports:
        print(
            json.dumps(
                {k: v for k, v in report_to_dict(r).items() if k != "cases"},
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
