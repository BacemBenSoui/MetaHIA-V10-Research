"""M7 -- mixed-corpus promotion integration v0.2 tests (three sources).

Uses injected fake generate_fns throughout (no network) to test the
MECHANICS of combining three evidence sources: fairness of the rule-set
superset property across all combinations, correct degeneration to fewer
sources when a mechanism proposes nothing, and non-regression of the
already-validated baseline. The REAL, non-deterministic four-way comparison
(actual Ollama calls) is not pinned here -- see
tests/test_m7_mixed_corpus_v0_2_live_demo_v0_1.py (skippable) and
MetaHIA_M7_TextClaimParser_V0_1.md Sec.10 for the real observed numbers.
"""
from __future__ import annotations

import json

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m7_corpus_from_text_claims_v0_1 import TEXT_CLAIMS_PATH
from m7_corpus_mixed_v0_2 import build_mixed_corpus_v2, compare_calibration_across_sources


def _no_proposal(prompt: str):
    return None


def _text_perfect_parser(prompt: str):
    claims = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    for claim in claims:
        if claim["text"] in prompt:
            return {"subject": claim["subject"], "relation": claim["relation"], "object": claim["asserted_object"]}
    return None


def test_no_llm_evidence_at_all_degenerates_every_condition_to_baseline():
    report = build_mixed_corpus_v2(llm_generate_fn=_no_proposal, text_generate_fn=_no_proposal)
    assert report.llm_records == ()
    assert report.text_claim_records == ()
    comparison = compare_calibration_across_sources(report, seed=0, brier_threshold=0.5)
    for condition in (comparison.with_witness, comparison.with_text_claims, comparison.with_both):
        assert condition.train_size == comparison.baseline.train_size
        assert condition.holdout_size == comparison.baseline.holdout_size
        assert condition.holdout_brier == comparison.baseline.holdout_brier
        assert condition.holdout_ece == comparison.baseline.holdout_ece


def test_baseline_reproduces_the_already_validated_m6_v0_2_number():
    report = build_mixed_corpus_v2(llm_generate_fn=_no_proposal, text_generate_fn=_no_proposal)
    comparison = compare_calibration_across_sources(report, seed=0, brier_threshold=0.5)
    assert comparison.baseline.holdout_brier == 0.48125
    direct = build_real_corpus_v2()
    assert [r.record_id for r in direct.records] == [r.record_id for r in report.adversarial_records]


def test_neither_llm_source_ever_introduces_a_rule_absent_from_the_adversarial_corpus():
    """Fairness property this module's four-way comparison relies on: no
    combination of sources may expand the rule-signature set beyond what the
    adversarial corpus alone already contains, regardless of what either
    fake LLM answers -- otherwise split_by_rule could assign a different
    holdout rule set per condition, breaking the apples-to-apples
    comparison."""
    report = build_mixed_corpus_v2(
        llm_generate_fn=lambda p: {"object": "Placeholder"},
        text_generate_fn=_text_perfect_parser,
    )
    adversarial_rules = {r.rule_signature for r in report.adversarial_records}
    assert {r.rule_signature for r in report.combined_with_witness} == adversarial_rules
    assert {r.rule_signature for r in report.combined_with_text_claims} == adversarial_rules
    assert {r.rule_signature for r in report.combined_all} == adversarial_rules


def test_with_both_is_the_exact_union_of_all_three_sources():
    report = build_mixed_corpus_v2(
        llm_generate_fn=lambda p: {"object": "Placeholder"},
        text_generate_fn=_text_perfect_parser,
    )
    assert len(report.text_claim_records) == 16  # perfect parser -> every candidate matched
    assert len(report.combined_all) == len(report.adversarial_records) + len(report.llm_records) + len(report.text_claim_records)
    ids = {r.record_id for r in report.combined_all}
    assert ids == (
        {r.record_id for r in report.adversarial_records}
        | {r.record_id for r in report.llm_records}
        | {r.record_id for r in report.text_claim_records}
    )


def test_adding_more_sources_never_shrinks_train_or_holdout():
    report = build_mixed_corpus_v2(
        llm_generate_fn=lambda p: {"object": "Placeholder"},
        text_generate_fn=_text_perfect_parser,
    )
    comparison = compare_calibration_across_sources(report, seed=0, brier_threshold=0.5)
    for condition in (comparison.with_witness, comparison.with_text_claims, comparison.with_both):
        assert condition.train_size >= comparison.baseline.train_size
        assert condition.holdout_size >= comparison.baseline.holdout_size
    assert comparison.with_both.train_size >= comparison.with_witness.train_size
    assert comparison.with_both.train_size >= comparison.with_text_claims.train_size


def test_perfect_text_parser_alone_reproduces_its_own_known_diversity():
    """Anchors the 'with_text_claims' condition's input against the already
    -verified perfect-parser wiring check from
    test_m7_text_claim_parser_v0_1.py: 16 records, 10 SUPPORTED / 6
    CONTRADICTED, when the LLM witness contributes nothing."""
    from m4_cold_start_evidence_v0_1 import CONTRADICTED, SUPPORTED

    report = build_mixed_corpus_v2(llm_generate_fn=_no_proposal, text_generate_fn=_text_perfect_parser)
    assert len(report.text_claim_records) == 16
    assert sum(1 for r in report.text_claim_records if r.outcome == SUPPORTED) == 10
    assert sum(1 for r in report.text_claim_records if r.outcome == CONTRADICTED) == 6
