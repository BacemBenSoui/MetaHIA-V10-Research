"""Runs the M6 context-transfer diagnosis on every real domain corpus
this project has built (family/organization/supply_chain/library) plus
their union, across 10 seeds each, to answer -- on real data, not by
construction alone -- whether context (novelty/redundancy/depth/
provenance) alone carries any predictive signal that transfers to an
unseen rule, beyond the flat global prior BASIS_GLOBAL_PRIOR already
falls back to on every holdout evaluation this project has ever run.

Usage: python scripts/run_m6_context_transfer_diagnosis_v0_1.py
Output: validation/m6_context_transfer_diagnosis_v0_1_results_<date>.json
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from m6_context_transfer_diagnosis_v0_1 import (  # noqa: E402
    result_to_dict,
    run_context_transfer_diagnosis_multi_seed,
)
from m6_corpus_from_library_v0_1 import build_library_corpus  # noqa: E402
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2  # noqa: E402
from m6_corpus_from_organization_v0_1 import build_organization_corpus  # noqa: E402
from m6_corpus_from_supply_chain_v0_1 import build_supply_chain_corpus  # noqa: E402

SEEDS = tuple(range(10))


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
    return {
        "n_seeds_with_non_empty_split": len(results),
        "mean_brier_delta": statistics.fmean(deltas) if deltas else None,
        "stdev_brier_delta": statistics.stdev(deltas) if len(deltas) > 1 else (0.0 if deltas else None),
        "n_seeds_context_beats_global": sum(1 for d in deltas if d < 0),
        "n_seeds_context_worse_than_global": sum(1 for d in deltas if d > 0),
        "n_seeds_tied": sum(1 for d in deltas if d == 0),
        "mean_n_holdout_hitting_context_bucket": (
            statistics.fmean(r.n_holdout_hitting_context_bucket for r in results) if results else None
        ),
        "mean_n_holdout": statistics.fmean(r.n_holdout for r in results) if results else None,
    }


def main() -> int:
    domains = _domain_records()
    all_results = {}
    for domain, records in domains.items():
        results = run_context_transfer_diagnosis_multi_seed(records, domain=domain, seeds=SEEDS)
        all_results[domain] = {
            "n_records": len(records),
            "per_seed": [result_to_dict(r) for r in results],
            "summary": _summarize(results),
        }

    payload = {
        "experiment": "M6 context-transfer diagnosis -- does context alone transfer across rules on real corpora?",
        "date_utc": date.today().isoformat(),
        "seeds": list(SEEDS),
        "domains": all_results,
    }

    out_path = REPO_ROOT / "validation" / f"m6_context_transfer_diagnosis_v0_1_results_{payload['date_utc']}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}\n")

    header = f"{'domain':<20} {'n_rec':>6} {'seeds':>6} {'mean_delta':>12} {'stdev':>8} {'ctx_wins':>9} {'ctx_loses':>10} {'ties':>5} {'mean_hit':>9}"
    print(header)
    for domain, data in all_results.items():
        s = data["summary"]
        print(
            f"{domain:<20} {data['n_records']:>6} {s['n_seeds_with_non_empty_split']:>6} "
            f"{s['mean_brier_delta']:>12.4f} {s['stdev_brier_delta']:>8.4f} "
            f"{s['n_seeds_context_beats_global']:>9} {s['n_seeds_context_worse_than_global']:>10} "
            f"{s['n_seeds_tied']:>5} {s['mean_n_holdout_hitting_context_bucket']:>9.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
