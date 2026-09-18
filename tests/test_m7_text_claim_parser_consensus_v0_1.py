"""Permanent invariant tests for M7 -- free-text claim parser consensus v0.1.

Uses injected fake generate_fns for both voters throughout -- no network
call. The live-Ollama demonstration (real local + LAN voters) is a separate,
explicitly-skippable test file
(test_m7_text_claim_parser_consensus_live_demo_v0_1.py).
"""
from __future__ import annotations

from m7_text_claim_parser_consensus_v0_1 import (
    REASON_AGREED,
    REASON_BOTH_VOTERS_FAILED,
    REASON_DISAGREEMENT,
    REASON_VOTER_A_FAILED,
    REASON_VOTER_B_FAILED,
    parse_claim_from_text_with_consensus,
)

ALLOWED = ("MERE_DE", "PERE_DE", "ENFANT_DE", "FILS_DE", "FILLE_DE", "FRERE_DE", "SOEUR_DE", "EPOUSE_DE", "EPOUX_DE")

AGREEING = {"subject": "Mai", "relation": "EPOUSE_DE", "object": "Hoang"}
DIFFERENT_OBJECT = {"subject": "Mai", "relation": "EPOUSE_DE", "object": "SomeoneElse"}


def test_both_voters_agreeing_yields_a_consensus_claim():
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: dict(AGREEING), generate_fn_b=lambda p: dict(AGREEING),
    )
    assert result.reason == REASON_AGREED
    assert result.claim.subject == "Mai"
    assert result.claim.relation == "EPOUSE_DE"
    assert result.claim.object == "Hoang"


def test_disagreeing_voters_yield_no_claim_never_arbitrarily_resolved():
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: dict(AGREEING), generate_fn_b=lambda p: dict(DIFFERENT_OBJECT),
    )
    assert result.reason == REASON_DISAGREEMENT
    assert result.claim is None


def test_voter_a_failing_is_distinguished_from_disagreement():
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: None, generate_fn_b=lambda p: dict(AGREEING),
    )
    assert result.reason == REASON_VOTER_A_FAILED
    assert result.claim is None


def test_voter_b_failing_is_distinguished_from_disagreement():
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: dict(AGREEING), generate_fn_b=lambda p: None,
    )
    assert result.reason == REASON_VOTER_B_FAILED
    assert result.claim is None


def test_both_voters_failing_is_its_own_reason():
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: None, generate_fn_b=lambda p: None,
    )
    assert result.reason == REASON_BOTH_VOTERS_FAILED
    assert result.claim is None


def test_a_voter_naming_a_relation_outside_the_closed_vocabulary_fails_closed():
    """Each voter still enforces parse_claim_from_text's own fail-closed
    vocabulary contract, unchanged -- consensus adds a second check on top,
    it does not weaken the first."""
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: {"subject": "Mai", "relation": "AMIE_DE", "object": "Hoang"},
        generate_fn_b=lambda p: dict(AGREEING),
    )
    assert result.reason == REASON_VOTER_A_FAILED
    assert result.claim is None


def test_consensus_claim_records_both_models_that_agreed():
    result = parse_claim_from_text_with_consensus(
        "txt", allowed_relations=ALLOWED,
        generate_fn_a=lambda p: dict(AGREEING), generate_fn_b=lambda p: dict(AGREEING),
    )
    assert len(result.claim.models) == 2
