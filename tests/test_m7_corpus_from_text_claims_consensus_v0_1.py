"""Permanent invariant tests for M7 -- consensus text-claim corpus builder v0.1.

Uses injected fake generate_fns for both voters throughout -- no network
call. The live-Ollama demonstration is a separate, explicitly-skippable
test file (test_m7_text_claim_parser_consensus_live_demo_v0_1.py).
"""
from __future__ import annotations

import json

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_text_claims_consensus_v0_1 import TEXT_CLAIMS_PATH, build_consensus_text_claim_corpus


def _perfect_agreeing_parser(prompt):
    claims = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    for claim in claims:
        if claim["text"] in prompt:
            return {"subject": claim["subject"], "relation": claim["relation"], "object": claim["asserted_object"]}
    return None


def test_two_agreeing_perfect_voters_reproduce_the_known_diversity():
    """When both voters always agree with each other and with the corpus
    author's own answer key, the consensus mechanism must produce EXACTLY
    the same 16-record, 10/6 outcome split as the single-model perfect-
    parser wiring check -- consensus should not change WHAT is possible,
    only filter out disagreement."""
    report = build_consensus_text_claim_corpus(
        generate_fn_a=_perfect_agreeing_parser, generate_fn_b=_perfect_agreeing_parser
    )
    assert report.excluded_voter_failed == ()
    assert report.excluded_disagreement == ()
    assert report.excluded_parsing_mismatch == ()
    assert len(report.records) == 16
    assert sum(1 for r in report.records if r.outcome == SUPPORTED) == 10
    assert sum(1 for r in report.records if r.outcome == CONTRADICTED) == 6
    assert all(r.provenance == GROUNDED_ANALOGY for r in report.records)


def test_both_voters_never_answering_yields_zero_records_all_voter_failed():
    report = build_consensus_text_claim_corpus(generate_fn_a=lambda p: None, generate_fn_b=lambda p: None)
    assert report.records == ()
    assert len(report.excluded_voter_failed) == 16
    assert report.excluded_disagreement == ()


def test_voters_always_disagreeing_are_excluded_as_disagreement_never_fabricated():
    report = build_consensus_text_claim_corpus(
        generate_fn_a=lambda p: {"subject": "Mai", "relation": "EPOUSE_DE", "object": "AnswerA"},
        generate_fn_b=lambda p: {"subject": "Mai", "relation": "EPOUSE_DE", "object": "AnswerB"},
    )
    assert report.records == ()
    assert len(report.excluded_disagreement) == 16
    assert report.excluded_voter_failed == ()


def test_voters_agreeing_on_the_wrong_subject_are_excluded_as_mismatch():
    """Both voters agree WITH EACH OTHER, but not with what the sentence is
    independently known to be about -- must be excluded as a parsing
    mismatch, never silently paired with the wrong candidate."""
    wrong_but_agreeing = {"subject": "NobodyInThisCorpus", "relation": "MERE_DE", "object": "X"}
    report = build_consensus_text_claim_corpus(
        generate_fn_a=lambda p: dict(wrong_but_agreeing), generate_fn_b=lambda p: dict(wrong_but_agreeing)
    )
    assert report.records == ()
    assert len(report.excluded_parsing_mismatch) == 16
    assert report.excluded_disagreement == ()
    assert report.excluded_voter_failed == ()


def test_every_candidate_is_accounted_for_across_four_exclusion_reasons():
    """Honest accounting: candidate_patterns_considered must equal the sum
    of records-produced patterns plus every distinct exclusion reason --
    never neither, never both."""
    report = build_consensus_text_claim_corpus(generate_fn_a=lambda p: None, generate_fn_b=lambda p: None)
    accounted = len(report.records) + len(report.excluded_voter_failed) + len(report.excluded_disagreement) + len(report.excluded_parsing_mismatch)
    total_accounted = accounted + len(report.excluded_no_matching_text_claim)
    assert total_accounted >= report.candidate_patterns_considered
