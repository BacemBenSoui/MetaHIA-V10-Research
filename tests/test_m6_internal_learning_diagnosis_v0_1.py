"""Permanent invariant tests for M6 -- internal-learning diagnosis v0.1
("M6-INTERNAL", `m6_internal_learning_diagnosis_v0_1.py`).

Uses small, hand-constructed synthetic records throughout -- no
dependency on any real domain corpus. Real-corpus numbers are computed
separately by `scripts/run_m6_internal_learning_diagnosis_v0_1.py` and
reported in `documentation/MetaHIA_M6_Structural_Learning_V0_1.md`,
never pinned here as an expected value.
"""
from __future__ import annotations

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_DIRECT, SUPPORTED
from kernel2 import Node, OBSERVATION, node_ref
from m6_internal_learning_diagnosis_v0_1 import (
    BASIS_GLOBAL_ONLY_BASELINE,
    GlobalOnlyPolicy,
    result_to_dict,
    run_internal_learning_diagnosis,
    run_internal_learning_diagnosis_multi_seed,
    split_within_rule,
)
from m6_structural_learning_v0_1 import BASIS_EXACT_BUCKET, BASIS_RULE_ONLY, StructuralOutcomeRecord

import pytest


def _pattern(name: str) -> Node:
    # Generic OBSERVATION kind, not PATTERN/SHAPE_PATTERN -- see
    # tests/test_m6_context_transfer_diagnosis_v0_1.py's own helper
    # docstring for why PATTERN silently collapses every synthetic rule
    # onto the same structural_signature() (found the hard way there;
    # not repeated here).
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


def test_split_within_rule_rejects_bad_fractions_and_bad_min_records():
    with pytest.raises(ValueError):
        split_within_rule((), val_fraction=-0.1)
    with pytest.raises(ValueError):
        split_within_rule((), holdout_fraction=1.0)
    with pytest.raises(ValueError):
        split_within_rule((), min_records_per_rule=1)


def test_split_within_rule_keeps_a_small_rule_entirely_in_train():
    records = (_record("r1", "RULE_A", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),)
    train, val, holdout = split_within_rule(records, holdout_fraction=0.5, min_records_per_rule=2)
    assert train == records
    assert val == () and holdout == ()


def test_split_within_rule_guarantees_every_holdout_rule_also_has_a_train_record():
    """The structural inverse of split_by_rule()'s own guarantee,
    checked directly: a holdout record's rule signature must ALWAYS
    also appear in train, with at least one record."""
    records = tuple(
        _record(f"r{i}-{j}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
        for i in range(5)
        for j in range(5)
    )
    train, _val, holdout = split_within_rule(records, holdout_fraction=0.4, seed=0)
    train_rules = {r.rule_signature for r in train}
    holdout_rules = {r.rule_signature for r in holdout}
    assert holdout_rules  # this corpus must actually produce a non-empty holdout
    assert holdout_rules.issubset(train_rules)


def test_split_within_rule_never_empties_a_rules_training_presence():
    records = tuple(
        _record(f"r{i}-{j}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
        for i in range(3)
        for j in range(2)  # exactly 2 records per rule -- the tightest possible case
    )
    train, _val, holdout = split_within_rule(records, holdout_fraction=0.9, seed=0)  # aggressive holdout fraction
    train_rules_count = {}
    for r in train:
        train_rules_count[r.rule_signature] = train_rules_count.get(r.rule_signature, 0) + 1
    for r in holdout:
        assert train_rules_count.get(r.rule_signature, 0) >= 1


def test_global_only_policy_ignores_rule_and_context_entirely():
    train = (
        _record("t1", "RULE_A", novelty=0.9, redundancy=0.1, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),
        _record("t2", "RULE_A", novelty=0.1, redundancy=0.9, depth=5, provenance=GROUNDED_DIRECT, outcome=CONTRADICTED),
    )
    policy = GlobalOnlyPolicy().fit(train)
    pred_a = policy.predict(_pattern("RULE_A"), 0.9, 0.1, 1, GROUNDED_DIRECT)
    pred_b = policy.predict(_pattern("RULE_Z"), 0.0, 0.0, 99, GROUNDED_DIRECT)  # a totally different query
    assert pred_a.distribution == pred_b.distribution  # context/rule never consulted
    assert pred_a.basis == BASIS_GLOBAL_ONLY_BASELINE
    assert pred_a.distribution[SUPPORTED] == 0.5 and pred_a.distribution[CONTRADICTED] == 0.5


def test_run_internal_learning_diagnosis_returns_none_when_no_rule_is_eligible():
    records = tuple(
        _record(f"r{i}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
        for i in range(5)
    )  # every rule has exactly 1 record -- none eligible for internal holdout
    result = run_internal_learning_diagnosis(records, domain="tiny", min_records_per_rule=2)
    assert result is None


def test_run_internal_learning_diagnosis_reaches_exact_bucket_or_rule_only_on_every_holdout_record():
    """The property this whole module exists to demonstrate: unlike
    split_by_rule()'s holdout (always BASIS_GLOBAL_PRIOR), every
    split_within_rule() holdout record's rule WAS seen in training, so
    predict() must resolve to EXACT_BUCKET or RULE_ONLY, never
    GLOBAL_PRIOR/UNIFORM_NO_DATA."""
    records = tuple(
        _record(f"r{i}-{j}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
        for i in range(5)
        for j in range(5)
    )
    result = run_internal_learning_diagnosis(records, domain="synthetic", holdout_fraction=0.4, seed=0)
    assert result is not None
    assert result.exact_or_rule_only_rate == 1.0
    assert set(result.basis_counts) <= {BASIS_EXACT_BUCKET, BASIS_RULE_ONLY}


def test_run_internal_learning_diagnosis_detects_a_genuine_rule_specific_signal():
    """Constructed so each rule's outcome is deterministic and DIFFERENT
    across rules (RULE_0 always SUPPORTED, RULE_1 always CONTRADICTED,
    etc.) -- a flat global prior sees a 50/50-ish mix and cannot do
    better than that, but the real policy, now actually able to use
    RULE_ONLY on a rule it has partially seen, should be near-perfect."""
    records = []
    for i in range(4):
        outcome = SUPPORTED if i % 2 == 0 else CONTRADICTED
        for j in range(6):
            records.append(
                _record(f"r{i}-{j}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=outcome)
            )
    result = run_internal_learning_diagnosis(tuple(records), domain="synthetic_signal", holdout_fraction=0.34, seed=0)
    assert result is not None
    assert result.real_policy_brier < result.global_only_brier
    assert result.brier_delta < 0
    assert result.real_policy_brier < 0.1  # near-perfect: every holdout rule was seen elsewhere with the same outcome


def test_multi_seed_runs_keep_each_seed_distinct():
    records = tuple(
        _record(f"r{i}-{j}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
        for i in range(5)
        for j in range(5)
    )
    results = run_internal_learning_diagnosis_multi_seed(records, domain="synthetic", seeds=range(5), holdout_fraction=0.4)
    assert len(results) >= 1
    assert len({r.seed for r in results}) == len(results)


def test_result_to_dict_is_json_serializable():
    import json

    records = tuple(
        _record(f"r{i}-{j}", f"RULE_{i}", novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED)
        for i in range(5)
        for j in range(5)
    )
    result = run_internal_learning_diagnosis(records, domain="synthetic", holdout_fraction=0.4, seed=0)
    assert result is not None
    payload = result_to_dict(result)
    json.dumps(payload)  # must not raise
    assert payload["domain"] == "synthetic"
