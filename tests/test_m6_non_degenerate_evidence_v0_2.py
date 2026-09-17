"""M6 -- non-degenerate evidence mechanism v0.2 tests.

Confirms m6_corpus_from_m4_m5_v0_2.py actually solves the degeneracy found
and documented in MetaHIA_M6_Structural_Learning_V0_1.md Sec. 6 (v0.1's
mechanism could only ever produce SUPPORTED or no evidence): with an
independent, deliberately partly-wrong verification claims corpus, the same
real acquire_cold_start() machinery now produces genuine outcome diversity,
and a genuinely non-trivial (neither 0 nor 2) holdout Brier score -- across
BOTH length-1 (direct) and length-2 (derived) patterns, extended 2026-09-17.
"""
from __future__ import annotations

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_DIRECT, SUPPORTED
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    brier_score_multiclass,
    evaluate_promotion,
    expected_calibration_error_top_label,
    split_by_rule,
)


def test_v2_mechanism_produces_genuine_outcome_diversity():
    """The headline fix: v0.1 could only ever produce {SUPPORTED} (or
    exclude). v0.2 must produce both SUPPORTED and CONTRADICTED from the
    same real machinery, driven by the independent claims corpus."""
    report = build_real_corpus_v2()
    assert report.candidate_patterns_considered == 69
    assert len(report.records) == 26
    outcomes = {r.outcome for r in report.records}
    assert outcomes == {SUPPORTED, CONTRADICTED}
    assert sum(1 for r in report.records if r.outcome == SUPPORTED) == 16
    assert sum(1 for r in report.records if r.outcome == CONTRADICTED) == 10


def test_v2_covers_both_length_1_and_length_2_patterns():
    """Extension 2026-09-17: claims are keyed by full skeleton, not just a
    single (subject, operator, direction), so a witness can confirm/deny a
    multi-hop derived relation exactly as a direct one."""
    report = build_real_corpus_v2()
    depths = {r.depth for r in report.records}
    assert depths == {1, 2}
    length_one = [r for r in report.records if r.depth == 1]
    length_two = [r for r in report.records if r.depth == 2]
    assert len(length_one) == 16
    assert len(length_two) == 10
    # both lengths individually show outcome diversity, not just the corpus as a whole
    assert {r.outcome for r in length_one} == {SUPPORTED, CONTRADICTED}
    assert {r.outcome for r in length_two} == {SUPPORTED, CONTRADICTED}


def test_v2_all_records_are_grounded_direct():
    report = build_real_corpus_v2()
    assert all(r.provenance == GROUNDED_DIRECT for r in report.records)


def test_v2_exclusions_are_reported_not_silently_dropped():
    report = build_real_corpus_v2()
    assert len(report.excluded_no_verification_claim) == 49


def test_v2_holdout_split_is_non_empty_and_deterministic():
    report = build_real_corpus_v2()
    train, val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert len(holdout) > 0 and len(train) > 0
    train2, val2, holdout2 = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert [r.record_id for r in holdout] == [r.record_id for r in holdout2]


def test_v2_holdout_brier_is_genuinely_non_degenerate():
    """Not 0.0 (perfect, as v0.1 always trivially was) and not 2.0 (maximally
    wrong) -- a real, informative number computed from genuine disagreement
    in the training data."""
    report = build_real_corpus_v2()
    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)
    brier = brier_score_multiclass(policy, holdout)
    assert 0.0 < brier < 2.0
    assert brier == 0.48125  # pinned for regression detection

    ece = expected_calibration_error_top_label(policy, holdout, n_bins=5)
    assert 0.0 <= ece < 1.0


def test_v2_promotion_gate_responds_to_the_threshold_on_real_data():
    report = build_real_corpus_v2()
    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)

    strict = evaluate_promotion(policy, None, holdout, brier_threshold=0.4)
    assert strict.promote is False and strict.reasons == ("HOLDOUT_BRIER_ABOVE_THRESHOLD",)

    lenient = evaluate_promotion(policy, None, holdout, brier_threshold=0.6)
    assert lenient.promote is True and lenient.reasons == ()
