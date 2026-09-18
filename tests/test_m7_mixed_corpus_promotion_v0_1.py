"""M7 -- mixed-corpus promotion integration tests v0.1.

Uses an injected fake `generate_fn` throughout (no network, no dependency on
a running Ollama instance) to test the MECHANICS of combining M7's LLM
evidence with M6's adversarial-corpus evidence: record union, rule-signature
parity between the adversarial-only and combined record sets (the fairness
property `compare_calibration_with_and_without_llm_evidence` relies on), and
that the comparison function degenerates correctly to "no difference" when
the LLM proposes nothing.

The REAL, non-deterministic comparison (actual Ollama call, actual holdout
Brier/ECE with vs without LLM evidence) is not pinned here -- see
tests/test_m7_mixed_corpus_live_demo_v0_1.py (skippable, structural
assertions only) and MetaHIA_M7_LLM_Fact_Proposer_V0_1.md Sec.6 for the real
observed numbers from an actual run.
"""
from __future__ import annotations

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m7_corpus_mixed_v0_1 import build_mixed_corpus, compare_calibration_with_and_without_llm_evidence


def _no_proposal(prompt: str):
    return None


def _always_answers(prompt: str):
    return {"object": "Placeholder"}


def test_llm_records_are_empty_when_the_model_proposes_nothing():
    report = build_mixed_corpus(generate_fn=_no_proposal)
    assert report.llm_records == ()
    assert report.combined_records == report.adversarial_records


def test_combined_records_are_the_union_of_both_sources():
    report = build_mixed_corpus(generate_fn=_always_answers)
    assert len(report.llm_records) > 0  # a placeholder answer is a well-formed proposal, so evidence IS produced
    assert len(report.combined_records) == len(report.adversarial_records) + len(report.llm_records)
    assert set(r.record_id for r in report.combined_records) == set(r.record_id for r in report.adversarial_records) | set(
        r.record_id for r in report.llm_records
    )


def test_llm_evidence_never_introduces_a_rule_absent_from_the_adversarial_corpus():
    """Fairness property the module docstring relies on: the LLM mechanism
    only asks about patterns ALREADY discovered from the same corpus file, so
    it can only add records for rules the adversarial corpus already knows
    about -- never a brand-new rule signature. This is what makes
    split_by_rule() assign the SAME holdout rules to both the baseline and
    the mixed run under the same seed."""
    report = build_mixed_corpus(generate_fn=_always_answers)
    adversarial_rules = {r.rule_signature for r in report.adversarial_records}
    combined_rules = {r.rule_signature for r in report.combined_records}
    assert combined_rules == adversarial_rules


def test_comparison_degenerates_to_identical_numbers_when_llm_proposes_nothing():
    """Regression/sanity guard for compare_calibration_with_and_without_llm_evidence
    itself: with zero LLM records, "mixed" must be numerically identical to
    "baseline", not merely close."""
    report = build_mixed_corpus(generate_fn=_no_proposal)
    comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)
    assert comparison.mixed_train_size == comparison.baseline_train_size
    assert comparison.mixed_holdout_size == comparison.baseline_holdout_size
    assert comparison.mixed_holdout_brier == comparison.baseline_holdout_brier
    assert comparison.mixed_holdout_ece == comparison.baseline_holdout_ece


def test_baseline_alone_reproduces_the_already_validated_m6_v0_2_number():
    """Anchors this new module against the number M6 v0.2 already froze in
    tests/test_m6_non_degenerate_evidence_v0_2.py -- if this drifts, the
    mixed-corpus comparison would be built on a moving baseline."""
    report = build_mixed_corpus(generate_fn=_no_proposal)
    comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)
    assert comparison.baseline_holdout_brier == 0.48125


def test_adding_llm_evidence_never_shrinks_the_training_or_holdout_set():
    report = build_mixed_corpus(generate_fn=_always_answers)
    comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)
    assert comparison.mixed_train_size >= comparison.baseline_train_size
    assert comparison.mixed_holdout_size >= comparison.baseline_holdout_size


def test_adversarial_only_report_matches_build_real_corpus_v2_directly():
    """The mixed-corpus module must not alter or filter the adversarial
    source in any way -- it only appends to it."""
    direct = build_real_corpus_v2()
    via_mixed = build_mixed_corpus(generate_fn=_no_proposal)
    assert [r.record_id for r in direct.records] == [r.record_id for r in via_mixed.adversarial_records]
