"""Runs the M6-INTERNAL diagnosis on every real domain corpus this
project has built (family/organization/supply_chain/library) plus their
union, across 10 seeds each, to answer -- on real data -- whether
`StructuralLearningPolicy` genuinely exploits `Rule x Context x Depth x
Provenance` when a rule HAS been partially observed in training
(unlike M6-TRANSFER's `split_by_rule()` holdout, which never lets this
happen at all).

Usage: python scripts/run_m6_internal_learning_diagnosis_v0_1.py
Output: validation/m6_internal_learning_diagnosis_v0_1_results_<date>.json
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from m6_corpus_from_library_v0_1 import build_library_corpus  # noqa: E402
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2  # noqa: E402
from m6_corpus_from_organization_v0_1 import build_organization_corpus  # noqa: E402
from m6_corpus_from_supply_chain_v0_1 import build_supply_chain_corpus  # noqa: E402
from m6_internal_learning_diagnosis_v0_1 import (  # noqa: E402
    result_to_dict,
    run_internal_learning_diagnosis_multi_seed,
)

SEEDS = tuple(range(10))
# Every real corpus this project has built caps out at exactly 2 records
# per rule (verified directly, not assumed) -- the default
# holdout_fraction=0.2 rounds DOWN to 0 held-out records for a 2-record
# rule (round(2*0.2)=0), which silently produces an empty holdout and
# `run_internal_learning_diagnosis` returning None everywhere, not
# because no rule is eligible but because none is ever aggressive
# enough to hold out even one record of one. 0.5 is the minimum fraction
# that actually holds out 1 of 2 records per eligible rule.
HOLDOUT_FRACTION = 0.5


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


def _summarize(results):
    deltas = [r.brier_delta for r in results]
    rates = [r.exact_or_rule_only_rate for r in results]
    return {
        "n_seeds_with_non_empty_split": len(results),
        "mean_exact_or_rule_only_rate": statistics.fmean(rates) if rates else None,
        "mean_brier_delta": statistics.fmean(deltas) if deltas else None,
        "stdev_brier_delta": statistics.stdev(deltas) if len(deltas) > 1 else (0.0 if deltas else None),
        "n_seeds_real_policy_beats_baseline": sum(1 for d in deltas if d < 0),
        "n_seeds_real_policy_worse_than_baseline": sum(1 for d in deltas if d > 0),
        "n_seeds_tied": sum(1 for d in deltas if d == 0),
        "mean_n_holdout": statistics.fmean(r.n_holdout for r in results) if results else None,
        "n_rules_eligible": results[0].n_rules_eligible if results else None,
    }


def main() -> int:
    domains = _domain_records()
    all_results = {}
    for domain, records in domains.items():
        results = run_internal_learning_diagnosis_multi_seed(records, domain=domain, seeds=SEEDS, holdout_fraction=HOLDOUT_FRACTION)
        all_results[domain] = {
            "n_records": len(records),
            "per_seed": [result_to_dict(r) for r in results],
            "summary": _summarize(results),
        }

    payload = {
        "experiment": "M6-INTERNAL diagnosis -- does StructuralLearningPolicy exploit Rule x Context x Depth x Provenance on a partially-seen rule?",
        "date_utc": date.today().isoformat(),
        "seeds": list(SEEDS),
        "domains": all_results,
    }

    out_path = REPO_ROOT / "validation" / f"m6_internal_learning_diagnosis_v0_1_results_{payload['date_utc']}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}\n")

    header = f"{'domain':<20} {'n_rec':>6} {'seeds':>6} {'n_rules_elig':>12} {'exact/rule_rate':>15} {'mean_delta':>11} {'stdev':>8} {'wins':>5} {'loses':>6}"
    print(header)
    for domain, data in all_results.items():
        s = data["summary"]
        if s["n_seeds_with_non_empty_split"] == 0:
            print(f"{domain:<20} {data['n_records']:>6}  every split produced an empty holdout at holdout_fraction={HOLDOUT_FRACTION} -- skipped")
            continue
        print(
            f"{domain:<20} {data['n_records']:>6} {s['n_seeds_with_non_empty_split']:>6} "
            f"{s['n_rules_eligible']:>12} {s['mean_exact_or_rule_only_rate']:>15.3f} "
            f"{s['mean_brier_delta']:>11.4f} {s['stdev_brier_delta']:>8.4f} "
            f"{s['n_seeds_real_policy_beats_baseline']:>5} {s['n_seeds_real_policy_worse_than_baseline']:>6}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
