"""M6 -- INDEPENDENT HOLDOUT step, corpus v0.2 v0.1.

Roadmap trajectory: M6 THIRD-PARTY VALIDATION -> INDEPENDENT HOLDOUT -> M7.
corpus/family_tree_facts_v0_1.json (frozen, used by
MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md) has only 2 real
evidence-backed rules -- too few for split_by_rule to produce any holdout at
default fractions. corpus/family_tree_facts_v0_2.json extends it with two
more independent family branches (same kind of hand-authored, internally
consistent data, not a different sourcing method) so a genuine non-empty
holdout is reachable.

Honesty check, not just a bigger number: a non-empty holdout is necessary
but not sufficient for a meaningful calibration result. This suite verifies
BOTH that the pipeline now runs end to end on a genuine holdout, AND that
the resulting Brier/ECE of 0.0 is a known degenerate case (every record's
outcome is SUPPORTED) rather than evidence of calibration skill -- the
replay-based evidence mechanism can, on any internally consistent corpus,
structurally only ever produce SUPPORTED or no evidence at all (see
m6_corpus_from_m4_m5_v0_1.py's module docstring); it cannot yet produce a
genuine CONTRADICTED or evidenced-UNKNOWN outcome from real data. A
discriminative calibration demonstration needs a richer evidence mechanism,
not a bigger corpus of the same kind -- documented here as the next open
question, not silently left implicit.
"""
from __future__ import annotations

from pathlib import Path

from m6_corpus_from_m4_m5_v0_1 import build_real_corpus
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    brier_score_multiclass,
    evaluate_promotion,
    expected_calibration_error_top_label,
    split_by_rule,
)

# Defined locally, not imported from m6_corpus_from_m4_m5_v0_1.py: that module
# is frozen and its hash is checked by MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md
# -- a prior mistake added this constant there instead, silently invalidating
# the frozen hash (caught by an external reviewer's execution, reverted).
CORPUS_PATH_V0_2 = Path(__file__).resolve().parent.parent / "corpus" / "family_tree_facts_v0_2.json"


def test_v0_2_corpus_produces_more_real_evidenced_rules_than_v0_1():
    report = build_real_corpus(CORPUS_PATH_V0_2)
    assert report.candidate_patterns_considered == 69
    assert len(report.records) == 23
    assert len(report.excluded_no_evidence) == 46


def test_v0_2_corpus_yields_a_genuine_non_empty_holdout():
    report = build_real_corpus(CORPUS_PATH_V0_2)
    train, val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert len(holdout) > 0
    assert len(train) > 0
    assert len(val) > 0
    assert len(train) + len(val) + len(holdout) == len(report.records)


def test_v0_2_holdout_split_is_deterministic_across_two_runs():
    report_a = build_real_corpus(CORPUS_PATH_V0_2)
    report_b = build_real_corpus(CORPUS_PATH_V0_2)
    split_a = split_by_rule(report_a.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    split_b = split_by_rule(report_b.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    ids_a = tuple(tuple(r.record_id for r in part) for part in split_a)
    ids_b = tuple(tuple(r.record_id for r in part) for part in split_b)
    assert ids_a == ids_b


def test_v0_2_promotion_pipeline_runs_end_to_end_on_a_real_holdout():
    report = build_real_corpus(CORPUS_PATH_V0_2)
    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)
    decision = evaluate_promotion(policy, None, holdout, brier_threshold=0.5)
    assert decision.holdout_brier is not None  # a real number was computed, not skipped as EMPTY_HOLDOUT
    assert decision.promote is True


def test_v0_2_zero_brier_is_a_known_degenerate_single_class_case_not_calibration_skill():
    """The honest half of this suite: confirms WHY holdout Brier/ECE are 0.0
    here, so this is never mistaken for a demonstrated calibration result."""
    report = build_real_corpus(CORPUS_PATH_V0_2)
    assert {r.outcome for r in report.records} == {"SUPPORTED"}  # single class -- see module docstring
    assert {r.provenance for r in report.records} == {"GROUNDED_DIRECT"}

    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)
    assert brier_score_multiclass(policy, holdout) == 0.0
    assert expected_calibration_error_top_label(policy, holdout, n_bins=5) == 0.0
