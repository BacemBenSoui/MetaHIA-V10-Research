"""Permanent invariant tests for M6 -- Structural Learning v0.1.

Each test guards one of the design decisions fixed before implementation
(see m6_structural_learning_v0_1.py's module docstring): no DERIVED gold, rule
identity is structural, holdout is split by rule (never by record), the
policy never fabricates confidence it doesn't have, Brier stays a proper
bounded score, and promotion fails closed.
"""
from __future__ import annotations

import pytest

from kernel2 import Node, OBSERVATION, compare, node_ref
from m4_cold_start_evidence_v0_1 import CONTRADICTED, DERIVED, GROUNDED_ANALOGY, GROUNDED_DIRECT, SUPPORTED, UNGROUNDED_HUMAN, UNKNOWN
from m6_structural_learning_v0_1 import (
    OUTCOME_CLASSES,
    BASIS_EXACT_BUCKET,
    BASIS_GLOBAL_PRIOR,
    BASIS_RULE_ONLY,
    BASIS_UNIFORM_NO_DATA,
    StructuralLearningPolicy,
    StructuralOutcomeRecord,
    brier_score_multiclass,
    calibration_report,
    evaluate_promotion,
    split_by_rule,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def _swap12(a_id, b_id, op, a1, a2, out):
    a = _obs(a_id, op, a1, a2, out)
    b = _obs(b_id, op, a2, a1, out)
    return a, b


def _rule(seed: str) -> Node:
    """A fresh PATTERN discovered from a swap(1,2) pair -- a stand-in for a
    genuine kernel-discovered rule, never hand-authored."""
    a, b = _swap12(f"{seed}a", f"{seed}b", f"OP_{seed}", "A", "B", "C")
    pattern = compare(a, b)
    assert pattern is not None
    return pattern


def _record(seed, rule=None, *, novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome=SUPPORTED):
    return StructuralOutcomeRecord(
        record_id=seed,
        rule=rule if rule is not None else _rule(seed),
        novelty=novelty,
        redundancy=redundancy,
        depth=depth,
        provenance=provenance,
        outcome=outcome,
    )


# ---------------------------------------------------------------------------
# 1. No DERIVED gold, closed vocabularies only.
# ---------------------------------------------------------------------------

def test_derived_is_never_accepted_as_a_learning_outcome():
    with pytest.raises(ValueError):
        _record("r1", outcome=DERIVED)


def test_outcome_must_be_a_settled_m4_class():
    with pytest.raises(ValueError):
        _record("r2", outcome="MAYBE")


def test_provenance_must_be_one_of_m4s_closed_vocabulary():
    with pytest.raises(ValueError):
        _record("r3", provenance="HEARSAY")


def test_outcome_classes_are_exactly_the_three_settled_states():
    assert set(OUTCOME_CLASSES) == {SUPPORTED, CONTRADICTED, UNKNOWN}
    assert DERIVED not in OUTCOME_CLASSES


# ---------------------------------------------------------------------------
# 2. Rule identity is structural, not referential.
# ---------------------------------------------------------------------------

def test_two_different_node_instances_of_the_same_pattern_share_one_rule_bucket():
    a1, b1 = _swap12("x1a", "x1b", "OP_SAME", "A", "B", "C")
    a2, b2 = _swap12("x2a", "x2b", "OP_SAME", "A", "B", "C")
    pattern1 = compare(a1, b1)
    pattern2 = compare(a2, b2)
    assert pattern1 is not pattern2  # genuinely different objects
    r1 = _record("same1", rule=pattern1)
    r2 = _record("same2", rule=pattern2)
    assert r1.rule_signature == r2.rule_signature
    assert r1.bucket_key()[0] == r2.bucket_key()[0]


def test_two_genuinely_different_patterns_have_different_rule_signatures():
    a1, b1 = _swap12("y1a", "y1b", "OP_ONE", "A", "B", "C")
    a2, b2 = _swap12("y2a", "y2b", "OP_TWO", "A", "B", "C")
    r1 = _record("diff1", rule=compare(a1, b1))
    r2 = _record("diff2", rule=compare(a2, b2))
    assert r1.rule_signature != r2.rule_signature


# ---------------------------------------------------------------------------
# 3. split_by_rule never scatters one rule across two splits.
# ---------------------------------------------------------------------------

def test_split_by_rule_never_puts_one_rule_in_two_partitions():
    records = []
    for i in range(20):
        rule = _rule(f"sp{i}")
        for j in range(5):  # 5 records per rule -- deliberately repeated
            records.append(_record(f"sp{i}_{j}", rule=rule))
    train, val, holdout = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=7)

    def rule_ids(group):
        return {r.rule_signature for r in group}

    assert rule_ids(train).isdisjoint(rule_ids(val))
    assert rule_ids(train).isdisjoint(rule_ids(holdout))
    assert rule_ids(val).isdisjoint(rule_ids(holdout))
    assert len(train) + len(val) + len(holdout) == len(records)


def test_split_by_rule_is_deterministic_for_a_fixed_seed():
    records = [_record(f"det{i}", rule=_rule(f"det{i}")) for i in range(12)]
    split_a = split_by_rule(records, seed=3)
    split_b = split_by_rule(records, seed=3)
    ids_a = tuple(tuple(r.record_id for r in part) for part in split_a)
    ids_b = tuple(tuple(r.record_id for r in part) for part in split_b)
    assert ids_a == ids_b


# ---------------------------------------------------------------------------
# 4. Policy versioning: only fit() advances the version, never predict().
# ---------------------------------------------------------------------------

def test_policy_version_starts_at_zero_and_only_fit_advances_it():
    policy = StructuralLearningPolicy()
    assert policy.version == 0
    rule = _rule("ver1")
    for _ in range(5):
        policy.predict(rule, 0.5, 0.5, 1, GROUNDED_DIRECT)
    assert policy.version == 0
    fitted = policy.fit([_record("ver1", rule=rule)])
    assert fitted.version == 1
    assert policy.version == 0  # original untouched -- fit() never mutates in place
    fitted_again = fitted.fit([_record("ver2", rule=_rule("ver2"))])
    assert fitted_again.version == 2


# ---------------------------------------------------------------------------
# 5. predict() never fabricates confidence it does not have -- honest backoff.
# ---------------------------------------------------------------------------

def test_predict_on_untrained_policy_is_uniform_with_zero_support():
    policy = StructuralLearningPolicy()
    pred = policy.predict(_rule("untrained"), 0.5, 0.5, 1, GROUNDED_DIRECT)
    assert pred.basis == BASIS_UNIFORM_NO_DATA
    assert pred.support == 0
    assert pred.distribution[SUPPORTED] == pytest.approx(1 / 3)


def test_predict_backs_off_from_exact_bucket_to_rule_to_global_never_overclaiming():
    rule_a = _rule("bucketA")
    rule_b = _rule("bucketB")
    train = [
        _record("a1", rule=rule_a, novelty=0.9, redundancy=0.1, depth=2, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),
        _record("a2", rule=rule_a, novelty=0.9, redundancy=0.1, depth=2, provenance=GROUNDED_DIRECT, outcome=SUPPORTED),
        _record("a3", rule=rule_a, novelty=0.1, redundancy=0.9, depth=5, provenance=UNGROUNDED_HUMAN, outcome=CONTRADICTED),
    ]
    policy = StructuralLearningPolicy().fit(train)

    exact = policy.predict(rule_a, 0.9, 0.1, 2, GROUNDED_DIRECT)
    assert exact.basis == BASIS_EXACT_BUCKET
    assert exact.support == 2
    assert exact.distribution[SUPPORTED] == 1.0

    rule_only = policy.predict(rule_a, 0.5, 0.5, 99, GROUNDED_ANALOGY)  # same rule, unseen bucket
    assert rule_only.basis == BASIS_RULE_ONLY
    assert rule_only.support == 3

    global_prior = policy.predict(rule_b, 0.5, 0.5, 1, GROUNDED_DIRECT)  # never-seen rule
    assert global_prior.basis == BASIS_GLOBAL_PRIOR
    assert global_prior.support == 3


# ---------------------------------------------------------------------------
# 6. Brier score is a proper, bounded score.
# ---------------------------------------------------------------------------

def test_brier_is_zero_for_a_perfectly_confident_correct_policy():
    rule = _rule("perfect")
    train = [_record(f"p{i}", rule=rule, outcome=SUPPORTED) for i in range(10)]
    policy = StructuralLearningPolicy().fit(train)
    holdout = [_record("ptest", rule=rule, outcome=SUPPORTED)]
    assert brier_score_multiclass(policy, holdout) == pytest.approx(0.0)


def test_brier_requires_at_least_one_record():
    policy = StructuralLearningPolicy()
    with pytest.raises(ValueError):
        brier_score_multiclass(policy, [])


def test_brier_is_bounded_between_zero_and_two_on_random_synthetic_data():
    import random
    rng = random.Random(11)
    rules = [_rule(f"bound{i}") for i in range(4)]
    train = [
        _record(f"tr{i}", rule=rng.choice(rules), novelty=rng.random(), redundancy=rng.random(),
                depth=rng.randint(0, 5), provenance=rng.choice([GROUNDED_DIRECT, GROUNDED_ANALOGY, UNGROUNDED_HUMAN]),
                outcome=rng.choice(list(OUTCOME_CLASSES)))
        for i in range(40)
    ]
    holdout = [
        _record(f"ho{i}", rule=rng.choice(rules), novelty=rng.random(), redundancy=rng.random(),
                depth=rng.randint(0, 5), provenance=rng.choice([GROUNDED_DIRECT, GROUNDED_ANALOGY, UNGROUNDED_HUMAN]),
                outcome=rng.choice(list(OUTCOME_CLASSES)))
        for i in range(20)
    ]
    policy = StructuralLearningPolicy().fit(train)
    score = brier_score_multiclass(policy, holdout)
    assert 0.0 <= score <= 2.0


# ---------------------------------------------------------------------------
# 7. calibration_report flags insufficient-data buckets explicitly.
# ---------------------------------------------------------------------------

def test_calibration_report_marks_sparse_buckets_as_insufficient_data():
    rule_common = _rule("common")
    rule_rare = _rule("rare")
    records = [_record(f"c{i}", rule=rule_common, outcome=SUPPORTED) for i in range(10)]
    records.append(_record("rare1", rule=rule_rare, outcome=CONTRADICTED))
    policy = StructuralLearningPolicy().fit(records)

    report = calibration_report(policy, records, "rule", min_support=5)
    by_key = {sl.key: sl for sl in report}
    assert by_key[records[0].rule_signature].sufficient_data is True
    assert by_key[records[-1].rule_signature].sufficient_data is False


def test_calibration_report_rejects_unknown_dimension():
    policy = StructuralLearningPolicy()
    with pytest.raises(ValueError):
        calibration_report(policy, [_record("dim1")], "nonsense")


# ---------------------------------------------------------------------------
# 8. Promotion fails closed.
# ---------------------------------------------------------------------------

def test_promotion_blocked_on_empty_holdout():
    policy = StructuralLearningPolicy().fit([_record("e1")])
    decision = evaluate_promotion(policy, None, [], brier_threshold=1.0)
    assert decision.promote is False
    assert "EMPTY_HOLDOUT" in decision.reasons


def test_promotion_blocked_when_above_absolute_threshold_even_with_no_previous_version():
    rule = _rule("thresh")
    # Deliberately miscalibrated: train says SUPPORTED, holdout is CONTRADICTED.
    policy = StructuralLearningPolicy().fit([_record("t1", rule=rule, outcome=SUPPORTED)])
    holdout = [_record("t2", rule=rule, outcome=CONTRADICTED)]
    decision = evaluate_promotion(policy, None, holdout, brier_threshold=0.1)
    assert decision.promote is False
    assert "HOLDOUT_BRIER_ABOVE_THRESHOLD" in decision.reasons


def test_promotion_blocked_on_regression_versus_previous_version():
    rule = _rule("regress")
    good_previous = StructuralLearningPolicy().fit([_record("g1", rule=rule, outcome=SUPPORTED)])
    bad_candidate = StructuralLearningPolicy().fit([_record("b1", rule=rule, outcome=CONTRADICTED)])
    holdout = [_record("h1", rule=rule, outcome=SUPPORTED)]
    decision = evaluate_promotion(bad_candidate, good_previous, holdout, brier_threshold=2.0)
    assert decision.promote is False
    assert "REGRESSION_VS_PREVIOUS_VERSION" in decision.reasons


def test_promotion_allowed_when_all_gates_clear():
    rule = _rule("clear")
    policy = StructuralLearningPolicy().fit([_record(f"cl{i}", rule=rule, outcome=SUPPORTED) for i in range(5)])
    holdout = [_record("clh", rule=rule, outcome=SUPPORTED)]
    decision = evaluate_promotion(policy, None, holdout, brier_threshold=0.5)
    assert decision.promote is True
    assert decision.reasons == ()


def test_sparse_bucket_never_blocks_promotion_below_min_support():
    """A catastrophically wrong prediction on a bucket with only 1 example
    must not block promotion at min_bucket_support=5 -- there is not enough
    evidence to trust that bucket either way, and the gate must say so rather
    than silently treating sparse-but-bad as safe OR unfairly vetoing it."""
    common_rule = _rule("sparse_common")
    rare_rule = _rule("sparse_rare")
    train = [_record(f"sc{i}", rule=common_rule, outcome=SUPPORTED) for i in range(10)]
    train.append(_record("sr1", rule=rare_rule, outcome=SUPPORTED))
    policy = StructuralLearningPolicy().fit(train)
    holdout = [_record("sch", rule=common_rule, outcome=SUPPORTED), _record("srh", rule=rare_rule, outcome=CONTRADICTED)]
    decision = evaluate_promotion(
        policy, None, holdout, brier_threshold=1.0, per_bucket_brier_threshold=0.5, min_bucket_support=5
    )
    assert not any(r.startswith("CATASTROPHIC_BUCKET") for r in decision.reasons)
