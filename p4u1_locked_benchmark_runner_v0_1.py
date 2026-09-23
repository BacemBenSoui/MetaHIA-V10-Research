"""P4-U.1 -- locked train/holdout/witness benchmark runner.

Runs the full protocol v0.3 pipeline (Gate A -> Gate B, unchanged --
`p4u1_unsupervised_pattern_discovery_v0_1.py` -- -> Gate C, redefined
as set-valued replay -- `p4u1_set_valued_replay_v0_1.py`) against the
three locked cases (U1/U2/U3) in
`p4u1_locked_benchmark_cases_v0_1.py`, with the exact numeric
thresholds fixed there BEFORE any holdout comparison (`GATE_PARAMS`).

Mirrors `p4t_locked_benchmark_runner_v0_1.py`'s own non-circularity
discipline, enforced MECHANICALLY, not by promise:

  1. `run_discovery_and_gates()` reads ONLY
     `p4u1_locked_benchmark_cases_v0_1.py` (train + holdout
     observations, and the DECLARED candidate skeletons -- never a
     Gate A/B/C outcome). Its source code never names
     `p4u1_locked_benchmark_witness_v0_1`.
  2. `commit_predictions()` writes the resulting predictions to
     `validation/p4u1_locked_benchmark_predictions_v0_1.json`,
     timestamped, BEFORE any witness data has been read.
  3. `reveal_and_compare()` is the ONLY function in this module that
     imports the witness module -- and only after predictions are
     already committed.
  4. `run_locked_benchmark()` composes the three steps in that exact
     order and additionally proves, dynamically via `sys.modules`,
     that the witness module was absent at the moment of commit.

Like `p4t_locked_benchmark_runner_v0_1.py`, this is a
SELF-ADMINISTERED, structurally-enforced protocol -- not a
third-party-witnessed gate closure. What it demonstrates is that
discovery, Gate B, and Gate C are mechanically incapable of having
read the answer before committing to one, exactly the concrete half of
a locked benchmark this project already applies to P4-T/M6/M7.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from p4u1_unsupervised_pattern_discovery_v0_1 import (
    GATE_A_DISCOVERED,
    GATE_A_NOT_DISCOVERED,
    GATE_B_RETAINED,
    GATE_C_NOT_APPLICABLE,
    discover_candidates,
    evaluate_gate_b,
    freeze_pattern,
    null_max_support_distribution,
)
from p4u1_set_valued_replay_v0_1 import (
    evaluate_gate_c_set_valued,
    replay_on_all_admissible_starts_set_valued,
)
from p4u1_locked_benchmark_cases_v0_1 import GATE_PARAMS, LOCKED_CASES

WITNESS_MODULE_NAME = "p4u1_locked_benchmark_witness_v0_1"
PREDICTIONS_PATH = Path(__file__).resolve().parent / "validation" / "p4u1_locked_benchmark_predictions_v0_1.json"


@dataclass(frozen=True)
class CandidatePrediction:
    case_id: str
    label: str
    gate_a: str  # DISCOVERED | NOT_DISCOVERED
    gate_b: Optional[str]  # RETAINED | REJECTED | None (never evaluated)
    gate_b_rejection_reason: Optional[str]
    gate_c: Optional[str]  # REPLICATED | FAILED | NOT_APPLICABLE | None (never evaluated)
    support_train: Optional[int]
    support_holdout: Optional[int]
    coverage: Optional[float]


def run_discovery_and_gates() -> Tuple[CandidatePrediction, ...]:
    """Gate A + B + C on every declared candidate of every locked case.
    Reads train/holdout observations and DECLARED skeletons only --
    `p4u1_locked_benchmark_cases_v0_1.py` carries no outcome
    information for this function to read even by accident. This
    function's own source code never names the witness module
    (verified statically by `tests/test_p4u1_locked_benchmark_v0_1.py`)."""
    results = []
    for case in LOCKED_CASES:
        candidates = discover_candidates(
            case.train_observations,
            min_depth=GATE_PARAMS["min_depth"],
            max_depth=GATE_PARAMS["max_depth"],
            max_paths=GATE_PARAMS["max_paths"],
        )
        by_skeleton = {c.skeleton: c for c in candidates}
        null_dist_train = null_max_support_distribution(
            case.train_observations,
            min_depth=GATE_PARAMS["min_depth"],
            max_depth=GATE_PARAMS["max_depth"],
            n_null=GATE_PARAMS["n_null"],
            seed_base=case.null_seed_base_train,
            max_paths=GATE_PARAMS["max_paths"],
        )
        # Computed once per CASE, not once per candidate: every candidate
        # that reaches Gate C within the same case shares the same
        # G_holdout, so its null-max distribution (Sec. 10.2(b)) is
        # identical for all of them -- recomputing it per candidate would
        # be a pure, avoidable multiplication of an already expensive
        # (200-replicate) computation.
        null_dist_holdout = (
            null_max_support_distribution(
                case.holdout_observations,
                min_depth=GATE_PARAMS["min_depth"], max_depth=GATE_PARAMS["max_depth"],
                n_null=GATE_PARAMS["n_null"], seed_base=case.null_seed_base_holdout,
                max_paths=GATE_PARAMS["max_paths"],
            )
            if case.holdout_observations
            else ()
        )

        for declared in case.candidates:
            found = by_skeleton.get(declared.skeleton)
            if found is None:
                results.append(
                    CandidatePrediction(case.case_id, declared.label, GATE_A_NOT_DISCOVERED, None, None, None, None, None, None)
                )
                continue

            gate_b = evaluate_gate_b(
                found, null_dist_train,
                min_depth=GATE_PARAMS["min_depth"], s_min=GATE_PARAMS["s_min"],
                null_percentile=GATE_PARAMS["null_percentile"],
            )
            if gate_b.outcome != GATE_B_RETAINED:
                results.append(
                    CandidatePrediction(
                        case.case_id, declared.label, GATE_A_DISCOVERED, gate_b.outcome, gate_b.rejection_reason,
                        GATE_C_NOT_APPLICABLE, found.support, None, None,
                    )
                )
                continue

            if not case.holdout_observations:
                results.append(
                    CandidatePrediction(
                        case.case_id, declared.label, GATE_A_DISCOVERED, gate_b.outcome, None,
                        GATE_C_NOT_APPLICABLE, found.support, None, None,
                    )
                )
                continue

            frozen = freeze_pattern(
                gate_b.pattern, frozen_id=f"LOCKED::{case.case_id}::{declared.label}",
                support_train=found.support, metadata={},
            )
            replication = replay_on_all_admissible_starts_set_valued(
                frozen, case.holdout_observations, max_paths=GATE_PARAMS["max_paths"]
            )
            gate_c = evaluate_gate_c_set_valued(
                replication, null_dist_holdout,
                k_min=GATE_PARAMS["k_min"], coverage_min=GATE_PARAMS["coverage_min"],
                null_percentile=GATE_PARAMS["null_percentile"],
            )
            results.append(
                CandidatePrediction(
                    case.case_id, declared.label, GATE_A_DISCOVERED, gate_b.outcome, None,
                    gate_c.outcome, found.support, replication.support_holdout, replication.coverage,
                )
            )
    return tuple(results)


def commit_predictions(predictions) -> Path:
    """Writes predictions to disk BEFORE any witness data is consulted --
    the same 'package remis avant exécution' checkpoint as P4-T's own
    runner. Once written, this file is the timestamped, locked record
    of what was predicted blind."""
    payload = {
        "committed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "witness_module_imported_yet": WITNESS_MODULE_NAME in sys.modules,
        "gate_params": GATE_PARAMS,
        "predictions": [
            {
                "case_id": p.case_id,
                "label": p.label,
                "gate_a": p.gate_a,
                "gate_b": p.gate_b,
                "gate_b_rejection_reason": p.gate_b_rejection_reason,
                "gate_c": p.gate_c,
                "support_train": p.support_train,
                "support_holdout": p.support_holdout,
                "coverage": p.coverage,
            }
            for p in predictions
        ],
    }
    PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return PREDICTIONS_PATH


@dataclass(frozen=True)
class CaseComparison:
    case_id: str
    label: str
    gate_a_matches_witness: bool
    gate_b_matches_witness: bool
    gate_c_matches_witness: bool

    @property
    def all_match(self) -> bool:
        return self.gate_a_matches_witness and self.gate_b_matches_witness and self.gate_c_matches_witness


def reveal_and_compare(predictions) -> Tuple[CaseComparison, ...]:
    """The ONLY function in this module that imports the witness module
    -- called strictly after `commit_predictions()`. Compares the
    already-committed predictions against truth; it never re-runs
    discovery, so the comparison itself cannot influence what was
    predicted."""
    from p4u1_locked_benchmark_witness_v0_1 import WITNESS_EXPECTED  # noqa: PLC0415

    comparisons = []
    for p in predictions:
        expected = WITNESS_EXPECTED[(p.case_id, p.label)]
        comparisons.append(
            CaseComparison(
                case_id=p.case_id,
                label=p.label,
                gate_a_matches_witness=(p.gate_a == expected["gate_a"]),
                gate_b_matches_witness=(p.gate_b == expected["gate_b"]),
                gate_c_matches_witness=(p.gate_c == expected["gate_c"]),
            )
        )
    return tuple(comparisons)


@dataclass(frozen=True)
class LockedBenchmarkReport:
    predictions: Tuple[CandidatePrediction, ...]
    comparisons: Tuple[CaseComparison, ...]
    predictions_path: str
    witness_imported_before_commit: bool


def run_locked_benchmark() -> LockedBenchmarkReport:
    """Composes the full protocol in the enforced order and returns a
    report including a DYNAMIC proof (not just a textual one) that the
    witness module was absent from `sys.modules` at the moment
    predictions were committed."""
    predictions = run_discovery_and_gates()
    witness_imported_before_commit = WITNESS_MODULE_NAME in sys.modules
    path = commit_predictions(predictions)
    comparisons = reveal_and_compare(predictions)
    return LockedBenchmarkReport(
        predictions=predictions,
        comparisons=comparisons,
        predictions_path=str(path),
        witness_imported_before_commit=witness_imported_before_commit,
    )


__all__ = [
    "CandidatePrediction",
    "CaseComparison",
    "LockedBenchmarkReport",
    "WITNESS_MODULE_NAME",
    "commit_predictions",
    "reveal_and_compare",
    "run_discovery_and_gates",
    "run_locked_benchmark",
]


if __name__ == "__main__":
    report = run_locked_benchmark()
    for comparison in report.comparisons:
        print(comparison)
    print("witness imported before commit:", report.witness_imported_before_commit)
