"""M6 v0.2 (non-degenerate evidence mechanism) -- Critical Validation v0.1.

Third-party validation suite for
MetaHIA_ThirdParty_Validation_Protocol_M6_V0_2_V0_1.md. Cases C01-C07 map
1:1 to that protocol's critical contract. Self-contained: does not import
from the other M6 test files, does not modify any frozen module.
"""
from __future__ import annotations

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_DIRECT, SUPPORTED
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    brier_score_multiclass,
    evaluate_promotion,
    split_by_rule,
)


# ---------------------------------------------------------------------------
# C01 -- Evidence comes from independent verification, not structural replay alone.
# ---------------------------------------------------------------------------

def test_c01_outcome_depends_on_independent_claim_not_replay_alone():
    """Every REPLAYED structural match is, by construction, correct against
    the graph it was replayed on -- so if outcomes were still decided by
    replay success alone, everything would be SUPPORTED. The presence of any
    CONTRADICTED record here proves the independent claims corpus, not the
    replay itself, is what determines the outcome."""
    report = build_real_corpus_v2()
    assert any(r.outcome == CONTRADICTED for r in report.records)


# ---------------------------------------------------------------------------
# C02 -- Genuine, non-degenerate outcome diversity from the same real machinery.
# ---------------------------------------------------------------------------

def test_c02_both_outcomes_are_reachable_and_both_present():
    report = build_real_corpus_v2()
    outcomes = {r.outcome for r in report.records}
    assert outcomes == {SUPPORTED, CONTRADICTED}
    assert len(report.records) >= 2


# ---------------------------------------------------------------------------
# C03 -- Claims are matched by full skeleton (any length), not length-1 only.
# ---------------------------------------------------------------------------

def test_c03_both_length_1_and_length_2_patterns_get_real_evidence():
    report = build_real_corpus_v2()
    depths = {r.depth for r in report.records}
    assert 1 in depths
    assert 2 in depths


# ---------------------------------------------------------------------------
# C04 -- Repeatability.
# ---------------------------------------------------------------------------

def test_c04_build_real_corpus_v2_is_repeatable():
    report_a = build_real_corpus_v2()
    report_b = build_real_corpus_v2()
    ids_a = sorted(r.record_id for r in report_a.records)
    ids_b = sorted(r.record_id for r in report_b.records)
    assert ids_a == ids_b
    outcomes_a = {r.record_id: r.outcome for r in report_a.records}
    outcomes_b = {r.record_id: r.outcome for r in report_b.records}
    assert outcomes_a == outcomes_b


# ---------------------------------------------------------------------------
# C05 -- Genuine, non-degenerate holdout calibration.
# ---------------------------------------------------------------------------

def test_c05_holdout_brier_is_strictly_between_zero_and_two():
    report = build_real_corpus_v2()
    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert len(holdout) > 0
    policy = StructuralLearningPolicy().fit(train)
    brier = brier_score_multiclass(policy, holdout)
    assert 0.0 < brier < 2.0


# ---------------------------------------------------------------------------
# C06 -- Promotion gate responds to the threshold on this same real data.
# ---------------------------------------------------------------------------

def test_c06_promotion_gate_blocks_and_allows_depending_on_threshold():
    report = build_real_corpus_v2()
    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)
    brier = brier_score_multiclass(policy, holdout)

    strict = evaluate_promotion(policy, None, holdout, brier_threshold=brier - 0.05)
    assert strict.promote is False

    lenient = evaluate_promotion(policy, None, holdout, brier_threshold=brier + 0.05)
    assert lenient.promote is True


# ---------------------------------------------------------------------------
# C07 -- Honest exclusion: unmatched candidates are counted, never fabricated.
# ---------------------------------------------------------------------------

def test_c07_unmatched_candidates_are_excluded_and_counted():
    """A pattern can yield more than one record (one per matching evidence
    start), so the count relationship is over DISTINCT patterns, not raw
    record count: every candidate pattern either produced at least one
    record or was explicitly excluded -- never neither, never both."""
    report = build_real_corpus_v2()
    assert report.candidate_patterns_considered > len(report.records)

    patterns_with_records = {r.record_id[len("realv2::"):].rsplit("::", 1)[0] for r in report.records}
    excluded_patterns = {msg.split(": ", 1)[0] for msg in report.excluded_no_verification_claim}
    assert patterns_with_records.isdisjoint(excluded_patterns)
    assert len(patterns_with_records) + len(excluded_patterns) == report.candidate_patterns_considered
    assert all(r.provenance == GROUNDED_DIRECT for r in report.records)
