"""Runs both measures of the M6-INTERNAL regularization diagnosis:

Measure A -- GLOBAL_ONLY / M6_RAW / M6_LAPLACE_A1 / M6_LAPLACE_A0.5 /
             M6_SUPPORT_WEIGHTED_K1 compared on the real domain corpora
             (family/organization/supply_chain/library + their union),
             10 seeds each, same `split_within_rule()` protocol as
             `m6_internal_learning_diagnosis_v0_1.py`.
Measure B -- the same 5 variants compared on a controlled synthetic
             convergence benchmark (known true distributions 90/10,
             50/50, 70/30 at support levels 1/2/5/10/20), scored
             against the KNOWN true distribution directly.

Usage: python scripts/run_m6_internal_regularized_diagnosis_v0_1.py
Output: validation/m6_internal_regularized_diagnosis_v0_1_results_<date>.json
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from m4_cold_start_evidence_v0_1 import CONTRADICTED, SUPPORTED  # noqa: E402
from m6_corpus_from_library_v0_1 import build_library_corpus  # noqa: E402
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2  # noqa: E402
from m6_corpus_from_organization_v0_1 import build_organization_corpus  # noqa: E402
from m6_corpus_from_supply_chain_v0_1 import build_supply_chain_corpus  # noqa: E402
from m6_internal_regularized_diagnosis_v0_1 import (  # noqa: E402
    build_policy_variants,
    comparison_result_to_dict,
    run_convergence_benchmark,
    run_regularized_comparison_multi_seed,
)

SEEDS = tuple(range(10))
HOLDOUT_FRACTION = 0.5  # see m6_internal_learning_diagnosis_v0_1.py: every real corpus caps at 2 records/rule
VARIANT_NAMES = tuple(build_policy_variants().keys())
SUPPORTS = (1, 2, 5, 10, 20)
TRUE_DISTRIBUTIONS = {
    "skewed_90_10": {SUPPORTED: 0.9, CONTRADICTED: 0.1},
    "balanced_50_50": {SUPPORTED: 0.5, CONTRADICTED: 0.5},
    "skewed_70_30": {SUPPORTED: 0.7, CONTRADICTED: 0.3},
}


def _domain_records():
    family = build_real_corpus_v2().records
    organization = build_organization_corpus().records
    supply_chain = build_supply_chain_corpus().records
    library = build_library_corpus().records
    combined = family + organization + supply_chain + library
    return {
        "family": family,
        "organization": organization,
        "supply_chain": supply_chain,
        "library": library,
        "combined_4_domains": combined,
    }


def _summarize_measure_a(results):
    summary = {}
    for name in VARIANT_NAMES:
        if name == "GLOBAL_ONLY":
            continue
        deltas = [r.brier_delta_vs_global_only(name) for r in results]
        summary[name] = {
            "mean_brier_delta_vs_global_only": statistics.fmean(deltas) if deltas else None,
            "stdev_brier_delta": statistics.stdev(deltas) if len(deltas) > 1 else (0.0 if deltas else None),
            "n_seeds_beats_global_only": sum(1 for d in deltas if d < 0),
            "n_seeds_worse_than_global_only": sum(1 for d in deltas if d > 0),
        }
    summary["mean_brier"] = {
        name: statistics.fmean(r.brier[name] for r in results) if results else None for name in VARIANT_NAMES
    }
    summary["mean_ece"] = {
        name: statistics.fmean(r.ece[name] for r in results) if results else None for name in VARIANT_NAMES
    }
    summary["n_seeds_with_non_empty_split"] = len(results)
    return summary


def run_measure_a():
    domains = _domain_records()
    all_results = {}
    for domain, records in domains.items():
        results = run_regularized_comparison_multi_seed(records, domain=domain, seeds=SEEDS, holdout_fraction=HOLDOUT_FRACTION)
        all_results[domain] = {
            "n_records": len(records),
            "per_seed": [comparison_result_to_dict(r) for r in results],
            "summary": _summarize_measure_a(results),
        }
    return all_results


def run_measure_b():
    return run_convergence_benchmark(TRUE_DISTRIBUTIONS, supports=SUPPORTS, n_trials=500, seed=0)


def main() -> int:
    print("Running Measure A (real corpora, 10 seeds x 5 configurations) ...")
    measure_a = run_measure_a()
    print("Running Measure B (synthetic convergence, 3 distributions x 5 support levels, 500 trials each) ...")
    measure_b = run_measure_b()

    payload = {
        "experiment": "M6-INTERNAL regularization diagnosis -- does smoothing fix the support=1 overconfidence deficit?",
        "date_utc": date.today().isoformat(),
        "measure_a_real_corpora": measure_a,
        "measure_b_synthetic_convergence": measure_b,
    }

    out_path = REPO_ROOT / "validation" / f"m6_internal_regularized_diagnosis_v0_1_results_{payload['date_utc']}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}\n")

    print("--- Measure A: mean Brier delta vs GLOBAL_ONLY (negative = variant wins) ---")
    header = f"{'domain':<20}" + "".join(f"{name:>18}" for name in VARIANT_NAMES if name != "GLOBAL_ONLY")
    print(header)
    for domain, data in measure_a.items():
        s = data["summary"]
        if s["n_seeds_with_non_empty_split"] == 0:
            print(f"{domain:<20}  (empty split)")
            continue
        row = f"{domain:<20}"
        for name in VARIANT_NAMES:
            if name == "GLOBAL_ONLY":
                continue
            row += f"{s[name]['mean_brier_delta_vs_global_only']:>18.4f}"
        print(row)

    print("\n--- Measure B: mean squared distance to true distribution (lower is better) ---")
    for label, by_support in measure_b.items():
        print(f"\n{label}:")
        header = f"{'support':>8}" + "".join(f"{name:>18}" for name in VARIANT_NAMES)
        print(header)
        for n in SUPPORTS:
            row = f"{n:>8}"
            for name in VARIANT_NAMES:
                row += f"{by_support[n][name]:>18.5f}"
            print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
