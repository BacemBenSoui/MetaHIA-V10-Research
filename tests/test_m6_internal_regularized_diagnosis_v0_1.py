"""Permanent invariant tests for M6 -- internal-learning regularization
diagnosis v0.1 (`m6_internal_regularized_diagnosis_v0_1.py`).

Uses small, hand-constructed synthetic records for most tests, plus one
real (but small, fast, network-free) domain corpus for the M6_RAW
consistency check against the actual `StructuralLearningPolicy`. Real
multi-domain numbers are computed separately by
`scripts/run_m6_internal_regularized_diagnosis_v0_1.py` and reported in
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md`, never pinned
here.
"""
from __future__ import annotations

from collections import Counter

import pytest

from kernel2 import Node, OBSERVATION, node_ref
from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_DIRECT, SUPPORTED, UNKNOWN
from m6_corpus_from_supply_chain_v0_1 import build_supply_chain_corpus
from m6_internal_learning_diagnosis_v0_1 import split_within_rule
from m6_internal_regularized_diagnosis_v0_1 import (
    RegularizedPolicy,
    build_policy_variants,
    comparison_result_to_dict,
    laplace_smoothing,
    measure_convergence,
    raw_smoothing,
    run_convergence_benchmark,
    run_regularized_comparison,
    run_regularized_comparison_multi_seed,
    support_weighted_smoothing,
)
from m6_structural_learning_v0_1 import (
    OUTCOME_CLASSES,
    StructuralLearningPolicy,
    StructuralOutcomeRecord,
    brier_score_multiclass,
    expected_calibration_error_top_label,
)


def _pattern(name: str) -> Node:
    return Node(f"rule::{name}", OBSERVATION, (node_ref(name),))


def _record(record_id, rule_name, *, novelty=0.5, redundancy=0.5, depth=1, provenance=GROUNDED_DIRECT, outcome) -> StructuralOutcomeRecord:
    return StructuralOutcomeRecord(
        record_id=record_id, rule=_pattern(rule_name), novelty=novelty, redundancy=redundancy,
        depth=depth, provenance=provenance, outcome=outcome,
    )


# ---------------------------------------------------------------------------
# 1. M6_RAW must reproduce the real StructuralLearningPolicy exactly.
# ---------------------------------------------------------------------------


def test_m6_raw_reproduces_the_real_structural_learning_policy_exactly():
    """The consistency check the module's own docstring promises: an
    independently-rebuilt cascade must match the real, validated
    policy's numbers exactly on real data, not merely by inspection."""
    records = build_supply_chain_corpus().records
    train, _val, holdout = split_within_rule(records, holdout_fraction=0.5, seed=0)
    assert holdout  # this corpus must actually produce a non-empty internal holdout

    real_policy = StructuralLearningPolicy().fit(train)
    raw_twin = RegularizedPolicy("M6_RAW", raw_smoothing).fit(train)

    assert brier_score_multiclass(real_policy, holdout) == pytest.approx(brier_score_multiclass(raw_twin, holdout))
    assert expected_calibration_error_top_label(real_policy, holdout) == pytest.approx(
        expected_calibration_error_top_label(raw_twin, holdout)
    )


# ---------------------------------------------------------------------------
# 2. Smoothing functions produce hand-computed values.
# ---------------------------------------------------------------------------


def test_laplace_smoothing_hand_computed():
    counts = Counter({SUPPORTED: 1})
    dist, support = laplace_smoothing(1.0)(counts, Counter())
    assert support == 1
    assert dist[SUPPORTED] == pytest.approx(2 / 4)
    assert dist[CONTRADICTED] == pytest.approx(1 / 4)
    assert dist[UNKNOWN] == pytest.approx(1 / 4)


def test_laplace_alpha_half_hand_computed():
    counts = Counter({SUPPORTED: 1})
    dist, support = laplace_smoothing(0.5)(counts, Counter())
    assert support == 1
    assert dist[SUPPORTED] == pytest.approx(1.5 / 2.5)
    assert dist[CONTRADICTED] == pytest.approx(0.5 / 2.5)


def test_support_weighted_smoothing_hand_computed():
    local = Counter({SUPPORTED: 1})
    glob = Counter({SUPPORTED: 5, CONTRADICTED: 5})  # 50/50 global prior
    dist, support = support_weighted_smoothing(1.0)(local, glob)
    assert support == 1
    # weight = 1/(1+1) = 0.5; local_dist SUPPORTED=1.0; global_dist 0.5/0.5
    assert dist[SUPPORTED] == pytest.approx(0.5 * 1.0 + 0.5 * 0.5)
    assert dist[CONTRADICTED] == pytest.approx(0.5 * 0.0 + 0.5 * 0.5)


def test_support_weighted_smoothing_approaches_local_estimate_as_support_grows():
    glob = Counter({SUPPORTED: 5, CONTRADICTED: 5})
    _dist_n1, _ = support_weighted_smoothing(1.0)(Counter({SUPPORTED: 1}), glob)
    dist_n20, _ = support_weighted_smoothing(1.0)(Counter({SUPPORTED: 20}), glob)
    assert dist_n20[SUPPORTED] > _dist_n1[SUPPORTED]  # weight grows toward 1 (fully local) as n grows
    assert dist_n20[SUPPORTED] == pytest.approx(20 / 21 * 1.0 + 1 / 21 * 0.5)


def test_raw_smoothing_matches_plain_frequency_no_smoothing():
    counts = Counter({SUPPORTED: 3, CONTRADICTED: 1})
    dist, support = raw_smoothing(counts, Counter())
    assert support == 4
    assert dist[SUPPORTED] == pytest.approx(0.75)
    assert dist[CONTRADICTED] == pytest.approx(0.25)
    assert dist[UNKNOWN] == 0.0


# ---------------------------------------------------------------------------
# 3. RegularizedPolicy's cascade order (basis naming) and fail-closed paths.
# ---------------------------------------------------------------------------


def test_regularized_policy_cascade_reaches_exact_bucket_then_rule_only_then_global_then_uniform():
    policy = RegularizedPolicy("TEST", raw_smoothing)
    train = (
        _record("t1", "RULE_A", novelty=0.9, redundancy=0.1, depth=1, outcome=SUPPORTED),
        _record("t2", "RULE_A", novelty=0.1, redundancy=0.1, depth=1, outcome=CONTRADICTED),  # different bucket, same rule
        _record("t3", "RULE_B", novelty=0.5, redundancy=0.5, depth=1, outcome=UNKNOWN),
    )
    fitted = policy.fit(train)

    exact = fitted.predict(_pattern("RULE_A"), 0.9, 0.1, 1, GROUNDED_DIRECT)
    assert exact.basis == "TEST_EXACT_BUCKET" and exact.support == 1

    rule_only = fitted.predict(_pattern("RULE_A"), 0.5, 0.5, 1, GROUNDED_DIRECT)  # same rule, unseen bucket
    assert rule_only.basis == "TEST_RULE_ONLY" and rule_only.support == 2

    global_prior = fitted.predict(_pattern("RULE_C"), 0.5, 0.5, 1, GROUNDED_DIRECT)  # unseen rule entirely
    assert global_prior.basis == "TEST_GLOBAL_PRIOR" and global_prior.support == 3

    empty_policy = RegularizedPolicy("TEST", raw_smoothing).fit(())
    uniform = empty_policy.predict(_pattern("RULE_A"), 0.5, 0.5, 1, GROUNDED_DIRECT)
    assert uniform.basis == "TEST_UNIFORM_NO_DATA"
    assert all(v == pytest.approx(1 / 3) for v in uniform.distribution.values())


def test_build_policy_variants_has_the_five_expected_names():
    variants = build_policy_variants()
    assert set(variants.keys()) == {"GLOBAL_ONLY", "M6_RAW", "M6_LAPLACE_A1", "M6_LAPLACE_A0.5", "M6_SUPPORT_WEIGHTED_K1"}


# ---------------------------------------------------------------------------
# 4. Real-split comparison harness (Measure A).
# ---------------------------------------------------------------------------


def test_run_regularized_comparison_returns_none_on_too_small_a_corpus():
    records = tuple(_record(f"r{i}", f"RULE_{i}", outcome=SUPPORTED) for i in range(5))  # every rule has 1 record
    result = run_regularized_comparison(records, domain="tiny")
    assert result is None


def test_run_regularized_comparison_scores_every_variant_on_a_real_corpus():
    records = build_supply_chain_corpus().records
    result = run_regularized_comparison(records, domain="supply_chain", seed=0)
    assert result is not None
    assert set(result.brier.keys()) == {"GLOBAL_ONLY", "M6_RAW", "M6_LAPLACE_A1", "M6_LAPLACE_A0.5", "M6_SUPPORT_WEIGHTED_K1"}
    assert set(result.ece.keys()) == set(result.brier.keys())
    # M6_RAW must match the already-measured real-policy finding exactly (Sec.13): worse than GLOBAL_ONLY.
    assert result.brier_delta_vs_global_only("M6_RAW") > 0


def test_multi_seed_comparison_keeps_each_seed_distinct():
    records = build_supply_chain_corpus().records
    results = run_regularized_comparison_multi_seed(records, domain="supply_chain", seeds=range(5))
    assert len(results) >= 1
    assert len({r.seed for r in results}) == len(results)


def test_comparison_result_to_dict_is_json_serializable():
    import json

    records = build_supply_chain_corpus().records
    result = run_regularized_comparison(records, domain="supply_chain", seed=0)
    payload = comparison_result_to_dict(result)
    json.dumps(payload)  # must not raise
    assert "M6_RAW" in payload["brier"]


# ---------------------------------------------------------------------------
# 5. Synthetic convergence benchmark (Measure B).
# ---------------------------------------------------------------------------


def test_measure_convergence_rejects_a_distribution_that_does_not_sum_to_one():
    with pytest.raises(ValueError):
        measure_convergence({SUPPORTED: 0.5, CONTRADICTED: 0.3}, n=5)


def test_raw_has_higher_expected_error_than_regularized_variants_at_support_one():
    """The central Measure B claim: at support=1, an unregularized
    point estimate is maximally overconfident, so on a truly mixed
    (50/50) distribution its expected squared error must exceed every
    regularized variant's -- checked with enough trials to be stable,
    not asserted from theory alone."""
    mse = measure_convergence({SUPPORTED: 0.5, CONTRADICTED: 0.5}, n=1, n_trials=400, seed=0)
    assert mse["M6_RAW"] > mse["M6_LAPLACE_A1"]
    assert mse["M6_RAW"] > mse["M6_SUPPORT_WEIGHTED_K1"]


def test_all_variants_improve_as_support_grows_on_a_skewed_distribution():
    """Convergence, not just relative ranking: every variant's error
    against a 90/10 true distribution should shrink from support=1 to
    support=20."""
    dist = {SUPPORTED: 0.9, CONTRADICTED: 0.1}
    mse_n1 = measure_convergence(dist, n=1, n_trials=300, seed=1)
    mse_n20 = measure_convergence(dist, n=20, n_trials=300, seed=1)
    for name in mse_n1:
        assert mse_n20[name] < mse_n1[name], name


def test_run_convergence_benchmark_produces_the_expected_table_shape():
    table = run_convergence_benchmark(
        {"fifty_fifty": {SUPPORTED: 0.5, CONTRADICTED: 0.5}}, supports=(1, 5), n_trials=50, seed=0
    )
    assert set(table.keys()) == {"fifty_fifty"}
    assert set(table["fifty_fifty"].keys()) == {1, 5}
    assert set(table["fifty_fifty"][1].keys()) == set(build_policy_variants().keys())


def test_run_convergence_benchmark_is_json_serializable():
    import json

    table = run_convergence_benchmark(
        {"fifty_fifty": {SUPPORTED: 0.5, CONTRADICTED: 0.5}}, supports=(1,), n_trials=20, seed=0
    )
    json.dumps(table)  # must not raise
