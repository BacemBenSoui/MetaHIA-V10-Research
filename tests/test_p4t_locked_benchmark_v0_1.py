"""P4-T.2 -- locked train/holdout/witness benchmark.

Verifies, by direct execution, that `p4t_locked_benchmark_runner_v0_1.py`
mechanically enforces TRAIN != HOLDOUT != WITNESS rather than merely
promising it in prose: a static check that the witness module is never
imported at module scope or inside the discovery/replay/commit functions,
and a dynamic check that it is genuinely absent from `sys.modules` at the
moment predictions are committed to disk.

This is a SELF-ADMINISTERED protocol, not a third-party-witnessed gate
closure -- stated explicitly here and in
`documentation/P4T2_Locked_Benchmark_V0_1.md`, matching this project's own
established rule that self-execution never closes a validation gate by
itself.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
from pathlib import Path

import p4t_locked_benchmark_runner_v0_1 as runner
from p4t_locked_benchmark_cases_v0_1 import LOCKED_CASES

RUNNER_SOURCE_PATH = Path(runner.__file__)


def test_locked_cases_cover_every_p4t_family_plus_both_fail_closed_outcomes():
    families = {c.family_expected for c in LOCKED_CASES}
    assert families == {
        "COMPARE_PERMUTATION", "COMPARE_RECURSIVE", "SELECTION_MAPPING",
        "COMPOSED", "AMBIGUOUS", "REJECTED",
    }
    assert len(LOCKED_CASES) == 7


def test_cases_module_contains_no_witness_only_identifiers():
    """The cases file must be a genuine blind-holdout source: no target
    information for any holdout case should exist in it at all (not even
    masked) -- checked by confirming the witness-only entity names never
    appear in the cases file's own source text."""
    cases_source = Path(
        Path(runner.__file__).resolve().parent / "p4t_locked_benchmark_cases_v0_1.py"
    ).read_text(encoding="utf-8")
    witness_only_tokens = ("c02_h1q", "c02_h2q", "c02_h3q", "w_c03_1", "w_c04_1", "w_c05_1")
    for token in witness_only_tokens:
        assert token not in cases_source


def _function_source_mentions(func, needle: str) -> bool:
    return needle in inspect.getsource(func)


def test_discovery_and_commit_functions_never_mention_the_witness_module_by_name():
    """Static check, mirroring this project's own _m7_dependency_scan
    pattern: the witness module name must not appear anywhere in the
    source of the functions that run discovery/replay or commit
    predictions -- only inside `reveal_and_compare`, which runs strictly
    after commit."""
    assert not _function_source_mentions(runner.run_discovery_and_replay, runner.WITNESS_MODULE_NAME)
    assert not _function_source_mentions(runner._discover_and_freeze, runner.WITNESS_MODULE_NAME)
    assert not _function_source_mentions(runner.commit_predictions, runner.WITNESS_MODULE_NAME)
    assert _function_source_mentions(runner.reveal_and_compare, runner.WITNESS_MODULE_NAME)


def test_witness_module_is_not_imported_at_module_scope():
    """Parses the runner file's AST and confirms there is no top-level
    (module-scope) import of the witness module -- only a nested import
    inside a function body can satisfy `reveal_and_compare`'s need for it."""
    tree = ast.parse(RUNNER_SOURCE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:  # top-level statements only, not nested in functions
        if isinstance(node, ast.ImportFrom) and node.module == runner.WITNESS_MODULE_NAME:
            raise AssertionError("witness module must not be imported at module scope")
        if isinstance(node, ast.Import):
            assert not any(alias.name == runner.WITNESS_MODULE_NAME for alias in node.names)


def test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed():
    """Dynamic proof, not just textual: actually run discovery/replay and
    commit, and confirm -- via Python's own import bookkeeping, not this
    module's say-so -- that the witness module had genuinely not been
    imported by that point in THIS test process."""
    sys.modules.pop(runner.WITNESS_MODULE_NAME, None)
    predictions = runner.run_discovery_and_replay()
    assert runner.WITNESS_MODULE_NAME not in sys.modules
    runner.commit_predictions(predictions)
    assert runner.WITNESS_MODULE_NAME not in sys.modules
    # Only now may the witness be imported, by the dedicated comparison step.
    comparisons = runner.reveal_and_compare(predictions)
    assert runner.WITNESS_MODULE_NAME in sys.modules
    assert len(comparisons) == len(predictions)


def test_run_locked_benchmark_reports_witness_not_imported_before_commit():
    """Python caches imports process-wide: once any earlier test in this
    session has legitimately called `reveal_and_compare` (which imports
    the witness module), it stays in `sys.modules` for the rest of the
    process -- that is a property of the interpreter's import cache, not
    evidence that THIS call's discovery/replay/commit read it early. Reset
    the cache first so this assertion demonstrates the runner's own
    ordering, not a stale earlier test's side effect (found and fixed
    2026-09-21: this test failed the first time it was written, for
    exactly this reason -- confirmed by direct execution, not assumed)."""
    sys.modules.pop(runner.WITNESS_MODULE_NAME, None)
    report = runner.run_locked_benchmark()
    assert report.witness_imported_before_commit is False


def test_run_locked_benchmark_matches_witness_on_every_case():
    """The end-to-end result: every case's outcome matches the locked
    witness, and every case with an expected prediction matches it
    structurally (never by a fragile repr() string comparison -- see
    `reveal_and_compare`'s use of kernel2.structural_equal)."""
    report = runner.run_locked_benchmark()
    by_id = {c.case_id: c for c in report.comparisons}
    assert len(by_id) == 7
    for comparison in report.comparisons:
        assert comparison.outcome_matches_witness, comparison
    for case_id in ("C01_PERMUTATION", "C02_RECURSIVE_PERMUTATION", "C03_PROJECTION", "C04_DUPLICATION", "C05_COMPOSITION"):
        assert by_id[case_id].prediction_matches_witness is True, case_id
    for case_id in ("C06_AMBIGUOUS", "C07_REJECTED"):
        assert by_id[case_id].prediction_matches_witness is None


def test_committed_predictions_file_is_written_and_deterministic_across_runs():
    report1 = runner.run_locked_benchmark()
    payload1 = json.loads(Path(report1.predictions_path).read_text(encoding="utf-8"))
    report2 = runner.run_locked_benchmark()
    payload2 = json.loads(Path(report2.predictions_path).read_text(encoding="utf-8"))
    payload1.pop("committed_at_utc")
    payload2.pop("committed_at_utc")
    assert payload1 == payload2
