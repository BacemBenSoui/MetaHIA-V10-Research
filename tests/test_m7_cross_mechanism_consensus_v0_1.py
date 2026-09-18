"""Permanent invariant tests for M7 -- cross-mechanism consensus v0.1
(closed-question witness + free-text claim parser must agree).

Uses injected fake generate_fns for both mechanisms throughout -- no
network call. The live-Ollama demonstration is a separate, explicitly-
skippable test file (test_m7_cross_mechanism_consensus_live_demo_v0_1.py).
"""
from __future__ import annotations

from m7_cross_mechanism_consensus_v0_1 import (
    REASON_AGREED,
    REASON_BOTH_FAILED,
    REASON_DISAGREEMENT,
    REASON_PARSER_FAILED,
    REASON_PARSER_MISMATCH,
    REASON_WITNESS_FAILED,
    evaluate_cross_mechanism_consensus,
)

KNOWN_FACTS = [("MERE_DE", "Amanda", "David"), ("MERE_DE", "Amanda", "Alice")]
ALLOWED = ("MERE_DE", "PERE_DE", "ENFANT_DE", "FILS_DE", "FILLE_DE", "FRERE_DE", "SOEUR_DE", "EPOUSE_DE", "EPOUX_DE")


def _kwargs(witness_fn, parser_fn):
    return dict(
        known_facts=KNOWN_FACTS, subject="Alice", relation="MERE_DE", text="Alice est la mère de Hugo.",
        allowed_relations=ALLOWED, witness_generate_fn=witness_fn, parser_generate_fn=parser_fn,
    )


def test_both_mechanisms_agreeing_yields_a_consensus_claim():
    result = evaluate_cross_mechanism_consensus(**_kwargs(
        lambda p: {"object": "Hugo"},
        lambda p: {"subject": "Alice", "relation": "MERE_DE", "object": "Hugo"},
    ))
    assert result.reason == REASON_AGREED
    assert result.claim.object == "Hugo"


def test_disagreement_on_object_is_excluded_never_arbitrarily_resolved():
    result = evaluate_cross_mechanism_consensus(**_kwargs(
        lambda p: {"object": "Hugo"},
        lambda p: {"subject": "Alice", "relation": "MERE_DE", "object": "SomeoneElse"},
    ))
    assert result.reason == REASON_DISAGREEMENT
    assert result.claim is None


def test_witness_failing_is_distinguished_from_disagreement():
    result = evaluate_cross_mechanism_consensus(**_kwargs(
        lambda p: None,
        lambda p: {"subject": "Alice", "relation": "MERE_DE", "object": "Hugo"},
    ))
    assert result.reason == REASON_WITNESS_FAILED


def test_parser_failing_is_distinguished_from_disagreement():
    result = evaluate_cross_mechanism_consensus(**_kwargs(
        lambda p: {"object": "Hugo"},
        lambda p: None,
    ))
    assert result.reason == REASON_PARSER_FAILED


def test_both_failing_is_its_own_reason():
    result = evaluate_cross_mechanism_consensus(**_kwargs(lambda p: None, lambda p: None))
    assert result.reason == REASON_BOTH_FAILED


def test_parser_mismatch_is_distinguished_from_disagreement():
    """The parser extracted a well-formed claim, but about a different
    subject than the sentence is independently known to be about -- must
    never be silently compared to the witness as if it were about the
    right candidate."""
    result = evaluate_cross_mechanism_consensus(**_kwargs(
        lambda p: {"object": "Hugo"},
        lambda p: {"subject": "NobodyInThisCorpus", "relation": "MERE_DE", "object": "Hugo"},
    ))
    assert result.reason == REASON_PARSER_MISMATCH
