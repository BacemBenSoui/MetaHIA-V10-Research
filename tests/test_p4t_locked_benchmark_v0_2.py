"""P4-T.2 v0.2 -- locked train/holdout/witness benchmark, with REAL P4-T.3
hypothesis-selection integration.

Mirrors `tests/test_p4t_locked_benchmark_v0_1.py`'s non-circularity
discipline (static text check, static AST check, dynamic `sys.modules`
check) for `p4t_locked_benchmark_runner_v0_2.py`, and adds coverage
specific to what v0.2 changes: the runner discovers its own position
pairs via `discover_all_hypotheses()`/`select_hypothesis()` instead of
being told them by the cases file, and two cases exist specifically to
exercise that layer's two non-trivial outcomes -- a unique winner among
several valid hypotheses, and a genuine tie (`AMBIGUOUS_SELECTION`).

This is still a SELF-ADMINISTERED protocol, not a third-party-witnessed
gate closure -- stated explicitly here and in
`documentation/P4T2_Locked_Benchmark_V0_1.md` Sec. 6bis, matching this
project's own established rule that self-execution never closes a
validation gate by itself.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
from pathlib import Path

from kernel2 import Node, NodeRef

import p4t_locked_benchmark_runner_v0_2 as runner
import p4t_structural_transformation_induction_v0_1 as p4t
from p4t_locked_benchmark_cases_v0_2 import LOCKED_CASES_V2

RUNNER_SOURCE_PATH = Path(runner.__file__)


def _collect_ref_ids(obj, into: set) -> None:
    if isinstance(obj, NodeRef):
        into.add(obj.ref_id)
    elif isinstance(obj, Node):
        for child in obj.children:
            _collect_ref_ids(child, into)
    elif isinstance(obj, (tuple, list)):
        for item in obj:
            _collect_ref_ids(item, into)


def test_locked_cases_v2_carry_no_position_fields():
    """The essential API change vs v0.1: this dataclass must not be able
    to name a source/target position at all, since finding one is now the
    mechanism's own job."""
    field_names = {f for case in LOCKED_CASES_V2 for f in vars(case)}
    assert "source_position" not in field_names
    assert "target_position" not in field_names


def test_locked_cases_v2_cover_both_selection_outcomes_plus_every_family():
    outcomes = {c.expected_selection_outcome for c in LOCKED_CASES_V2}
    assert outcomes == {"RETAINED", "AMBIGUOUS_SELECTION", "NO_HYPOTHESES"}
    families = {c.family_expected for c in LOCKED_CASES_V2 if c.family_expected is not None}
    assert families == {"SELECTION_MAPPING", "COMPOSED"}
    assert len(LOCKED_CASES_V2) == 6


def test_v2c03_genuinely_has_more_than_one_hypothesis_before_selection_narrows_it():
    """The case built to satisfy "2+ valid hypotheses, unique winner":
    confirms, by direct execution (not by trusting the case's own
    comment), that discover_all_hypotheses() really does find more than
    one hypothesis here, and that select_hypothesis() still narrows to a
    unique retained one."""
    case = next(c for c in LOCKED_CASES_V2 if c.case_id == "V2C03_TWO_HYPOTHESES_UNIQUE_WINNER")
    hypotheses = p4t.discover_all_hypotheses(case.train_rows)
    assert len(hypotheses) >= 2
    result = p4t.select_hypothesis(hypotheses)
    assert result.outcome == p4t.OUTCOME_RETAINED
    assert result.retained.candidate.family == "SELECTION_MAPPING"


def test_v2c04_genuinely_has_a_tie_at_the_best_rank():
    """The case built to satisfy "2+ same-complexity hypotheses,
    AMBIGUOUS_SELECTION": confirms, by direct execution, that at least two
    hypotheses share the lowest complexity rank present."""
    case = next(c for c in LOCKED_CASES_V2 if c.case_id == "V2C04_AMBIGUOUS_SELECTION")
    hypotheses = p4t.discover_all_hypotheses(case.train_rows)
    best_rank = min(h.complexity_rank for h in hypotheses)
    tied_at_best = [h for h in hypotheses if h.complexity_rank == best_rank]
    assert len(tied_at_best) >= 2
    result = p4t.select_hypothesis(hypotheses)
    assert result.outcome == p4t.OUTCOME_AMBIGUOUS_SELECTION
    assert result.retained is None


def test_no_holdout_entity_is_reused_from_training_within_any_case():
    """Permanent regression guard against re-introducing the exact defect
    P4-T.1 bis had to fix in v0.1's C02 (a holdout entity silently reusing
    a training NodeRef id). Checked generically here for every v0.2 case,
    including COMPOSED's two independently-trained row sets, by comparing
    the plain string repr of each side -- not by re-deriving each case's
    entity names by hand."""
    for case in LOCKED_CASES_V2:
        train_ref_ids: set = set()
        _collect_ref_ids(case.train_rows, train_ref_ids)
        _collect_ref_ids(case.composed_inner_rows, train_ref_ids)
        _collect_ref_ids(case.composed_outer_rows, train_ref_ids)
        holdout_ref_ids: set = set()
        _collect_ref_ids(case.holdout_source, holdout_ref_ids)
        overlap = train_ref_ids & holdout_ref_ids
        assert not overlap, (case.case_id, overlap)


def test_cases_module_contains_no_witness_only_identifiers():
    cases_source = Path(
        Path(runner.__file__).resolve().parent / "p4t_locked_benchmark_cases_v0_2.py"
    ).read_text(encoding="utf-8")
    witness_only_tokens = ("w_v2c01_1", "w_v2c02_1", "w_v2c03_1", "w_v2c05_1")
    for token in witness_only_tokens:
        assert token not in cases_source


def _function_source_mentions(func, needle: str) -> bool:
    return needle in inspect.getsource(func)


def test_discovery_and_commit_functions_never_mention_the_witness_module_by_name():
    assert not _function_source_mentions(runner.run_discovery_and_replay, runner.WITNESS_MODULE_NAME)
    assert not _function_source_mentions(runner._discover_and_freeze_v2, runner.WITNESS_MODULE_NAME)
    assert not _function_source_mentions(runner.commit_predictions, runner.WITNESS_MODULE_NAME)
    assert _function_source_mentions(runner.reveal_and_compare, runner.WITNESS_MODULE_NAME)


def test_witness_module_is_not_imported_at_module_scope():
    tree = ast.parse(RUNNER_SOURCE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == runner.WITNESS_MODULE_NAME:
            raise AssertionError("witness module must not be imported at module scope")
        if isinstance(node, ast.Import):
            assert not any(alias.name == runner.WITNESS_MODULE_NAME for alias in node.names)


def test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed():
    sys.modules.pop(runner.WITNESS_MODULE_NAME, None)
    predictions = runner.run_discovery_and_replay()
    assert runner.WITNESS_MODULE_NAME not in sys.modules
    runner.commit_predictions(predictions)
    assert runner.WITNESS_MODULE_NAME not in sys.modules
    comparisons = runner.reveal_and_compare(predictions)
    assert runner.WITNESS_MODULE_NAME in sys.modules
    assert len(comparisons) == len(predictions)


def test_run_locked_benchmark_reports_witness_not_imported_before_commit():
    sys.modules.pop(runner.WITNESS_MODULE_NAME, None)
    report = runner.run_locked_benchmark()
    assert report.witness_imported_before_commit is False


def test_run_locked_benchmark_matches_witness_on_every_case():
    report = runner.run_locked_benchmark()
    by_id = {c.case_id: c for c in report.comparisons}
    assert len(by_id) == 6
    for comparison in report.comparisons:
        assert comparison.selection_outcome_matches_witness, comparison
    for case_id in ("V2C01_PROJECTION", "V2C02_DUPLICATION", "V2C03_TWO_HYPOTHESES_UNIQUE_WINNER", "V2C05_COMPOSED"):
        assert by_id[case_id].prediction_matches_witness is True, case_id
    for case_id in ("V2C04_AMBIGUOUS_SELECTION", "V2C06_NO_HYPOTHESES"):
        assert by_id[case_id].prediction_matches_witness is None


def test_committed_predictions_file_is_written_and_deterministic_across_runs():
    report1 = runner.run_locked_benchmark()
    payload1 = json.loads(Path(report1.predictions_path).read_text(encoding="utf-8"))
    report2 = runner.run_locked_benchmark()
    payload2 = json.loads(Path(report2.predictions_path).read_text(encoding="utf-8"))
    payload1.pop("committed_at_utc")
    payload2.pop("committed_at_utc")
    assert payload1 == payload2
