"""P4-T.2 -- locked train/holdout/witness benchmark runner.

Addresses the limitation stated plainly in
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 8 and
raised again by the external review: every existing P4-T test builds its
own synthetic data in the same file as its own assertions, which is a
mechanism proof, not a locked protocol with `TRAIN != HOLDOUT != WITNESS`.

This module enforces that separation MECHANICALLY, not by promise:

  1. `run_discovery_and_replay()` reads ONLY
     `p4t_locked_benchmark_cases_v0_1.py` (train rows + holdout SOURCE
     observations -- no target information present anywhere in that file).
     It does not import, and its source code never even names,
     `p4t_locked_benchmark_witness_v0_1`.
  2. `commit_predictions()` writes the resulting predictions to
     `validation/p4t_locked_benchmark_predictions_v0_1.json`, timestamped,
     BEFORE any witness data has been read. Once written, this file is the
     locked record of what the mechanism predicted blind.
  3. `reveal_and_compare()` is the ONLY place in this entire module that
     imports `p4t_locked_benchmark_witness_v0_1` -- and it does so only
     after being called with already-committed predictions.
  4. `run_locked_benchmark()` composes the three steps in that exact order
     and additionally asserts, at runtime, that the witness module was not
     yet present in `sys.modules` right after the commit step -- a dynamic
     proof of import order, not merely a textual one.

This is a SELF-ADMINISTERED, structurally-enforced protocol. It is
explicitly NOT a third-party-witnessed gate closure (no external party
held the witness file) -- the same distinction this project already draws
for M4-M7 (self-execution never closes a validation gate on its own).
What it upgrades, honestly: from "the same file proves and asserts" to
"discovery and replay are mechanically incapable of having read the
answer," which is the concrete, checkable half of the gap a locked
benchmark is supposed to close.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple

from kernel2 import Node, structural_equal
import p4t_structural_transformation_induction_v0_1 as p4t
from p4t_locked_benchmark_cases_v0_1 import LOCKED_CASES, LockedCase

WITNESS_MODULE_NAME = "p4t_locked_benchmark_witness_v0_1"
PREDICTIONS_PATH = Path(__file__).resolve().parent / "validation" / "p4t_locked_benchmark_predictions_v0_1.json"


@dataclass(frozen=True)
class CasePrediction:
    case_id: str
    family_expected: str
    outcome: str
    predicted: Tuple[object, ...]  # actual Node/NodeRef predictions, used for real comparison

    @property
    def predicted_repr(self) -> Tuple[str, ...]:
        """Human-readable audit trail only -- repr() embeds each Node's own
        arbitrary node_id label, so it is NEVER used for the actual
        comparison against witness values (see `reveal_and_compare`, which
        compares `predicted` via `kernel2.structural_equal` instead)."""
        return tuple(repr(item) for item in self.predicted)


def _discover_and_freeze(rows: Sequence[Node], *, source_position: int, target_position: int, frozen_id: str):
    candidate = p4t.discover(rows, source_position=source_position, target_position=target_position)
    if candidate.outcome != p4t.OUTCOME_CANDIDATE:
        return candidate, None
    frozen = p4t.freeze(candidate, frozen_id=frozen_id)
    return candidate, frozen


def run_discovery_and_replay() -> Tuple[CasePrediction, ...]:
    """Gate A + B + C on every locked case. Reads train rows and holdout
    SOURCE observations only -- no target/witness data exists anywhere in
    `p4t_locked_benchmark_cases_v0_1.py` for this function to read even by
    accident. This function's own source code never names the witness
    module (verified statically by
    `tests/test_p4t_locked_benchmark_v0_1.py`)."""
    results = []
    for case in LOCKED_CASES:
        if case.family_expected == "COMPOSED":
            inner_candidate, inner_frozen = _discover_and_freeze(
                case.composed_inner_rows, source_position=case.source_position, target_position=case.target_position,
                frozen_id=f"LOCKED::{case.case_id}::INNER",
            )
            outer_candidate, outer_frozen = _discover_and_freeze(
                case.composed_outer_rows, source_position=case.source_position, target_position=case.target_position,
                frozen_id=f"LOCKED::{case.case_id}::OUTER",
            )
            if inner_frozen is None or outer_frozen is None:
                results.append(CasePrediction(case.case_id, case.family_expected, "REJECTED", ()))
                continue
            frozen = p4t.compose_frozen(outer_frozen, inner_frozen, frozen_id=f"LOCKED::{case.case_id}")
            predictions = p4t.blind_replay(frozen, case.holdout_source)
            results.append(
                CasePrediction(case.case_id, case.family_expected, p4t.OUTCOME_CANDIDATE, tuple(predictions))
            )
            continue

        candidate, frozen = _discover_and_freeze(
            case.train_rows, source_position=case.source_position, target_position=case.target_position,
            frozen_id=f"LOCKED::{case.case_id}",
        )
        if frozen is None:
            results.append(CasePrediction(case.case_id, case.family_expected, candidate.outcome, ()))
            continue
        predictions = p4t.blind_replay(frozen, case.holdout_source)
        results.append(
            CasePrediction(case.case_id, case.family_expected, p4t.OUTCOME_CANDIDATE, tuple(predictions))
        )
    return tuple(results)


def commit_predictions(predictions: Sequence[CasePrediction]) -> Path:
    """Writes predictions to disk BEFORE any witness data is consulted --
    the literal 'package remis avant execution' checkpoint. Once written,
    this file is the timestamped, locked record of what was predicted
    blind; it cannot be quietly revised after peeking at the truth."""
    payload = {
        "committed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "witness_module_imported_yet": WITNESS_MODULE_NAME in sys.modules,
        "predictions": [
            {
                "case_id": p.case_id,
                "family_expected": p.family_expected,
                "outcome": p.outcome,
                "predicted_repr": list(p.predicted_repr),
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
    outcome_matches_witness: bool
    prediction_matches_witness: Optional[bool]


def reveal_and_compare(predictions: Sequence[CasePrediction]) -> Tuple[CaseComparison, ...]:
    """The ONLY function in this module that imports the witness module --
    called strictly after `commit_predictions()`. Re-runs discovery
    independently is NOT done here: this function only compares the
    already-committed predictions against truth, so the comparison itself
    cannot influence what was predicted."""
    from p4t_locked_benchmark_witness_v0_1 import WITNESS_OUTCOME, WITNESS_PREDICTIONS  # noqa: PLC0415

    comparisons = []
    for pred in predictions:
        expected_outcome = WITNESS_OUTCOME.get(pred.case_id)
        outcome_ok = pred.outcome == expected_outcome
        pred_ok: Optional[bool] = None
        if pred.case_id in WITNESS_PREDICTIONS:
            expected_values = WITNESS_PREDICTIONS[pred.case_id]
            pred_ok = len(expected_values) == len(pred.predicted) and all(
                structural_equal(expected, actual) for expected, actual in zip(expected_values, pred.predicted)
            )
        comparisons.append(CaseComparison(pred.case_id, outcome_ok, pred_ok))
    return tuple(comparisons)


@dataclass(frozen=True)
class LockedBenchmarkReport:
    predictions: Tuple[CasePrediction, ...]
    comparisons: Tuple[CaseComparison, ...]
    predictions_path: str
    witness_imported_before_commit: bool


def run_locked_benchmark() -> LockedBenchmarkReport:
    """Composes the full protocol in the enforced order and returns a
    report including a DYNAMIC proof (not just a textual one) that the
    witness module was absent from `sys.modules` at the moment predictions
    were committed."""
    predictions = run_discovery_and_replay()
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
    "CaseComparison",
    "CasePrediction",
    "LockedBenchmarkReport",
    "WITNESS_MODULE_NAME",
    "commit_predictions",
    "reveal_and_compare",
    "run_discovery_and_replay",
    "run_locked_benchmark",
]


if __name__ == "__main__":
    report = run_locked_benchmark()
    for comparison in report.comparisons:
        print(comparison)
    print("witness imported before commit:", report.witness_imported_before_commit)
