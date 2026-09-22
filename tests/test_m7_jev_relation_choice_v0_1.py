"""Permanent invariant tests for M7 -- JEV/Kev relation-choice skeleton v0.1.

Uses an injected fake `JevDecideClient` throughout -- no network call, no
dependency on the LAN sandbox host, so these run deterministically in any
environment while the Kev infrastructure on 192.168.1.11 is still being
provisioned. There is deliberately no "live demo" test in this file yet
(unlike test_m7_live_ollama_demo_v0_1.py's pattern) -- this module makes
no real network call at all, so there is nothing to demo until a real
client exists.
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from m4_cold_start_evidence_v0_1 import CHALLENGE, GROUNDED_ANALOGY, SUPPORT
import pytest

from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_GLOSSED,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_STRICT,
    JevProposal,
    WorkedExample,
    build_strict_symbol_map,
    jev_evidence_for_prediction,
    propose_relation_jev,
)

ALL_RELATIONS = ("EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE")


class _FakeClient:
    """Records the (context, choices) it was called with, and returns a
    pre-scripted (chosen, positive_prob) pair -- or None to simulate an
    unreachable/unusable response."""

    def __init__(self, result: Optional[Tuple[str, float]]):
        self.result = result
        self.last_context: Optional[str] = None
        self.last_choices: Optional[Sequence[str]] = None

    def decide(self, *, context: str, choices: Sequence[str]):
        self.last_context = context
        self.last_choices = choices
        return self.result


# ---------------------------------------------------------------------------
# 1. build_strict_symbol_map: a real, order-independent, invertible bijection.
# ---------------------------------------------------------------------------


def test_strict_symbol_map_is_deterministic_regardless_of_input_order():
    map_a = build_strict_symbol_map(["MERE_DE", "EPOUX_DE", "PERE_DE"])
    map_b = build_strict_symbol_map(["PERE_DE", "MERE_DE", "EPOUX_DE"])
    assert map_a == map_b


def test_strict_symbol_map_is_a_bijection_over_opaque_tokens():
    symbol_map = build_strict_symbol_map(ALL_RELATIONS)
    assert len(symbol_map) == len(ALL_RELATIONS)
    assert len(set(symbol_map.values())) == len(ALL_RELATIONS)
    assert all(symbol.startswith("R") for symbol in symbol_map.values())
    # never leaks the real name into the symbol itself
    for real, symbol in symbol_map.items():
        assert real not in symbol


def test_strict_symbol_map_rejects_empty_or_duplicate_vocabulary():
    with pytest.raises(ValueError):
        build_strict_symbol_map([])
    with pytest.raises(ValueError):
        build_strict_symbol_map(["MERE_DE", "MERE_DE"])


# ---------------------------------------------------------------------------
# 2. STRICT mode: the constructed context never leaks a real relation name.
# ---------------------------------------------------------------------------


def test_strict_mode_requires_at_least_one_worked_example():
    """An opaque symbol carries no information on its own -- silently
    falling back to an unlabeled request would defeat the whole point of
    the STRICT condition, so this must raise, never proceed."""
    client = _FakeClient(("R1", 0.9))
    with pytest.raises(ValueError):
        propose_relation_jev(
            text="Alice est la mère de Bob.",
            subject="Alice",
            obj="Bob",
            all_relations=ALL_RELATIONS,
            semantic_condition=RELATION_VOCABULARY_MODE_STRICT,
            client=client,
            worked_examples=(),
        )


def test_strict_mode_context_never_contains_any_real_relation_name():
    """The core opacity property this module exists to guarantee --
    checked by direct inspection of the constructed context string, the
    same discipline already used for P4-T's freeze() opacity tests."""
    client = _FakeClient(("R3", 0.87))
    examples = (
        WorkedExample("Claire est la mère de Denis.", "MERE_DE"),
        WorkedExample("Eve est la mère de Frank.", "MERE_DE"),
    )
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_STRICT,
        client=client,
        worked_examples=examples,
    )
    assert proposal is not None
    for real_name in ALL_RELATIONS:
        assert real_name not in client.last_context
    for choice in client.last_choices:
        assert choice not in ALL_RELATIONS
        assert choice.startswith("R")


def test_strict_mode_resolves_the_chosen_symbol_back_to_the_real_relation():
    client = _FakeClient(("R3", 0.87))  # R3 = MERE_DE (3rd alphabetically among ALL_RELATIONS)
    examples = (WorkedExample("Claire est la mère de Denis.", "MERE_DE"),)
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_STRICT,
        client=client,
        worked_examples=examples,
    )
    assert proposal is not None
    assert proposal.relation == "MERE_DE"
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_STRICT
    assert proposal.positive_prob == 0.87


# ---------------------------------------------------------------------------
# 3. LABELED mode: the real names ARE presented (matches the already-
#    measured Jev benchmark, reclassified as this tier).
# ---------------------------------------------------------------------------


def test_labeled_mode_exposes_the_real_relation_names_via_choices():
    """The real vocabulary reaches the model through the typed `choices`
    parameter (mirroring the real Jev API's own `Choice` type, P8 doc
    Sec. 3), not necessarily through the free-text context -- this is
    exactly what distinguishes LABELED from STRICT: in STRICT, `choices`
    itself is opaque symbols (see the test above); in LABELED, it is the
    real names."""
    client = _FakeClient(("MERE_DE", 0.95))
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is not None
    assert set(client.last_choices) == set(ALL_RELATIONS)
    assert proposal.relation == "MERE_DE"
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_LABELED


# ---------------------------------------------------------------------------
# 4. GLOSSED mode: requires a definition for every relation, none omitted.
# ---------------------------------------------------------------------------


def test_glossed_mode_requires_a_definition_for_every_relation():
    client = _FakeClient(("MERE_DE", 0.95))
    incomplete_glosses = {"MERE_DE": "X est la mère de Y"}  # missing the other 3
    with pytest.raises(ValueError):
        propose_relation_jev(
            text="Alice est la mère de Bob.",
            subject="Alice",
            obj="Bob",
            all_relations=ALL_RELATIONS,
            semantic_condition=RELATION_VOCABULARY_MODE_GLOSSED,
            client=client,
            glosses=incomplete_glosses,
        )


def test_glossed_mode_context_contains_the_supplied_definitions():
    client = _FakeClient(("MERE_DE", 0.95))
    glosses = {r: f"définition de {r}" for r in ALL_RELATIONS}
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_GLOSSED,
        client=client,
        glosses=glosses,
    )
    assert proposal is not None
    assert "définition de MERE_DE" in client.last_context
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_GLOSSED


# ---------------------------------------------------------------------------
# 5. Guardrails carried over from the measured benchmark, unconditional.
# ---------------------------------------------------------------------------


def test_subject_equal_to_object_is_always_rejected_before_any_call():
    """Measured T05/T08/T09 self-loop bug: refused unconditionally,
    without even calling the client."""
    client = _FakeClient(("MERE_DE", 0.99))
    proposal = propose_relation_jev(
        text="Alice est la mère d'Alice.",
        subject="Alice",
        obj="Alice",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is None
    assert client.last_context is None  # never even called


def test_out_of_vocabulary_choice_is_rejected_not_coerced():
    """Measured A05 failure mode: an out-of-vocabulary answer must be
    rejected outright, never silently mapped to the nearest-looking known
    relation."""
    client = _FakeClient(("CONJOINT_DE", 0.98))  # not in ALL_RELATIONS
    proposal = propose_relation_jev(
        text="Alice est la conjointe de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is None


def test_unreachable_or_unusable_client_response_yields_no_proposal():
    client = _FakeClient(None)
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is None


def test_malformed_probability_fails_closed_rather_than_crashing_later():
    client = _FakeClient(("MERE_DE", 1.5))  # out of [0,1]
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is None


def test_unknown_semantic_condition_is_rejected():
    client = _FakeClient(("MERE_DE", 0.9))
    with pytest.raises(ValueError):
        propose_relation_jev(
            text="Alice est la mère de Bob.",
            subject="Alice",
            obj="Bob",
            all_relations=ALL_RELATIONS,
            semantic_condition="UNKNOWN_MODE",
            client=client,
        )


# ---------------------------------------------------------------------------
# 6. jev_evidence_for_prediction: always GROUNDED_ANALOGY, condition tagged.
# ---------------------------------------------------------------------------


def _proposal(relation="MERE_DE", positive_prob=0.87, semantic_condition=RELATION_VOCABULARY_MODE_STRICT):
    return JevProposal(
        subject="Alice",
        relation=relation,
        object="Bob",
        positive_prob=positive_prob,
        model="kev-4b",
        semantic_condition=semantic_condition,
        raw_response="{}",
    )


def test_evidence_is_always_grounded_analogy_never_direct():
    evidence = jev_evidence_for_prediction(
        _proposal(), candidate_id="CAND-1", predicted_relation="MERE_DE", evidence_index=0
    )
    assert evidence.provenance == GROUNDED_ANALOGY


def test_evidence_polarity_reflects_agreement_with_the_real_prediction():
    agree = jev_evidence_for_prediction(
        _proposal(relation="MERE_DE"), candidate_id="CAND-1", predicted_relation="MERE_DE", evidence_index=0
    )
    disagree = jev_evidence_for_prediction(
        _proposal(relation="PERE_DE"), candidate_id="CAND-1", predicted_relation="MERE_DE", evidence_index=1
    )
    assert agree.polarity == SUPPORT
    assert disagree.polarity == CHALLENGE


def test_evidence_confidence_uses_the_calibrated_positive_prob():
    evidence = jev_evidence_for_prediction(
        _proposal(positive_prob=0.73), candidate_id="CAND-1", predicted_relation="MERE_DE", evidence_index=0
    )
    assert evidence.confidence == 0.73


def test_evidence_metadata_carries_the_semantic_condition():
    """The governance rule's required field: every evidence record from an
    external model must declare which semantic condition produced it."""
    evidence = jev_evidence_for_prediction(
        _proposal(semantic_condition=RELATION_VOCABULARY_MODE_LABELED),
        candidate_id="CAND-1",
        predicted_relation="MERE_DE",
        evidence_index=0,
    )
    assert evidence.metadata["semantic_condition"] == RELATION_VOCABULARY_MODE_LABELED
