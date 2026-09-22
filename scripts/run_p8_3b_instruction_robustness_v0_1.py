"""Runs P8.3b for real against the live Kev-0.8B server: LABELED only,
5 `instructions`-wording variants x 39 cases = 195 real HTTP calls,
criteria order fixed to the corpus's own (P8.1 baseline) order. See
`m7_jev_instruction_robustness_v0_1.py` for why the original wording
itself is not re-run here -- its result already exists, real and saved,
in `validation/jev_benchmark_v0_2_results_2026-09-22.json`.

Usage: python scripts/run_p8_3b_instruction_robustness_v0_1.py
Env:   KEV_BASE_URL (default http://192.168.1.11:8009)
Output: validation/jev_instruction_robustness_v0_1_results_<date>.json
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
from m7_jev_instruction_robustness_v0_1 import INSTRUCTION_VARIANTS, run_instruction_robustness  # noqa: E402
from m7_jev_order_ablation_v0_1 import summarize_order_ablation, summary_to_dict  # noqa: E402
from m7_jev_relation_choice_v0_1 import DEFAULT_LABELED_GLOSSED_INSTRUCTIONS, JevKevSystemOneClient  # noqa: E402

KEV_BASE_URL = os.environ.get("KEV_BASE_URL", "http://192.168.1.11:8009")


def main() -> int:
    client = JevKevSystemOneClient(KEV_BASE_URL)
    if not client.reachable():
        print(f"Kev server not reachable at {KEV_BASE_URL} -- aborting, no partial run.", file=sys.stderr)
        return 1

    _vocabulary, _demonstration_set, cases = load_corpus()
    n_calls = len(INSTRUCTION_VARIANTS) * len(cases)
    print(f"Running {len(INSTRUCTION_VARIANTS)} instruction variants x {len(cases)} cases = {n_calls} real HTTP calls against {KEV_BASE_URL} ...")
    started = time.monotonic()
    reports = run_instruction_robustness(client)
    elapsed = time.monotonic() - started
    print(f"Done in {elapsed:.1f}s ({elapsed / n_calls:.2f}s/call).")

    summary = summarize_order_ablation(reports)

    result = {
        "experiment": "P8.3b -- LABELED instructions-wording robustness",
        "date_utc": date.today().isoformat(),
        "kev_base_url": KEV_BASE_URL,
        "n_variants": len(INSTRUCTION_VARIANTS),
        "n_cases_per_variant": len(cases),
        "n_calls": n_calls,
        "elapsed_seconds": elapsed,
        "variants": dict(INSTRUCTION_VARIANTS),
        "baseline_reference": {
            "original_instructions": DEFAULT_LABELED_GLOSSED_INSTRUCTIONS,
            "note": (
                "The original wording itself is not re-run here -- see "
                "validation/jev_benchmark_v0_2_results_2026-09-22.json for its "
                "already-saved real result (overall=0.744, positive=0.750, "
                "adversarial=0.737, brier=0.377, ece=0.137; 4/4 conjoint paraphrases resisted)."
            ),
        },
        "variant_reports": [report_to_dict(r) for r in reports],
        "variant_summary": summary_to_dict(summary),
    }

    out_path = REPO_ROOT / "validation" / f"jev_instruction_robustness_v0_1_results_{result['date_utc']}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}")

    print("\n--- variant summary (5 instruction-wording variants) ---")
    print(json.dumps(summary_to_dict(summary), indent=2, ensure_ascii=False))
    print("\n--- per-variant headline numbers ---")
    for r in reports:
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
