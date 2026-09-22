"""Permanent invariant tests for M7 -- JEV/Kev to M4 integration (P8.4,
`m7_jev_m4_integration_v0_1.py`).

Uses an injected fake `JevDecideClient` -- no network call. Verifies,
against hand-scripted agree/disagree responses, that:
  - a correct candidate corroborated by a correct JEV classification
    reaches SUPPORTED under both evaluators;
  - a wrong candidate correctly challenged by JEV reaches CONTRADICTED
    under both evaluators (real M7 value, not lost by the
    provenance-aware evaluator);
  - a CORRECT candidate wrongly challenged by JEV alone (no
    corroboration) is contaminated to CONTRADICTED under
    `default_evaluator` -- the exact failure mode this module exists to
    surface;
  - the SAME wrongly-challenged candidate, once corroborated by one
    independent GROUNDED_DIRECT support, is CONTAINED (SUPPORTED) under
    `provenance_aware_evaluator` but NOT under `default_evaluator`
    (still CONTRADICTED) -- the central architectural finding, proven
    here on fake data before any real Kev call is trusted.
"""
from __future__ import annotations

from typing import Mapping, Optional

from m4_cold_start_evidence_v0_1 import CONTRADICTED, SUPPORTED
from m7_jev_m4_integration_v0_1 import (
    CHECKS,
    default_evaluator,
    outcome_to_dict,
    provenance_aware_evaluator,
    run_integration_checks,
)


class _ScriptedJevClient:
    """Returns a fixed (chosen_relation, confidence) per exact text
    match, regardless of which candidate relation the caller is
    checking against -- exactly mirrors the real client's contract:
    JEV classifies the TEXT, it never sees the candidate."""

    def __init__(self, answer_by_text: Mapping[str, str], *, confidence: float = 0.9):
        self.answer_by_text = answer_by_text
        self.confidence = confidence

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        for text, chosen in self.answer_by_text.items():
            if text in state:
                others = [r for r in criteria if r != chosen]
                remainder = 0.0 if not others else (1.0 - self.confidence) / len(others)
                dist = {chosen: self.confidence, **{o: remainder for o in others}}
                return chosen, dist[chosen], dist
        raise AssertionError(f"no known text in state: {state!r}")


def _outcome(outcomes, check_id):
    return next(o for o in outcomes if o.check_id == check_id)


def test_clean_agreement_reaches_supported_under_both_evaluators():
    client = _ScriptedJevClient({"Nora est la mère de Milo.": "MERE_DE"})
    outcomes = run_integration_checks(client, checks=(next(c for c in CHECKS if c.check_id == "clean_agreement"),))
    (outcome,) = outcomes
    assert outcome.default_final_state == SUPPORTED
    assert outcome.provenance_aware_final_state == SUPPORTED
    assert outcome.default_matches_ground_truth
    assert outcome.provenance_aware_matches_ground_truth


def test_jev_catches_a_deliberately_wrong_candidate_under_both_evaluators():
    client = _ScriptedJevClient({"Nora est la mère de Milo.": "MERE_DE"})
    check = next(c for c in CHECKS if c.check_id == "jev_catches_structural_error")
    (outcome,) = run_integration_checks(client, checks=(check,))
    assert outcome.default_final_state == CONTRADICTED
    assert outcome.provenance_aware_final_state == CONTRADICTED
    assert outcome.default_matches_ground_truth  # correctly contradicted -- real M7 value, not lost


def test_a_correct_candidate_is_contaminated_by_a_lone_wrong_jev_classification():
    """The central failure mode this module surfaces: JEV misclassifies
    (scripted here as the documented EPOUX_DE/EPOUSE_DE confusion), and
    with no other evidence, `default_evaluator` flips a TRUE candidate
    to CONTRADICTED."""
    client = _ScriptedJevClient({"Boris est l'époux de Kyra.": "EPOUSE_DE"})
    check = next(c for c in CHECKS if c.check_id == "known_limitation_contamination")
    (outcome,) = run_integration_checks(client, checks=(check,))
    assert outcome.default_final_state == CONTRADICTED
    assert not outcome.default_matches_ground_truth  # contamination: candidate was actually correct


def test_corroborating_direct_evidence_is_contained_only_by_the_provenance_aware_evaluator():
    """The key comparison: identical wrong JEV classification, but this
    check adds one independent GROUNDED_DIRECT support.
    `default_evaluator` still lets the lone analogy challenge win
    (CONTRADICTED, still wrong); `provenance_aware_evaluator` contains
    it (SUPPORTED, correct) -- proving containment is architecturally
    available, just not the default."""
    client = _ScriptedJevClient({"Boris est l'époux de Kyra.": "EPOUSE_DE"})
    check = next(c for c in CHECKS if c.check_id == "known_limitation_with_corroboration")
    (outcome,) = run_integration_checks(client, checks=(check,))
    assert outcome.default_final_state == CONTRADICTED
    assert not outcome.default_matches_ground_truth
    assert outcome.provenance_aware_final_state == SUPPORTED
    assert outcome.provenance_aware_matches_ground_truth


def test_all_four_checks_run_together_with_only_two_distinct_jev_calls():
    """Cost discipline: clean_agreement/jev_catches_structural_error
    share one text, the two known_limitation checks share another --
    the proposal cache must mean exactly 2 distinct calls for 4 checks,
    verified by counting, not just asserted."""
    call_log = []

    class _CountingClient(_ScriptedJevClient):
        def decide(self, **kwargs):
            call_log.append(kwargs["state"])
            return super().decide(**kwargs)

    client = _CountingClient({"Nora est la mère de Milo.": "MERE_DE", "Boris est l'époux de Kyra.": "EPOUSE_DE"})
    outcomes = run_integration_checks(client)
    assert len(outcomes) == 4
    assert len(call_log) == 2


def test_outcome_to_dict_is_json_serializable_and_complete():
    import json

    client = _ScriptedJevClient({"Nora est la mère de Milo.": "MERE_DE", "Boris est l'époux de Kyra.": "EPOUSE_DE"})
    outcomes = run_integration_checks(client)
    payload = [outcome_to_dict(o) for o in outcomes]
    json.dumps(payload)  # must not raise
    for row in payload:
        assert "default_final_state" in row
        assert "provenance_aware_final_state" in row
        assert "correct_final_state" in row


def test_unreachable_client_yields_no_evidence_and_unknown_state():
    """Fails closed exactly like every other M7 mechanism: a `None`
    proposal must never be silently treated as agreement or
    disagreement."""

    class _UnreachableClient:
        def decide(self, **kwargs):
            return None

    check = next(c for c in CHECKS if c.check_id == "clean_agreement")
    (outcome,) = run_integration_checks(_UnreachableClient(), checks=(check,))
    assert outcome.jev_proposal is None
    assert outcome.evidence == ()
    assert outcome.default_final_state == "UNKNOWN"
    assert outcome.provenance_aware_final_state == "UNKNOWN"
