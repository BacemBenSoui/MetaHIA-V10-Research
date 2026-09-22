"""Permanent invariant tests for M6 -- context-transfer diagnosis v0.1
(`m6_context_transfer_diagnosis_v0_1.py`).

Uses small, hand-constructed synthetic records throughout for the
mechanism tests -- no dependency on any real domain corpus -- so these
never depend on network access or a specific corpus's exact numbers.
Real-corpus numbers are computed separately by
`scripts/run_m6_context_transfer_diagnosis_v0_1.py` and reported in
`documentation/M6_CONTEXT_TRANSFER_DIAGNOSIS_V0_1.md`, never pinned
here as an expected value (the whole point of this diagnostic is to
report whatever the real corpora actually show, not a value decided in
advance).
"""
from __future__ import annotations

from kernel2 import Node, OBSERVATION, node_ref
from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, GROUNDED_DIRECT, SUPPORTED, UNKNOWN
from m6_context_transfer_diagnosis_v0_1 import (
    ContextOnlyPolicy,
    context_key,
    result_to_dict,
    run_context_transfer_diagnosis,
    run_context_transfer_diagnosis_multi_seed,
)
from m6_structural_learning_v0_1 import StructuralOutcomeRecord


def _pattern(name: str) -> Node:
    """A plain OBSERVATION-kind node, deliberately NOT `PATTERN`/
    `SHAPE_PATTERN` -- `structural_signature()` dispatches those two
    kinds to `_pattern_unified_signature()`, which expects a real
    PatternSlot-based structure and returns `None` for a hand-built
    stand-in like this one (found by direct execution: an earlier
    version of this helper used `PATTERN` and every synthetic rule
    silently collapsed to the same `None` signature, before any test
    using it was trusted). A generic kind falls through to
    `structural_signature`'s generic `(kind, children)` branch, which
    gives each distinct `node_ref(name)` its own distinct signature --
    exactly what these tests need."""
    return Node(f"rule::{name}", OBSERVATION, (node_ref(name),))


def _record(record_id, rule_name, *, novelty, redundancy, depth, provenance, outcome) -> StructuralOutcomeRecord:
    return StructuralOutcomeRecord(
        record_id=record_id,
        rule=_pattern(rule_name),
        novelty=novelty,
        redundancy=redundancy,
        depth=depth,
        provenance=provenance,
        outcome=outcome,
    )


def test_context_key_matches_bucket_key_with_rule_signature_dropped():
    """The equivalence the whole module depends on, checked directly:
    context_key() must be exactly bucket_key()[1:], never an
    independently-reimplemented banding that could silently drift."""
    r = _record("r1", "RULE_A", novelty=0.9, redundancy=0.1, depth=2, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
    assert context_key(r) == r.bucket_key()[1:]
    assert context_key(r) == ("HIGH", "LOW", 2, GROUNDED_DIRECT)


def test_context_only_policy_ignores_rule_identity_by_construction():
    """Two different rules sharing the same context must be pooled into
    the same bucket -- the entire mechanism this diagnostic tests."""
    train = (
        _record("t1", "RULE_A", novelty=0.9, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),
        _record("t2", "RULE_B", novelty=0.9, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),
    )
    policy = ContextOnlyPolicy().fit(train)
    # RULE_C was never seen in training at all -- if context pooling works,
    # its prediction still uses the 2-record bucket shared by RULE_A/RULE_B.
    unseen_rule = _pattern("RULE_C")
    pred = policy.predict(unseen_rule, 0.9, 0.1, 1, GROUNDED_DIRECT)
    assert pred.support == 2
    assert pred.distribution[SUPPORTED] == 1.0


def test_context_only_policy_falls_back_to_global_prior_for_an_unseen_context():
    train = (
        _record("t1", "RULE_A", novelty=0.9, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),
        _record("t2", "RULE_B", novelty=0.1, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=CONTRADICTED),
    )
    policy = ContextOnlyPolicy().fit(train)
    pred = policy.predict(_pattern("RULE_C"), 0.5, 0.5, 9, GROUNDED_ANALOGY)  # a context combo never seen
    assert pred.basis == "CONTEXT_GLOBAL_FALLBACK"
    assert pred.support == 2
    assert pred.distribution[SUPPORTED] == 0.5 and pred.distribution[CONTRADICTED] == 0.5


def test_run_context_transfer_diagnosis_detects_a_genuine_context_signal():
    """Constructed so context (not rule identity) is perfectly
    predictive: every LOW-novelty record is SUPPORTED, every HIGH-novelty
    record is CONTRADICTED, regardless of which of 6 distinct rules it
    belongs to. If the mechanism works, context_bucket_brier must be
    near 0 while global_prior_brier (a single 50/50 mix) stays high --
    proving the comparison can detect a real signal when one exists,
    before trusting a real-corpus negative result."""
    records = []
    for i in range(6):
        rule_name = f"RULE_{i}"
        outcome = SUPPORTED if i % 2 == 0 else CONTRADICTED
        novelty = 0.1 if outcome == SUPPORTED else 0.9
        for j in range(4):  # enough records per rule for split_by_rule's val/holdout fractions
            records.append(
                _record(f"r{i}-{j}", rule_name, novelty=novelty, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=outcome)
            )

    result = run_context_transfer_diagnosis(tuple(records), domain="synthetic_signal", seed=0, val_fraction=0.0, holdout_fraction=0.34)
    assert result is not None
    assert result.context_bucket_brier < result.global_prior_brier
    assert result.brier_delta < 0


def test_run_context_transfer_diagnosis_returns_none_on_an_empty_split():
    """Fail-closed discipline: a corpus too small to produce a non-empty
    holdout must not fabricate a comparison."""
    records = (_record("r1", "RULE_A", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=UNKNOWN),)
    result = run_context_transfer_diagnosis(records, domain="tiny", seed=0, val_fraction=0.0, holdout_fraction=0.5)
    assert result is None


def test_multi_seed_runs_never_silently_average_away_a_disagreement():
    records = []
    for i in range(6):
        rule_name = f"RULE_{i}"
        outcome = SUPPORTED if i % 2 == 0 else CONTRADICTED
        novelty = 0.1 if outcome == SUPPORTED else 0.9
        for j in range(4):
            records.append(
                _record(f"r{i}-{j}", rule_name, novelty=novelty, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=outcome)
            )
    results = run_context_transfer_diagnosis_multi_seed(tuple(records), domain="synthetic_signal", seeds=range(5), val_fraction=0.0, holdout_fraction=0.34)
    assert len(results) >= 1
    assert all(r.domain == "synthetic_signal" for r in results)
    assert len({r.seed for r in results}) == len(results)  # every returned result keeps its own seed, not merged


def test_result_to_dict_is_json_serializable():
    import json

    records = []
    for i in range(6):
        rule_name = f"RULE_{i}"
        outcome = SUPPORTED if i % 2 == 0 else CONTRADICTED
        for j in range(4):
            records.append(
                _record(f"r{i}-{j}", rule_name, novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=outcome)
            )
    result = run_context_transfer_diagnosis(tuple(records), domain="synthetic", seed=0, val_fraction=0.0, holdout_fraction=0.34)
    assert result is not None
    payload = result_to_dict(result)
    json.dumps(payload)  # must not raise
    assert payload["domain"] == "synthetic"
