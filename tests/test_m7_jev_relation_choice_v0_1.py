"""Permanent invariant tests for M7 -- JEV/Kev relation-choice v0.1.

Uses an injected fake `JevDecideClient` throughout -- no network call, no
dependency on the LAN sandbox host, so these run deterministically in any
environment. The fake client's `decide(state, instructions, criteria)`
signature matches the VERIFIED real `jaredpalmer/kev` `POST /v1/systemone`
`choice`-question contract (read directly from its README/source,
2026-09-22), not a guess. A separate, genuinely network-dependent live
demo lives in test_m7_jev_live_demo_v0_1.py (skips cleanly if the Kev
server is unreachable, mirroring test_m7_live_ollama_demo_v0_1.py's own
pattern).
"""
from __future__ import annotations

from typing import Mapping, Optional, Tuple

from m4_cold_start_evidence_v0_1 import CHALLENGE, GROUNDED_ANALOGY, SUPPORT
import pytest

from m7_jev_relation_choice_v0_1 import (
    DEFAULT_LABELED_GLOSSED_INSTRUCTIONS,
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


def _dist(chosen: str, chosen_prob: float, options) -> dict:
    """A plausible full probability distribution for tests that don't
    care about its exact shape -- puts `chosen_prob` on `chosen`, spreads
    the remainder evenly across the rest."""
    others = [o for o in options if o != chosen]
    remainder = (1.0 - chosen_prob) / len(others) if others else 0.0
    return {chosen: chosen_prob, **{o: remainder for o in others}}


class _FakeClient:
    """Records the (state, instructions, criteria) it was called with, and
    returns a pre-scripted (chosen, positive_prob, probabilities) triple --
    or None to simulate an unreachable/unusable response."""

    def __init__(self, result: Optional[Tuple[str, float, Mapping[str, float]]]):
        self.result = result
        self.last_state: Optional[str] = None
        self.last_instructions: Optional[str] = None
        self.last_criteria: Optional[Mapping[str, Optional[str]]] = None

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        self.last_state = state
        self.last_instructions = instructions
        self.last_criteria = criteria
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
    client = _FakeClient(("R1", 0.9, {"R1": 0.9}))
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


def test_strict_mode_never_leaks_any_real_relation_name_anywhere():
    """The core opacity property this module exists to guarantee --
    checked by direct inspection of every field sent to the client (state,
    instructions, and criteria keys/values), the same discipline already
    used for P4-T's freeze() opacity tests. `criteria` values are all
    `None` in STRICT mode -- no description is ever given, opaque symbol
    or otherwise."""
    client = _FakeClient(("R3", 0.87, _dist("R3", 0.87, ["R1", "R2", "R3", "R4"])))
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
        assert real_name not in client.last_state
        assert real_name not in client.last_instructions
    for key, description in client.last_criteria.items():
        assert key not in ALL_RELATIONS
        assert key.startswith("R")
        assert description is None
    # the returned proposal, on the other hand, is re-keyed to real names --
    # nothing downstream of propose_relation_jev should ever need to know
    # the opaque-symbol mapping.
    assert set(proposal.probabilities.keys()) == set(ALL_RELATIONS)


def test_strict_mode_resolves_the_chosen_symbol_back_to_the_real_relation():
    client = _FakeClient(
        ("R3", 0.87, _dist("R3", 0.87, ["R1", "R2", "R3", "R4"]))
    )  # R3 = MERE_DE (3rd alphabetically among ALL_RELATIONS)
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


def test_labeled_mode_exposes_the_real_relation_names_as_criteria_keys():
    """The real vocabulary reaches the model through `criteria`'s keys
    (Kev's real `choice`-question mechanism: "you choose the id; the model
    never sees it" -- but it DOES see every criteria key), every
    description still `None` -- this is exactly what distinguishes
    LABELED from STRICT (opaque keys) and from GLOSSED (keys + text)."""
    client = _FakeClient(("MERE_DE", 0.95, _dist("MERE_DE", 0.95, ALL_RELATIONS)))
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is not None
    assert set(client.last_criteria.keys()) == set(ALL_RELATIONS)
    assert all(description is None for description in client.last_criteria.values())
    assert proposal.relation == "MERE_DE"
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_LABELED


def test_instructions_override_replaces_the_default_text_leaving_state_and_criteria_untouched():
    """P8.3b: the one remaining LABELED input not yet order/content-
    tested. `None` (the default, every other test in this file) must
    keep the exact built-in text; a non-`None` override must replace it
    exactly, without touching `state` or `criteria`."""
    client_default = _FakeClient(("MERE_DE", 0.95, _dist("MERE_DE", 0.95, ALL_RELATIONS)))
    propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client_default,
    )
    assert client_default.last_instructions == DEFAULT_LABELED_GLOSSED_INSTRUCTIONS

    client_override = _FakeClient(("MERE_DE", 0.95, _dist("MERE_DE", 0.95, ALL_RELATIONS)))
    custom_instructions = "What relationship does this sentence express?"
    propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client_override,
        instructions_override=custom_instructions,
    )
    assert client_override.last_instructions == custom_instructions
    assert client_override.last_instructions != DEFAULT_LABELED_GLOSSED_INSTRUCTIONS
    assert client_override.last_state == client_default.last_state
    assert client_override.last_criteria == client_default.last_criteria


# ---------------------------------------------------------------------------
# 4. GLOSSED mode: requires a definition for every relation, none omitted.
# ---------------------------------------------------------------------------


def test_glossed_mode_requires_a_definition_for_every_relation():
    client = _FakeClient(("MERE_DE", 0.95, _dist("MERE_DE", 0.95, ALL_RELATIONS)))
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


def test_glossed_mode_criteria_carries_the_supplied_definitions():
    client = _FakeClient(("MERE_DE", 0.95, _dist("MERE_DE", 0.95, ALL_RELATIONS)))
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
    assert client.last_criteria == glosses
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_GLOSSED


# ---------------------------------------------------------------------------
# 5. Guardrails carried over from the measured benchmark, unconditional.
# ---------------------------------------------------------------------------


def test_subject_equal_to_object_is_always_rejected_before_any_call():
    """Measured T05/T08/T09 self-loop bug: refused unconditionally,
    without even calling the client."""
    client = _FakeClient(("MERE_DE", 0.99, _dist("MERE_DE", 0.99, ALL_RELATIONS)))
    proposal = propose_relation_jev(
        text="Alice est la mère d'Alice.",
        subject="Alice",
        obj="Alice",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is None
    assert client.last_state is None  # never even called


def test_out_of_vocabulary_choice_is_rejected_not_coerced():
    """Measured A05 failure mode: an out-of-vocabulary answer must be
    rejected outright, never silently mapped to the nearest-looking known
    relation."""
    client = _FakeClient(("CONJOINT_DE", 0.98, {"CONJOINT_DE": 0.98}))  # not in ALL_RELATIONS
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
    client = _FakeClient(("MERE_DE", 1.5, _dist("MERE_DE", 0.9, ALL_RELATIONS)))  # positive_prob out of [0,1]
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=client,
    )
    assert proposal is None


def test_malformed_probability_distribution_fails_closed():
    """The distribution itself (not just the chosen option's own
    probability) is validated too -- a value out of [0,1] anywhere in it
    is a malformed response, never a usable proposal."""
    client = _FakeClient(("MERE_DE", 0.9, {"MERE_DE": 0.9, "PERE_DE": 1.4, "EPOUX_DE": 0.0, "EPOUSE_DE": 0.0}))
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
    client = _FakeClient(("MERE_DE", 0.9, _dist("MERE_DE", 0.9, ALL_RELATIONS)))
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
        probabilities=_dist(relation, positive_prob, ALL_RELATIONS),
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


def test_evidence_metadata_carries_the_full_probability_distribution():
    """Needed for real multiclass calibration (P8.1) -- positive_prob
    alone cannot reconstruct how probability was spread across the
    options that were NOT chosen."""
    proposal = _proposal(positive_prob=0.6)
    evidence = jev_evidence_for_prediction(
        proposal, candidate_id="CAND-1", predicted_relation="MERE_DE", evidence_index=0
    )
    assert evidence.metadata["probabilities"] == dict(proposal.probabilities)


# ---------------------------------------------------------------------------
# 7. JevKevSystemOneClient: real response-shape parsing, network mocked.
#
# Response shape verified directly against jaredpalmer/kev's own README
# example (2026-09-22, read via the GitHub API, not assumed):
#   {"answers": {"<id>": {"type": "choice", "choice": "...",
#                          "confidence": ..., "probabilities": {...}}}}
# ---------------------------------------------------------------------------

import json as _json  # local import, only these tests touch the network layer
from m7_jev_relation_choice_v0_1 import JevKevSystemOneClient


class _FakeHTTPResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._body = _json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_system_one_client_parses_a_real_shaped_response(monkeypatch):
    kev_response = {
        "model": "kev-latest",
        "answers": {
            "relation": {
                "type": "choice",
                "choice": "MERE_DE",
                "confidence": 0.82,
                "probabilities": {"MERE_DE": 0.91, "PERE_DE": 0.05, "EPOUX_DE": 0.02, "EPOUSE_DE": 0.02},
            }
        },
        "usage": {"input_tokens": 42, "output_tokens": 10},
        "latency_ms": 123.4,
    }
    import m7_jev_relation_choice_v0_1 as jevmod

    monkeypatch.setattr(jevmod.urllib.request, "urlopen", lambda *a, **k: _FakeHTTPResponse(kev_response))
    client = JevKevSystemOneClient("http://192.168.1.11:8009")
    result = client.decide(state="Alice est la mère de Bob.", instructions="Which relation applies?", criteria={"MERE_DE": None})
    assert result == ("MERE_DE", 0.91, {"MERE_DE": 0.91, "PERE_DE": 0.05, "EPOUX_DE": 0.02, "EPOUSE_DE": 0.02})


def test_system_one_client_fails_closed_on_missing_answer(monkeypatch):
    import m7_jev_relation_choice_v0_1 as jevmod

    monkeypatch.setattr(jevmod.urllib.request, "urlopen", lambda *a, **k: _FakeHTTPResponse({"answers": {}}))
    client = JevKevSystemOneClient("http://192.168.1.11:8009")
    result = client.decide(state="x", instructions="y", criteria={"A": None})
    assert result is None


def test_system_one_client_fails_closed_on_connection_error(monkeypatch):
    import urllib.error

    import m7_jev_relation_choice_v0_1 as jevmod

    def _raise(*a, **k):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(jevmod.urllib.request, "urlopen", _raise)
    client = JevKevSystemOneClient("http://192.168.1.11:8009")
    result = client.decide(state="x", instructions="y", criteria={"A": None})
    assert result is None


def test_system_one_client_reachable_probe_reflects_connection_state(monkeypatch):
    import urllib.error

    import m7_jev_relation_choice_v0_1 as jevmod

    monkeypatch.setattr(jevmod.urllib.request, "urlopen", lambda *a, **k: _FakeHTTPResponse({"models": []}))
    client = JevKevSystemOneClient("http://192.168.1.11:8009")
    assert client.reachable() is True

    def _raise(*a, **k):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(jevmod.urllib.request, "urlopen", _raise)
    assert client.reachable() is False
