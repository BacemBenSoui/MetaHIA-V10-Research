"""Permanent invariant tests for M7 -- free-text claim parser v0.1.

Uses an injected fake `generate_fn` throughout -- no network call, no
dependency on a running Ollama instance, matching the discipline already
established for m7_llm_fact_proposer_v0_1.py and m7_corpus_mixed_v0_1.py.
The live-Ollama demonstration is a separate, explicitly-skippable test file
(test_m7_text_claim_parser_live_demo_v0_1.py).
"""
from __future__ import annotations

import json

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_text_claims_v0_1 import TEXT_CLAIMS_PATH, build_text_claim_corpus
from m7_text_claim_parser_v0_1 import ParsedClaim, parse_claim_from_text

ALLOWED = ("MERE_DE", "PERE_DE", "ENFANT_DE", "FILS_DE", "FILLE_DE", "FRERE_DE", "SOEUR_DE", "EPOUSE_DE", "EPOUX_DE")


# ---------------------------------------------------------------------------
# 1. Fail-closed parsing: malformed output is never fabricated into a claim.
# ---------------------------------------------------------------------------

def test_none_response_is_no_claim():
    result = parse_claim_from_text("Mai est l'épouse de Hoang.", allowed_relations=ALLOWED, generate_fn=lambda p: None)
    assert result is None


def test_non_dict_response_is_no_claim():
    result = parse_claim_from_text("Mai est l'épouse de Hoang.", allowed_relations=ALLOWED, generate_fn=lambda p: "not a dict")
    assert result is None


def test_missing_field_is_no_claim():
    for raw in [{"subject": "Mai", "relation": "EPOUSE_DE"}, {"relation": "EPOUSE_DE", "object": "Hoang"}, {}]:
        result = parse_claim_from_text("txt", allowed_relations=ALLOWED, generate_fn=lambda p, r=raw: r)
        assert result is None


def test_non_string_or_empty_fields_are_no_claim():
    bad = [
        {"subject": 42, "relation": "EPOUSE_DE", "object": "Hoang"},
        {"subject": "Mai", "relation": "EPOUSE_DE", "object": "   "},
        {"subject": "  ", "relation": "EPOUSE_DE", "object": "Hoang"},
    ]
    for raw in bad:
        result = parse_claim_from_text("txt", allowed_relations=ALLOWED, generate_fn=lambda p, r=raw: r)
        assert result is None


# ---------------------------------------------------------------------------
# 2. Fail-closed vocabulary: a relation outside the closed set is rejected,
# never coerced into the closest-looking known relation.
# ---------------------------------------------------------------------------

def test_relation_outside_closed_vocabulary_is_no_claim():
    result = parse_claim_from_text(
        "Mai est l'amie de Hoang.", allowed_relations=ALLOWED,
        generate_fn=lambda p: {"subject": "Mai", "relation": "AMIE_DE", "object": "Hoang"},
    )
    assert result is None


# ---------------------------------------------------------------------------
# 3. A well-formed, in-vocabulary claim is accepted.
# ---------------------------------------------------------------------------

def test_well_formed_claim_is_accepted():
    result = parse_claim_from_text(
        "Mai est l'épouse de Hoang.", allowed_relations=ALLOWED,
        generate_fn=lambda p: {"subject": " Mai ", "relation": " EPOUSE_DE ", "object": " Hoang "},
    )
    assert result == ParsedClaim(subject="Mai", relation="EPOUSE_DE", object="Hoang", model=result.model, raw_response=result.raw_response)


def test_prompt_includes_the_sentence_and_the_allowed_relations():
    captured = {}

    def capturing(prompt):
        captured["prompt"] = prompt
        return None

    parse_claim_from_text("Mai est l'épouse de Hoang.", allowed_relations=ALLOWED, generate_fn=capturing)
    assert "Mai est l'épouse de Hoang." in captured["prompt"]
    for rel in ALLOWED:
        assert rel in captured["prompt"]


# ---------------------------------------------------------------------------
# 4. Corpus builder: three honestly distinct exclusion reasons, never merged
# and never silently dropped.
# ---------------------------------------------------------------------------

def test_no_parse_ever_produced_when_llm_proposes_nothing():
    report = build_text_claim_corpus(generate_fn=lambda p: None)
    assert report.records == ()
    assert len(report.excluded_no_parse) == 16  # the 16 real length-1 candidates all have a matching text claim


def test_parsing_mismatch_is_excluded_never_paired_with_the_wrong_candidate():
    """A fake LLM that always names a DIFFERENT subject than what any
    sentence is actually about must never be silently paired with a
    candidate it doesn't match."""
    report = build_text_claim_corpus(
        generate_fn=lambda p: {"subject": "NobodyInThisCorpus", "relation": "MERE_DE", "object": "X"}
    )
    assert report.records == ()
    assert len(report.excluded_parsing_mismatch) == 16
    assert report.excluded_no_parse == ()


def test_perfect_parser_reproduces_the_corpus_authors_intended_diversity():
    """A fake generate_fn that echoes back the CORRECT (subject, relation,
    asserted_object) for whichever sentence appears in the prompt --
    simulating perfect extraction -- must reproduce exactly the outcome
    diversity the text-claims corpus was authored to contain (10 agreeing,
    6 deliberately wrong), independent of any real model's actual accuracy.
    This is an infrastructure/wiring check, not an LLM accuracy claim."""
    claims = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    by_text = {c["text"]: c for c in claims}

    def perfect_parser(prompt):
        for text, claim in by_text.items():
            if text in prompt:
                return {"subject": claim["subject"], "relation": claim["relation"], "object": claim["asserted_object"]}
        return None

    report = build_text_claim_corpus(generate_fn=perfect_parser)
    assert report.excluded_no_parse == ()
    assert report.excluded_parsing_mismatch == ()
    assert len(report.records) == 16
    assert sum(1 for r in report.records if r.outcome == SUPPORTED) == 10
    assert sum(1 for r in report.records if r.outcome == CONTRADICTED) == 6
    assert all(r.provenance == GROUNDED_ANALOGY for r in report.records)


def test_candidate_patterns_considered_matches_the_sibling_llm_mechanism():
    """Same corpus, same length-1 scoping as m7_corpus_from_llm_v0_1.py --
    the candidate count must match exactly."""
    from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus

    text_report = build_text_claim_corpus(generate_fn=lambda p: None)
    llm_report = build_llm_witnessed_corpus(generate_fn=lambda p: None)
    assert text_report.candidate_patterns_considered == llm_report.candidate_patterns_considered
