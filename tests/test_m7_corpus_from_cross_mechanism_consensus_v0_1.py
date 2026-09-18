"""Permanent invariant tests for M7 -- cross-mechanism consensus corpus
builder v0.1. Uses injected fake generate_fns for both mechanisms
throughout -- no network call. The live-Ollama demonstration is a separate,
explicitly-skippable test file
(test_m7_cross_mechanism_consensus_live_demo_v0_1.py).
"""
from __future__ import annotations

import json

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_cross_mechanism_consensus_v0_1 import TEXT_CLAIMS_PATH, build_cross_mechanism_corpus


def _perfect_fakes():
    claims = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    by_subject_relation = {(c["subject"], c["relation"]): c for c in claims}

    def perfect_witness(prompt):
        for (subj, rel), c in by_subject_relation.items():
            if f'{rel}("{subj}", ?)' in prompt:
                return {"object": c["asserted_object"]}
        return None

    def perfect_parser(prompt):
        for (subj, rel), c in by_subject_relation.items():
            if c["text"] in prompt:
                return {"subject": subj, "relation": rel, "object": c["asserted_object"]}
        return None

    return perfect_witness, perfect_parser


def test_both_mechanisms_perfectly_agreeing_reproduce_the_known_diversity():
    perfect_witness, perfect_parser = _perfect_fakes()
    report = build_cross_mechanism_corpus(witness_generate_fn=perfect_witness, parser_generate_fn=perfect_parser)
    assert report.excluded_mechanism_failed == ()
    assert report.excluded_disagreement == ()
    assert report.excluded_parsing_mismatch == ()
    assert len(report.records) == 16
    assert sum(1 for r in report.records if r.outcome == SUPPORTED) == 10
    assert sum(1 for r in report.records if r.outcome == CONTRADICTED) == 6
    assert all(r.provenance == GROUNDED_ANALOGY for r in report.records)


def test_both_mechanisms_never_answering_yields_zero_records_all_mechanism_failed():
    report = build_cross_mechanism_corpus(witness_generate_fn=lambda p: None, parser_generate_fn=lambda p: None)
    assert report.records == ()
    assert len(report.excluded_mechanism_failed) == 16
    assert report.excluded_disagreement == ()
    assert report.excluded_parsing_mismatch == ()


def test_only_witness_answering_is_still_mechanism_failed_not_disagreement():
    report = build_cross_mechanism_corpus(witness_generate_fn=lambda p: {"object": "X"}, parser_generate_fn=lambda p: None)
    assert report.records == ()
    assert len(report.excluded_mechanism_failed) == 16
    assert report.excluded_disagreement == ()


def test_disagreeing_mechanisms_are_excluded_never_fabricated():
    _perfect_witness, perfect_parser = _perfect_fakes()
    report = build_cross_mechanism_corpus(
        witness_generate_fn=lambda p: {"object": "AlwaysDifferentAnswer"}, parser_generate_fn=perfect_parser
    )
    assert report.records == ()
    assert len(report.excluded_disagreement) == 16
    assert report.excluded_mechanism_failed == ()


def test_parser_mismatch_is_excluded_never_paired_with_wrong_candidate():
    perfect_witness, _perfect_parser = _perfect_fakes()
    report = build_cross_mechanism_corpus(
        witness_generate_fn=perfect_witness,
        parser_generate_fn=lambda p: {"subject": "NobodyInThisCorpus", "relation": "MERE_DE", "object": "X"},
    )
    assert report.records == ()
    assert len(report.excluded_parsing_mismatch) == 16
    assert report.excluded_disagreement == ()


def test_candidate_count_matches_the_sibling_mechanisms():
    from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus
    from m7_corpus_from_text_claims_v0_1 import build_text_claim_corpus

    cross_report = build_cross_mechanism_corpus(witness_generate_fn=lambda p: None, parser_generate_fn=lambda p: None)
    text_report = build_text_claim_corpus(generate_fn=lambda p: None)
    llm_report = build_llm_witnessed_corpus(generate_fn=lambda p: None)
    assert cross_report.candidate_patterns_considered == text_report.candidate_patterns_considered == llm_report.candidate_patterns_considered == 14
