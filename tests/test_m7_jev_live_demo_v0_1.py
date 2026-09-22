"""M7 -- live JEV/Kev demonstration v0.1.

Unlike test_m7_jev_relation_choice_v0_1.py (deterministic, injected fake
client), this file makes REAL calls to a Kev/Jev-compatible
`/v1/systemone` server. Skipped cleanly if that server is not reachable --
mirrors test_m7_live_ollama_demo_v0_1.py's own established pattern
exactly, so the main suite stays portable (a genuinely external reviewer,
or this repo before the LAN sandbox Kev deployment described in
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`, will not have
this reachable).

Base URL: `KEV_BASE_URL` env var if set, else
`http://192.168.1.11:8009` (the LAN sandbox host, the port the user's
actual Kev-0.8B deployment uses -- confirmed reachable and answering
real `/v1/systemone` calls 2026-09-22, see
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 6bis for the
first real smoke-test result). Not hardcoded anywhere else in this repo;
this is the single place a real deployment detail is allowed to appear,
exactly like `LOCAL_HOST` is for Ollama.

Live model calls are NOT deterministic across runs/checkpoints/hardware --
like `test_m7_live_ollama_demo_v0_1.py`, this test does not pin an exact
outcome. It only asserts the STRUCTURAL properties this mechanism
guarantees regardless of what Kev actually answers: a real HTTP round
trip, GROUNDED_ANALOGY provenance, a probability within [0, 1], honest
`None` when the answer cannot be used.
"""
from __future__ import annotations

import os

import pytest

from m4_cold_start_evidence_v0_1 import GROUNDED_ANALOGY
from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_GLOSSED,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_STRICT,
    JevKevSystemOneClient,
    WorkedExample,
    jev_evidence_for_prediction,
    propose_relation_jev,
)

KEV_BASE_URL = os.environ.get("KEV_BASE_URL", "http://192.168.1.11:8009")

_CLIENT = JevKevSystemOneClient(KEV_BASE_URL)

pytestmark = pytest.mark.skipif(
    not _CLIENT.reachable(), reason=f"Kev/Jev server not reachable at {KEV_BASE_URL} -- skipping live demo"
)

ALL_RELATIONS = ("EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE")


def test_live_labeled_call_returns_a_well_formed_proposal_or_none():
    """LABELED mode, matching the already-measured Jev benchmark
    (documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md Sec. 2) -- the
    first real call against this repo's own Kev deployment. A well-formed
    proposal must have a relation from the closed vocabulary and a
    probability within [0, 1]; `None` (e.g. server returned an
    out-of-vocabulary answer) is also an acceptable, honest outcome --
    this test never forces a specific answer out of a real external
    model.
    """
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
        client=_CLIENT,
    )
    if proposal is None:
        return
    assert proposal.relation in ALL_RELATIONS
    assert 0.0 <= proposal.positive_prob <= 1.0
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_LABELED

    evidence = jev_evidence_for_prediction(
        proposal, candidate_id="LIVE-DEMO-1", predicted_relation="MERE_DE", evidence_index=0
    )
    assert evidence.provenance == GROUNDED_ANALOGY
    assert evidence.metadata["semantic_condition"] == RELATION_VOCABULARY_MODE_LABELED


def test_live_glossed_call_returns_a_well_formed_proposal_or_none():
    """GLOSSED mode: same sentence, with explicit MetaHIA-authored
    definitions. First measured real result (2026-09-22, single case, not
    a benchmark): confidence 0.92, higher than LABELED's 0.85 on the same
    sentence -- consistent with, but not proof of, the hypothesis that
    an explicit definition helps. See
    documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md Sec. 6bis for the
    full honest write-up (n=1, not generalized)."""
    glosses = {
        "EPOUX_DE": "X est le mari de Y",
        "EPOUSE_DE": "X est la femme de Y",
        "MERE_DE": "X est la mère de Y",
        "PERE_DE": "X est le père de Y",
    }
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_GLOSSED,
        client=_CLIENT,
        glosses=glosses,
    )
    if proposal is None:
        return
    assert proposal.relation in ALL_RELATIONS
    assert 0.0 <= proposal.positive_prob <= 1.0
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_GLOSSED


def test_live_strict_call_returns_a_well_formed_proposal_or_none():
    """STRICT mode: opaque symbols only, plus worked examples -- the
    condition that actually tests this project's structural-abstraction
    hypothesis. First measured real result (2026-09-22, single case, not
    a benchmark): Kev correctly resolved the opaque symbol R3 back to
    MERE_DE from three worked examples alone, confidence 0.69 -- lower
    than LABELED (0.85) and GLOSSED (0.92) on the identical sentence, the
    expected direction (less semantic information given -> lower
    confidence), but a single case is a smoke test, not a controlled
    comparison. See
    documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md Sec. 6bis."""
    examples = (
        WorkedExample("Claire est la mère de Denis.", "MERE_DE"),
        WorkedExample("Eve est la mère de Frank.", "MERE_DE"),
        WorkedExample("Guy est le père de Henri.", "PERE_DE"),
    )
    proposal = propose_relation_jev(
        text="Alice est la mère de Bob.",
        subject="Alice",
        obj="Bob",
        all_relations=ALL_RELATIONS,
        semantic_condition=RELATION_VOCABULARY_MODE_STRICT,
        client=_CLIENT,
        worked_examples=examples,
    )
    if proposal is None:
        return
    assert proposal.relation in ALL_RELATIONS
    assert 0.0 <= proposal.positive_prob <= 1.0
    assert proposal.semantic_condition == RELATION_VOCABULARY_MODE_STRICT
