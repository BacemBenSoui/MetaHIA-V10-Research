"""P4-U.1 -- locked train/holdout/witness benchmark.

Verifies, by direct execution, that
`p4u1_locked_benchmark_runner_v0_1.py` mechanically enforces
TRAIN != HOLDOUT != WITNESS rather than merely promising it in prose --
the same static + dynamic import-order checks
`tests/test_p4t_locked_benchmark_v0_1.py` already applies to P4-T's own
locked benchmark.

This is a SELF-ADMINISTERED protocol, not a third-party-witnessed gate
closure -- stated explicitly here and in
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`,
matching this project's own established rule that self-execution never
closes a validation gate by itself.

**Runtime note**: the real end-to-end run
(`test_run_locked_benchmark_matches_witness_on_every_case`) computes a
200-replicate null-max distribution for TRAIN and HOLDOUT on all three
cases -- a genuinely expensive, real computation (order of a few
minutes), not a toy. A module-scoped fixture runs it exactly ONCE and
every assertion below reads from that single result, rather than
re-running the full benchmark per test.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
from pathlib import Path

import pytest

import p4u1_locked_benchmark_runner_v0_1 as runner
from p4u1_locked_benchmark_cases_v0_1 import LOCKED_CASES

RUNNER_SOURCE_PATH = Path(runner.__file__)


def test_locked_cases_cover_u1_u2_u3():
    case_ids = {c.case_id for c in LOCKED_CASES}
    assert case_ids == {"U1", "U2", "U3"}


def test_u1_declares_the_real_motif_and_all_three_decoys():
    u1 = next(c for c in LOCKED_CASES if c.case_id == "U1")
    labels = {cand.label for cand in u1.candidates}
    assert labels == {"REAL_MOTIF", "DECOY_SUB_SEUIL", "DECOY_DEPTH1", "DECOY_TRAIN_ONLY"}


def test_cases_module_contains_no_witness_only_identifiers():
    """The cases file must be a genuine blind-holdout source -- no
    outcome/witness identifier should exist in it at all."""
    cases_source = Path(
        Path(runner.__file__).resolve().parent / "p4u1_locked_benchmark_cases_v0_1.py"
    ).read_text(encoding="utf-8")
    witness_only_tokens = ("WITNESS_EXPECTED", "REPLICATED", "NOT_APPLICABLE")
    for token in witness_only_tokens:
        assert token not in cases_source


def _function_source_mentions(func, needle: str) -> bool:
    return needle in inspect.getsource(func)


def test_discovery_and_commit_functions_never_mention_the_witness_module_by_name():
    """Static check, mirroring `test_p4t_locked_benchmark_v0_1.py`'s own
    pattern: the witness module name must not appear anywhere in the
    source of the functions that run discovery/gates or commit
    predictions -- only inside `reveal_and_compare`, which runs
    strictly after commit."""
    assert not _function_source_mentions(runner.run_discovery_and_gates, runner.WITNESS_MODULE_NAME)
    assert not _function_source_mentions(runner.commit_predictions, runner.WITNESS_MODULE_NAME)
    assert _function_source_mentions(runner.reveal_and_compare, runner.WITNESS_MODULE_NAME)


def test_witness_module_is_not_imported_at_module_scope():
    """Parses the runner file's AST and confirms there is no top-level
    (module-scope) import of the witness module -- only a nested import
    inside a function body can satisfy `reveal_and_compare`'s need for it."""
    tree = ast.parse(RUNNER_SOURCE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == runner.WITNESS_MODULE_NAME:
            raise AssertionError("witness module must not be imported at module scope")
        if isinstance(node, ast.Import):
            assert not any(alias.name == runner.WITNESS_MODULE_NAME for alias in node.names)


@pytest.fixture(scope="module")
def locked_benchmark_report():
    """Runs the full, real, expensive locked benchmark exactly ONCE for
    this whole test module (see module docstring)."""
    sys.modules.pop(runner.WITNESS_MODULE_NAME, None)
    return runner.run_locked_benchmark()


def test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed(locked_benchmark_report):
    """Dynamic proof, not just textual: the witness module had genuinely
    not been imported at the moment predictions were committed --
    Python's own import bookkeeping, not this test's say-so."""
    assert locked_benchmark_report.witness_imported_before_commit is False
    assert runner.WITNESS_MODULE_NAME in sys.modules  # imported by reveal_and_compare, strictly after


def test_committed_predictions_file_exists_and_matches_declared_candidate_count(locked_benchmark_report):
    path = Path(locked_benchmark_report.predictions_path)
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    total_declared = sum(len(c.candidates) for c in LOCKED_CASES)
    assert len(payload["predictions"]) == total_declared


def test_run_locked_benchmark_matches_witness_on_every_declared_candidate(locked_benchmark_report):
    """The end-to-end result: every declared candidate's Gate A/B/C
    outcome matches the locked witness -- the concrete demonstration
    that Gate B (unchanged) correctly separates REAL_MOTIF and
    DECOY_TRAIN_ONLY (both concentrated enough to pass) from
    DECOY_SUB_SEUIL (too small) and DECOY_DEPTH1 (wrong depth), and
    that the NEW set-valued Gate C (Sec. 10) is what then separates
    REAL_MOTIF (replicates in holdout) from DECOY_TRAIN_ONLY (does
    not) -- exactly the U1/U2/U3 separation the protocol was designed
    to test."""
    by_key = {(c.case_id, c.label): c for c in locked_benchmark_report.comparisons}
    assert len(by_key) == sum(len(c.candidates) for c in LOCKED_CASES)
    for comparison in locked_benchmark_report.comparisons:
        assert comparison.all_match, comparison


def test_real_motif_clears_gate_b_and_gate_c_with_real_margin(locked_benchmark_report):
    """Not just PASS/FAIL -- the actual numbers must show real
    separation, not a coincidence sitting exactly at the threshold."""
    from p4u1_locked_benchmark_cases_v0_1 import GATE_PARAMS

    pred = next(p for p in locked_benchmark_report.predictions if p.case_id == "U1" and p.label == "REAL_MOTIF")
    assert pred.support_train >= GATE_PARAMS["s_min"]
    assert pred.support_holdout >= GATE_PARAMS["k_min"]
    assert pred.coverage >= GATE_PARAMS["coverage_min"]


def test_decoy_train_only_clears_gate_b_but_fails_gate_c_at_zero_support(locked_benchmark_report):
    """The concrete demonstration that Gate B alone cannot detect a
    train-only regularity -- it takes real support in TRAIN, same as
    REAL_MOTIF -- but Gate C's holdout replication finds nothing at
    all (support_holdout == 0), never a marginal near-miss."""
    pred = next(p for p in locked_benchmark_report.predictions if p.case_id == "U1" and p.label == "DECOY_TRAIN_ONLY")
    assert pred.gate_b == "RETAINED"
    assert pred.support_holdout == 0
    assert pred.gate_c == "FAILED"


def test_committed_predictions_file_is_deterministic_across_runs(locked_benchmark_report):
    """Reuses the module fixture's already-committed run as the first
    sample (avoiding a third expensive full run) and runs the benchmark
    ONE more time, confirming the committed predictions are
    byte-identical modulo the timestamp -- the determinism guarantee a
    locked benchmark exists to provide."""
    payload1 = json.loads(Path(locked_benchmark_report.predictions_path).read_text(encoding="utf-8"))
    sys.modules.pop(runner.WITNESS_MODULE_NAME, None)
    report2 = runner.run_locked_benchmark()
    payload2 = json.loads(Path(report2.predictions_path).read_text(encoding="utf-8"))
    payload1.pop("committed_at_utc")
    payload2.pop("committed_at_utc")
    assert payload1 == payload2
