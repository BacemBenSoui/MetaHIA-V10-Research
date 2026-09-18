"""M7 free-text claim parser -- Critical Validation v0.1.

Third-party validation suite for
MetaHIA_ThirdParty_Validation_Protocol_M7_TextClaimParser_V0_1.md. Cases
C01-C09 map 1:1 to that protocol's critical contract. Self-contained: does
not import from the other M7 test files, does not modify any frozen module.

Deliberately network-free: every case uses an injected fake `generate_fn`,
never a real Ollama call, so this suite runs identically whether or not the
evaluator has Ollama installed. The real, non-reproducible live-LLM result
(50% parsing fidelity, 5 SUPPORTED / 2 CONTRADICTED) is reported as an
already-disclosed empirical finding in the protocol document, not asserted
here.
"""
from __future__ import annotations

import json

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_text_claims_v0_1 import TEXT_CLAIMS_PATH, build_text_claim_corpus
from m7_text_claim_parser_v0_1 import ParsedClaim, parse_claim_from_text

ALLOWED = ("MERE_DE", "PERE_DE", "ENFANT_DE", "FILS_DE", "FILLE_DE", "FRERE_DE", "SOEUR_DE", "EPOUSE_DE", "EPOUX_DE")


# ---------------------------------------------------------------------------
# C01 -- Fail-closed parsing: malformed/missing/non-string/empty fields never
# fabricated into a claim.
# ---------------------------------------------------------------------------

def test_c01_malformed_responses_are_never_fabricated_into_a_claim():
    malformed = [
        None, "not a dict", {}, {"subject": "Mai", "relation": "EPOUSE_DE"},
        {"subject": 42, "relation": "EPOUSE_DE", "object": "Hoang"},
        {"subject": "Mai", "relation": "EPOUSE_DE", "object": "   "},
    ]
    for raw in malformed:
        result = parse_claim_from_text("txt", allowed_relations=ALLOWED, generate_fn=lambda p, r=raw: r)
        assert result is None, f"malformed response {raw!r} must yield no claim"


# ---------------------------------------------------------------------------
# C02 -- Fail-closed vocabulary: a relation outside the closed set is
# rejected, never coerced into the closest-looking known relation.
# ---------------------------------------------------------------------------

def test_c02_relation_outside_closed_vocabulary_is_rejected():
    result = parse_claim_from_text(
        "Mai est l'amie de Hoang.", allowed_relations=ALLOWED,
        generate_fn=lambda p: {"subject": "Mai", "relation": "AMIE_DE", "object": "Hoang"},
    )
    assert result is None


# ---------------------------------------------------------------------------
# C03 -- A well-formed, in-vocabulary claim is accepted.
# ---------------------------------------------------------------------------

def test_c03_well_formed_in_vocabulary_claim_is_accepted():
    result = parse_claim_from_text(
        "Mai est l'épouse de Hoang.", allowed_relations=ALLOWED,
        generate_fn=lambda p: {"subject": " Mai ", "relation": " EPOUSE_DE ", "object": " Hoang "},
    )
    assert result == ParsedClaim(subject="Mai", relation="EPOUSE_DE", object="Hoang", model=result.model, raw_response=result.raw_response)


# ---------------------------------------------------------------------------
# C04 -- The prompt actually presents the sentence and the FULL closed
# vocabulary to the model (the fail-closed contract only means something if
# the model is genuinely told the constraint).
# ---------------------------------------------------------------------------

def test_c04_prompt_contains_the_sentence_and_every_allowed_relation():
    captured = {}

    def capturing(prompt):
        captured["prompt"] = prompt
        return None

    parse_claim_from_text("Mai est l'épouse de Hoang.", allowed_relations=ALLOWED, generate_fn=capturing)
    assert "Mai est l'épouse de Hoang." in captured["prompt"]
    for rel in ALLOWED:
        assert rel in captured["prompt"]


# ---------------------------------------------------------------------------
# C05 -- A well-formed but MISMATCHED extraction (wrong subject/relation for
# what this sentence is independently known to be about) is excluded, never
# silently paired with the wrong candidate.
# ---------------------------------------------------------------------------

def test_c05_parsing_mismatch_is_excluded_never_paired_with_wrong_candidate():
    report = build_text_claim_corpus(
        generate_fn=lambda p: {"subject": "NobodyInThisCorpus", "relation": "MERE_DE", "object": "X"}
    )
    assert report.records == ()
    assert len(report.excluded_parsing_mismatch) == 16
    assert report.excluded_no_parse == ()


# ---------------------------------------------------------------------------
# C06 -- Honest, mutually exclusive exclusion accounting: a non-answering
# model yields zero records, all candidates accounted for as no-parse.
# ---------------------------------------------------------------------------

def test_c06_non_answering_model_yields_zero_records_all_accounted_as_no_parse():
    report = build_text_claim_corpus(generate_fn=lambda p: None)
    assert report.records == ()
    assert len(report.excluded_no_parse) == 16
    assert report.excluded_parsing_mismatch == ()


# ---------------------------------------------------------------------------
# C07 -- Non-circularity: asserted_object (the corpus author's own answer
# key) is never read by the evidence-building code path.
# ---------------------------------------------------------------------------

def test_c07_asserted_object_never_influences_the_evidence_mechanism():
    """A generate_fn that never sees asserted_object (only ever sees the
    prompt, which does not contain it -- see the sibling non-leakage
    property in m7_llm_fact_proposer_v0_1.py) and always answers with an
    object that DISAGREES with the true asserted_object for every claim must
    still be handled exactly like any other consistent extraction -- SUPPORT
    or CHALLENGE decided purely by comparison to the real kernel prediction,
    never by whether it matches asserted_object."""
    claims = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    by_text = {c["text"]: c for c in claims}

    def always_wrong_object(prompt):
        for text, claim in by_text.items():
            if text in prompt:
                return {"subject": claim["subject"], "relation": claim["relation"], "object": "Deliberately_Wrong_Answer"}
        return None

    report = build_text_claim_corpus(generate_fn=always_wrong_object)
    assert report.excluded_parsing_mismatch == ()
    assert len(report.records) == 16
    # every record must be CONTRADICTED (the fabricated object never equals
    # a real predicted_object) -- proves outcome is computed from the real
    # kernel prediction, not from asserted_object
    assert all(r.outcome == CONTRADICTED for r in report.records)


# ---------------------------------------------------------------------------
# C08 -- Wiring correctness: a perfect parser reproduces exactly the outcome
# diversity the corpus was authored to contain (10 agreeing, 6 deliberately
# wrong) -- an infrastructure check, not an LLM accuracy claim.
# ---------------------------------------------------------------------------

def test_c08_perfect_parser_reproduces_the_corpus_authors_intended_diversity():
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


# ---------------------------------------------------------------------------
# C09 -- Cross-mechanism consistency: same corpus, same length-1 scope as the
# sibling closed-question mechanism -- the candidate count must match.
# ---------------------------------------------------------------------------

def test_c09_candidate_count_matches_the_sibling_llm_mechanism():
    from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus

    text_report = build_text_claim_corpus(generate_fn=lambda p: None)
    llm_report = build_llm_witnessed_corpus(generate_fn=lambda p: None)
    assert text_report.candidate_patterns_considered == llm_report.candidate_patterns_considered
    assert text_report.candidate_patterns_considered == 14
