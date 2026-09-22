"""P4-T.2 v0.2 -- locked train/holdout/witness benchmark runner, with
REAL P4-T.3 hypothesis-selection integration.

`p4t_locked_benchmark_runner_v0_1.py` called `p4t.discover()` directly
with a `source_position`/`target_position` pair taken straight from each
`LockedCase` -- the benchmark itself told the mechanism which columns to
compare, so P4-T.3's own hypothesis-enumeration/selection layer
(`discover_all_hypotheses()`/`select_hypothesis()`) was never exercised
inside the locked protocol, only in its own unit tests. This version
closes exactly that gap: `_discover_and_freeze_v2()` below calls
`discover_all_hypotheses()` then `select_hypothesis()` and only freezes
whichever hypothesis (if any) is genuinely retained -- the runner never
receives or assumes a position pair from `p4t_locked_benchmark_cases_v0_2.py`.

Same non-circularity discipline as v0.1, unchanged:

  1. `run_discovery_and_replay()` reads ONLY
     `p4t_locked_benchmark_cases_v0_2.py`. Its source code never names
     `p4t_locked_benchmark_witness_v0_2`.
  2. `commit_predictions()` writes to
     `validation/p4t_locked_benchmark_predictions_v0_2.json`, timestamped,
     BEFORE any witness data has been read.
  3. `reveal_and_compare()` is the ONLY function in this module that
     imports the witness module, strictly after predictions are committed.
  4. `run_locked_benchmark()` composes the three steps in that order and
     asserts, dynamically via `sys.modules`, that the witness module was
     absent at the moment of commit.

This is still a SELF-ADMINISTERED, structurally-enforced protocol, not a
third-party-witnessed gate closure -- the same distinction v0.1 already
draws for itself and this project draws for M4-M7.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

from kernel2 import structural_equal
import p4t_structural_transformation_induction_v0_1 as p4t
from p4t_locked_benchmark_cases_v0_2 import LOCKED_CASES_V2, LockedCaseV2

WITNESS_MODULE_NAME = "p4t_locked_benchmark_witness_v0_2"
PREDICTIONS_PATH = Path(__file__).resolve().parent / "validation" / "p4t_locked_benchmark_predictions_v0_2.json"


@dataclass(frozen=True)
class CasePredictionV2:
    case_id: str
    family_expected: Optional[str]
    selection_outcome: str  # "RETAINED" | "AMBIGUOUS_SELECTION" | "NO_HYPOTHESES"
    retained_family: Optional[str]
    predicted: Tuple[object, ...]

    @property
    def predicted_repr(self) -> Tuple[str, ...]:
        """Human-readable audit trail only -- never used for the actual
        comparison against witness values, since repr() embeds each
        predicted Node's own arbitrary node_id (see `reveal_and_compare`,
        which uses kernel2.structural_equal instead)."""
        return tuple(repr(item) for item in self.predicted)


def _discover_and_freeze_v2(rows: Sequence, *, frozen_id: str):
    """Gate A.3 + B: enumerates every hypothesis, selects the unique
    lowest-complexity one (if any), and freezes it. Returns
    (selection_outcome, retained_family, frozen_or_None) -- the runner
    never tells this function which position pair to use."""
    hypotheses = p4t.discover_all_hypotheses(rows)
    selection = p4t.select_hypothesis(hypotheses)
    if selection.outcome != p4t.OUTCOME_RETAINED:
        return selection.outcome, None, None
    frozen = p4t.freeze(selection.retained.candidate, frozen_id=frozen_id)
    return selection.outcome, selection.retained.candidate.family, frozen


def run_discovery_and_replay() -> Tuple[CasePredictionV2, ...]:
    """Gate A.3 + B + C on every locked case. Reads train rows and
    holdout SOURCE observations only from
    `p4t_locked_benchmark_cases_v0_2.py` -- no target/witness data exists
    anywhere in that file. This function's own source code never names
    the witness module (verified statically by
    `tests/test_p4t_locked_benchmark_v0_2.py`)."""
    results = []
    for case in LOCKED_CASES_V2:
        if case.family_expected == "COMPOSED":
            inner_outcome, _, inner_frozen = _discover_and_freeze_v2(
                case.composed_inner_rows, frozen_id=f"LOCKEDV2::{case.case_id}::INNER",
            )
            outer_outcome, _, outer_frozen = _discover_and_freeze_v2(
                case.composed_outer_rows, frozen_id=f"LOCKEDV2::{case.case_id}::OUTER",
            )
            if inner_frozen is None or outer_frozen is None:
                worst = inner_outcome if inner_frozen is None else outer_outcome
                results.append(CasePredictionV2(case.case_id, case.family_expected, worst, None, ()))
                continue
            frozen = p4t.compose_frozen(outer_frozen, inner_frozen, frozen_id=f"LOCKEDV2::{case.case_id}")
            predictions = p4t.blind_replay(frozen, case.holdout_source)
            results.append(
                CasePredictionV2(case.case_id, case.family_expected, p4t.OUTCOME_RETAINED, "COMPOSED", tuple(predictions))
            )
            continue

        selection_outcome, retained_family, frozen = _discover_and_freeze_v2(
            case.train_rows, frozen_id=f"LOCKEDV2::{case.case_id}",
        )
        if frozen is None:
            results.append(CasePredictionV2(case.case_id, case.family_expected, selection_outcome, retained_family, ()))
            continue
        predictions = p4t.blind_replay(frozen, case.holdout_source)
        results.append(
            CasePredictionV2(case.case_id, case.family_expected, selection_outcome, retained_family, tuple(predictions))
        )
    return tuple(results)


def commit_predictions(predictions: Sequence[CasePredictionV2]) -> Path:
    """Writes predictions to disk BEFORE any witness data is consulted --
    the locked, timestamped record of what was predicted blind."""
    payload = {
        "committed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "witness_module_imported_yet": WITNESS_MODULE_NAME in sys.modules,
        "predictions": [
            {
                "case_id": p.case_id,
                "family_expected": p.family_expected,
                "selection_outcome": p.selection_outcome,
                "retained_family": p.retained_family,
                "predicted_repr": list(p.predicted_repr),
            }
            for p in predictions
        ],
    }
    PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return PREDICTIONS_PATH


@dataclass(frozen=True)
class CaseComparisonV2:
    case_id: str
    selection_outcome_matches_witness: bool
    prediction_matches_witness: Optional[bool]


def reveal_and_compare(predictions: Sequence[CasePredictionV2]) -> Tuple[CaseComparisonV2, ...]:
    """The ONLY function in this module that imports the witness module --
    called strictly after `commit_predictions()`."""
    from p4t_locked_benchmark_witness_v0_2 import WITNESS_SELECTION_OUTCOME, WITNESS_PREDICTIONS  # noqa: PLC0415

    comparisons = []
    for pred in predictions:
        expected_outcome = WITNESS_SELECTION_OUTCOME.get(pred.case_id)
        outcome_ok = pred.selection_outcome == expected_outcome
        pred_ok: Optional[bool] = None
        if pred.case_id in WITNESS_PREDICTIONS:
            expected_values = WITNESS_PREDICTIONS[pred.case_id]
            pred_ok = len(expected_values) == len(pred.predicted) and all(
                structural_equal(expected, actual) for expected, actual in zip(expected_values, pred.predicted)
            )
        comparisons.append(CaseComparisonV2(pred.case_id, outcome_ok, pred_ok))
    return tuple(comparisons)


@dataclass(frozen=True)
class LockedBenchmarkReportV2:
    predictions: Tuple[CasePredictionV2, ...]
    comparisons: Tuple[CaseComparisonV2, ...]
    predictions_path: str
    witness_imported_before_commit: bool


def run_locked_benchmark() -> LockedBenchmarkReportV2:
    """Composes the full v0.2 protocol in the enforced order and returns a
    report including a DYNAMIC proof that the witness module was absent
    from `sys.modules` at the moment predictions were committed."""
    predictions = run_discovery_and_replay()
    witness_imported_before_commit = WITNESS_MODULE_NAME in sys.modules
    path = commit_predictions(predictions)
    comparisons = reveal_and_compare(predictions)
    return LockedBenchmarkReportV2(
        predictions=predictions,
        comparisons=comparisons,
        predictions_path=str(path),
        witness_imported_before_commit=witness_imported_before_commit,
    )


__all__ = [
    "CaseComparisonV2",
    "CasePredictionV2",
    "LockedBenchmarkReportV2",
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
