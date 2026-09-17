"""M6 -- Critical Validation v0.1.

Third-party validation suite for MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md.
Cases C01-C09 map 1:1 to that protocol's critical contract. This file is
self-contained (does not import from the other M6 test files) and does not
modify any of the frozen modules it imports.
"""
from __future__ import annotations

import pytest

from kernel2 import Node, OBSERVATION, build_structural_graph, compare, discover_paths, generalize_path_pattern, node_ref
from m4_cold_start_evidence_v0_1 import CONTRADICTED, DERIVED, GROUNDED_DIRECT, SUPPORTED
from m6_corpus_from_m4_m5_v0_1 import build_real_corpus, demo_contradicted_case
from m6_structural_learning_v0_1 import (
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
    return _obs(a_id, op, a1, a2, out), _obs(b_id, op, a2, a1, out)


def _rule(seed: str) -> Node:
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
# C01 -- No DERIVED gold.
# ---------------------------------------------------------------------------

def test_c01_derived_is_never_accepted_as_a_learning_outcome():
    with pytest.raises(ValueError):
        _record("c01", outcome=DERIVED)


# ---------------------------------------------------------------------------
# C02 -- Rule identity is structural, not referential, for both rule kinds.
# ---------------------------------------------------------------------------

def test_c02_node_pattern_identity_is_structural():
    a1, b1 = _swap12("c02n1a", "c02n1b", "OP_C02N", "A", "B", "C")
    a2, b2 = _swap12("c02n2a", "c02n2b", "OP_C02N", "A", "B", "C")
    p1, p2 = compare(a1, b1), compare(a2, b2)
    assert p1 is not p2
    assert _record("c02n1", rule=p1).rule_signature == _record("c02n2", rule=p2).rule_signature


def test_c02_pathpattern_identity_is_structural():
    def chain(prefix):
        facts = [
            Node(f"{prefix}1", OBSERVATION, (node_ref("R"), node_ref(f"{prefix}A"), node_ref(f"{prefix}B")), provenance=(f"{prefix}1",)),
            Node(f"{prefix}2", OBSERVATION, (node_ref("S"), node_ref(f"{prefix}B"), node_ref(f"{prefix}C")), provenance=(f"{prefix}2",)),
        ]
        graph = build_structural_graph(facts)
        return discover_paths(graph, start=node_ref(f"{prefix}A"), end=node_ref(f"{prefix}C"), max_depth=2)[0]

    pattern_1 = generalize_path_pattern([chain("c02p1"), chain("c02p2")], pattern_id="event_A")
    pattern_2 = generalize_path_pattern([chain("c02p3"), chain("c02p4")], pattern_id="event_B")
    assert pattern_1 != pattern_2  # different pattern_id/source_path_ids
    assert _record("c02p_1", rule=pattern_1).rule_signature == _record("c02p_2", rule=pattern_2).rule_signature


# ---------------------------------------------------------------------------
# C03 -- Holdout split never scatters one rule, and is deterministic.
# ---------------------------------------------------------------------------

def test_c03_split_by_rule_never_splits_one_rule_and_is_deterministic():
    records = []
    for i in range(15):
        rule = _rule(f"c03_{i}")
        records.extend(_record(f"c03_{i}_{j}", rule=rule) for j in range(3))

    train, val, holdout = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=5)
    rule_sets = [{r.rule_signature for r in part} for part in (train, val, holdout)]
    assert rule_sets[0].isdisjoint(rule_sets[1])
    assert rule_sets[0].isdisjoint(rule_sets[2])
    assert rule_sets[1].isdisjoint(rule_sets[2])

    train2, val2, holdout2 = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=5)
    assert [r.record_id for r in train] == [r.record_id for r in train2]
    assert [r.record_id for r in holdout] == [r.record_id for r in holdout2]


# ---------------------------------------------------------------------------
# C04 -- Policy version advances only through fit(), never predict().
# ---------------------------------------------------------------------------

def test_c04_version_only_advances_through_fit():
    policy = StructuralLearningPolicy()
    assert policy.version == 0
    rule = _rule("c04")
    for _ in range(10):
        policy.predict(rule, 0.5, 0.5, 1, GROUNDED_DIRECT)
    assert policy.version == 0
    fitted = policy.fit([_record("c04", rule=rule)])
    assert fitted.version == 1
    assert policy.version == 0


# ---------------------------------------------------------------------------
# C05 -- predict() never fabricates confidence: honest backoff hierarchy.
# ---------------------------------------------------------------------------

def test_c05_backoff_hierarchy_is_honest():
    fresh = StructuralLearningPolicy()
    pred = fresh.predict(_rule("c05_untrained"), 0.5, 0.5, 1, GROUNDED_DIRECT)
    assert pred.basis == BASIS_UNIFORM_NO_DATA and pred.support == 0

    rule_a, rule_b = _rule("c05_a"), _rule("c05_b")
    policy = StructuralLearningPolicy().fit([
        _record("c05_1", rule=rule_a, novelty=0.9, redundancy=0.1, depth=2, outcome=SUPPORTED),
        _record("c05_2", rule=rule_a, novelty=0.9, redundancy=0.1, depth=2, outcome=SUPPORTED),
    ])
    assert policy.predict(rule_a, 0.9, 0.1, 2, GROUNDED_DIRECT).basis == BASIS_EXACT_BUCKET
    assert policy.predict(rule_a, 0.1, 0.9, 9, GROUNDED_DIRECT).basis == BASIS_RULE_ONLY
    assert policy.predict(rule_b, 0.5, 0.5, 1, GROUNDED_DIRECT).basis == BASIS_GLOBAL_PRIOR


# ---------------------------------------------------------------------------
# C06 -- Calibration is proper, bounded, and sparse buckets are flagged.
# ---------------------------------------------------------------------------

def test_c06_brier_is_bounded_and_zero_for_perfect_prediction():
    rule = _rule("c06")
    policy = StructuralLearningPolicy().fit([_record(f"c06_{i}", rule=rule, outcome=SUPPORTED) for i in range(5)])
    assert brier_score_multiclass(policy, [_record("c06_test", rule=rule, outcome=SUPPORTED)]) == pytest.approx(0.0)


def test_c06_sparse_buckets_are_flagged_not_hidden():
    common, rare = _rule("c06_common"), _rule("c06_rare")
    records = [_record(f"c06_c{i}", rule=common, outcome=SUPPORTED) for i in range(8)]
    records.append(_record("c06_r1", rule=rare, outcome=CONTRADICTED))
    policy = StructuralLearningPolicy().fit(records)
    report = calibration_report(policy, records, "rule", min_support=5)
    by_key = {sl.key: sl for sl in report}
    assert by_key[records[0].rule_signature].sufficient_data is True
    assert by_key[records[-1].rule_signature].sufficient_data is False


# ---------------------------------------------------------------------------
# C07 -- Promotion fails closed; a sparse bucket never blocks it unfairly.
# ---------------------------------------------------------------------------

def test_c07_promotion_blocked_on_empty_holdout():
    decision = evaluate_promotion(StructuralLearningPolicy().fit([_record("c07a")]), None, [], brier_threshold=1.0)
    assert decision.promote is False and decision.reasons == ("EMPTY_HOLDOUT",)


def test_c07_promotion_blocked_on_regression_versus_previous():
    rule = _rule("c07b")
    good = StructuralLearningPolicy().fit([_record("c07b_prev", rule=rule, outcome=SUPPORTED)])
    bad = StructuralLearningPolicy().fit([_record("c07b_cand", rule=rule, outcome=CONTRADICTED)])
    decision = evaluate_promotion(bad, good, [_record("c07b_ho", rule=rule, outcome=SUPPORTED)], brier_threshold=2.0)
    assert decision.promote is False and "REGRESSION_VS_PREVIOUS_VERSION" in decision.reasons


def test_c07_sparse_bucket_never_blocks_promotion():
    common, rare = _rule("c07c_common"), _rule("c07c_rare")
    train = [_record(f"c07c_{i}", rule=common, outcome=SUPPORTED) for i in range(8)]
    train.append(_record("c07c_rare_train", rule=rare, outcome=SUPPORTED))
    policy = StructuralLearningPolicy().fit(train)
    holdout = [_record("c07c_common_ho", rule=common, outcome=SUPPORTED), _record("c07c_rare_ho", rule=rare, outcome=CONTRADICTED)]
    decision = evaluate_promotion(policy, None, holdout, brier_threshold=1.0, per_bucket_brier_threshold=0.5, min_bucket_support=5)
    assert not any(r.startswith("CATASTROPHIC_BUCKET") for r in decision.reasons)


# ---------------------------------------------------------------------------
# C08 -- Real-corpus records trace to genuine M4 evidence; exclusions are honest.
# ---------------------------------------------------------------------------

def test_c08_real_corpus_records_trace_to_genuine_evidence():
    report = build_real_corpus()
    assert report.candidate_patterns_considered == 28
    assert len(report.records) == 2
    assert len(report.excluded_no_evidence) == 26
    assert all(r.provenance == GROUNDED_DIRECT and r.outcome == SUPPORTED for r in report.records)


# ---------------------------------------------------------------------------
# C09 -- The negative (CONTRADICTED) path works on real machinery, kept
#         explicitly separate from the real-corpus statistics.
# ---------------------------------------------------------------------------

def test_c09_negative_evidence_path_reaches_contradicted():
    demo = demo_contradicted_case()
    assert demo.outcome == CONTRADICTED
    assert demo.provenance == GROUNDED_DIRECT
