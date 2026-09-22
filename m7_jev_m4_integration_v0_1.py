"""MetaHIA M7 -- JEV/Kev to M4 integration test v0.1 (P8.4).

Explicit pivot requested after P8.3b: P8.1-P8.3b already extracted the
marginal information needed to characterize LABELED as a benchmark
(order sensitivity real but isolated to criteria order; wording
robust; MERE_DE/PERE_DE never confused; EPOUX_DE/EPOUSE_DE a
persistent, documented limitation). Continuing to tune LABELED's
prompt would have low marginal scientific value. The more important,
previously untested question: **does LABELED's known imperfection
actually threaten M4/M6's epistemic states, or does the existing M4
evidence-acquisition architecture already contain it?** -- "une
question d'architecture d'évidence, pas de perfectionnement du
modèle."

This is a small, hand-controlled integration test (4 real cases, 2
distinct real HTTP calls -- not another large benchmark), reusing
`m4_cold_start_evidence_v0_1.acquire_cold_start` exactly as
`m7_corpus_from_llm_v0_1.py` already does, and LABELED's FROZEN
baseline configuration (original criteria order, original
`instructions` wording -- the one combination with a full P8.1/P8.3a/
P8.3b real characterization; see `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`
Sec. 6 for why the separately-measured "best" order (`separated`,
P8.3a) and "best" wording (`imperative_short`, P8.3b) are NOT combined
here -- that specific pairing has never been run together, and
combining two independently-optimized settings without verifying them
jointly would be exactly the kind of unverified compounding this
project's own discipline refuses elsewhere).

Two evaluators are compared on the same evidence, to make the
architectural question concrete rather than rhetorical:

  `default_evaluator`      -- the exact pattern already used by
                               `m7_corpus_from_llm_v0_1.py` and
                               `m6_corpus_from_m4_m5_v0_2.py`: ANY
                               accepted CHALLENGE forces CONTRADICTED,
                               regardless of how much SUPPORT is also
                               present.
  `provenance_aware_evaluator` -- a CHALLENGE with provenance
                               GROUNDED_ANALOGY (exactly what JEV/Kev
                               evidence always is -- see
                               `m7_jev_relation_choice_v0_1.py`'s own
                               docstring) never overrides a SUPPORT
                               with provenance GROUNDED_DIRECT. This
                               is not an invented rule -- it
                               operationalizes the epistemic hierarchy
                               this project already states
                               (GROUNDED_DIRECT outranks
                               GROUNDED_ANALOGY) but which
                               `default_evaluator`'s "any CHALLENGE
                               wins" logic does not actually enforce.

Four cases, deliberately covering both a success mode and the known
failure mode, not just favorable cases:

  clean_agreement              -- candidate matches what the
                                   independent text actually says;
                                   sanity check.
  jev_catches_structural_error -- candidate is DELIBERATELY wrong; the
                                   independent text correctly
                                   contradicts it -- demonstrates
                                   real, positive M7 value.
  known_limitation_contamination -- candidate is CORRECT (matches the
                                   text), but the text is exactly the
                                   documented EPOUX_DE/EPOUSE_DE
                                   failure mode -- tests whether a
                                   single wrong LABELED classification
                                   can flip a TRUE candidate to
                                   CONTRADICTED with no other evidence
                                   present.
  known_limitation_with_corroboration -- same as above, PLUS one
                                   independent GROUNDED_DIRECT SUPPORT
                                   (simulating an already-available
                                   structural observation) -- tests
                                   whether corroborating direct
                                   evidence changes the outcome under
                                   each evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from m4_cold_start_evidence_v0_1 import (
    CHALLENGE,
    CONTRADICTED,
    GROUNDED_ANALOGY,
    GROUNDED_DIRECT,
    OBSERVATION,
    SUPPORT,
    SUPPORTED,
    UNKNOWN,
    AcquisitionRequest,
    EvidenceRecord,
    LEVEL_A,
    acquire_cold_start,
    build_evidence,
)
from m7_jev_benchmark_v0_2 import load_corpus
from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_LABELED,
    JevDecideClient,
    JevProposal,
    jev_evidence_for_prediction,
    propose_relation_jev,
)


def default_evaluator(candidate_id: str, accepted_evidence: Sequence[EvidenceRecord]) -> str:
    """The exact pattern already used by `m7_corpus_from_llm_v0_1._evaluator`
    and `m6_corpus_from_m4_m5_v0_2.py`'s own evaluator -- reused
    verbatim, not reinvented, so the comparison below is against this
    project's REAL existing convention, not a straw man."""
    if any(e.polarity == CHALLENGE for e in accepted_evidence):
        return CONTRADICTED
    if any(e.polarity == SUPPORT for e in accepted_evidence):
        return SUPPORTED
    return UNKNOWN


def provenance_aware_evaluator(candidate_id: str, accepted_evidence: Sequence[EvidenceRecord]) -> str:
    """A GROUNDED_ANALOGY challenge (exactly what JEV/Kev evidence
    always is) never overrides a GROUNDED_DIRECT support on its own --
    operationalizes the GROUNDED_DIRECT > GROUNDED_ANALOGY hierarchy
    this project already states elsewhere, which `default_evaluator`
    does not enforce. A GROUNDED_DIRECT challenge (never produced by
    JEV/Kev, but possible from other M7 sources) still overrides,
    exactly like before -- only analogy-sourced challenges are
    contained."""
    supports = [e for e in accepted_evidence if e.polarity == SUPPORT]
    challenges = [e for e in accepted_evidence if e.polarity == CHALLENGE]
    direct_supports = [e for e in supports if e.provenance == GROUNDED_DIRECT]
    non_analogy_challenges = [e for e in challenges if e.provenance != GROUNDED_ANALOGY]
    if direct_supports and not non_analogy_challenges:
        return SUPPORTED
    if challenges:
        return CONTRADICTED
    if supports:
        return SUPPORTED
    return UNKNOWN


@dataclass(frozen=True)
class IntegrationCheck:
    check_id: str
    description: str
    jev_text: str
    jev_subject: str
    jev_object: str
    structural_candidate_relation: str
    correct_final_state: str
    add_corroborating_direct_support: bool = False


CHECKS: Tuple[IntegrationCheck, ...] = (
    IntegrationCheck(
        check_id="clean_agreement",
        description="Candidate matches what the independent text actually says -- sanity check.",
        jev_text="Nora est la mère de Milo.",
        jev_subject="Nora",
        jev_object="Milo",
        structural_candidate_relation="MERE_DE",
        correct_final_state=SUPPORTED,
    ),
    IntegrationCheck(
        check_id="jev_catches_structural_error",
        description="Candidate is deliberately wrong (PERE_DE); the text correctly says MERE_DE.",
        jev_text="Nora est la mère de Milo.",
        jev_subject="Nora",
        jev_object="Milo",
        structural_candidate_relation="PERE_DE",
        correct_final_state=CONTRADICTED,
    ),
    IntegrationCheck(
        check_id="known_limitation_contamination",
        description=(
            "Candidate is CORRECT (EPOUX_DE, matches the text exactly), but the text is the "
            "documented EPOUX_DE/EPOUSE_DE LABELED failure mode -- tests whether one wrong "
            "classification alone flips a true candidate to CONTRADICTED."
        ),
        jev_text="Boris est l'époux de Kyra.",
        jev_subject="Boris",
        jev_object="Kyra",
        structural_candidate_relation="EPOUX_DE",
        correct_final_state=SUPPORTED,
    ),
    IntegrationCheck(
        check_id="known_limitation_with_corroboration",
        description=(
            "Same as known_limitation_contamination, plus one independent GROUNDED_DIRECT "
            "support -- tests whether corroborating direct evidence changes the outcome."
        ),
        jev_text="Boris est l'époux de Kyra.",
        jev_subject="Boris",
        jev_object="Kyra",
        structural_candidate_relation="EPOUX_DE",
        correct_final_state=SUPPORTED,
        add_corroborating_direct_support=True,
    ),
)


@dataclass(frozen=True)
class IntegrationOutcome:
    check_id: str
    description: str
    structural_candidate_relation: str
    jev_proposal: Optional[JevProposal]
    evidence: Tuple[EvidenceRecord, ...]
    default_final_state: str
    provenance_aware_final_state: str
    correct_final_state: str

    @property
    def default_matches_ground_truth(self) -> bool:
        return self.default_final_state == self.correct_final_state

    @property
    def provenance_aware_matches_ground_truth(self) -> bool:
        return self.provenance_aware_final_state == self.correct_final_state


def run_integration_checks(
    client: JevDecideClient,
    checks: Sequence[IntegrationCheck] = CHECKS,
) -> Tuple[IntegrationOutcome, ...]:
    vocabulary, _demonstration_set, _cases = load_corpus()
    proposal_cache: dict = {}
    outcomes = []

    for i, check in enumerate(checks):
        cache_key = check.jev_text
        if cache_key not in proposal_cache:
            proposal_cache[cache_key] = propose_relation_jev(
                text=check.jev_text,
                subject=check.jev_subject,
                obj=check.jev_object,
                all_relations=vocabulary,
                semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
                client=client,
            )
        proposal = proposal_cache[cache_key]

        evidence: list = []
        if proposal is not None:
            evidence.append(
                jev_evidence_for_prediction(
                    proposal,
                    candidate_id=check.check_id,
                    predicted_relation=check.structural_candidate_relation,
                    evidence_index=i,
                )
            )
        if check.add_corroborating_direct_support:
            evidence.append(
                build_evidence(
                    evidence_id=f"EV-DIRECT-{check.check_id}",
                    candidate_id=check.check_id,
                    relation=check.structural_candidate_relation,
                    polarity=SUPPORT,
                    source_id="structural_direct_observation",
                    kind=OBSERVATION,
                    confidence=1.0,
                    independent_group=f"direct::{check.check_id}",
                    direct=True,
                    analogy=False,
                )
            )
        evidence_tuple = tuple(evidence)

        def _run(evaluator):
            request = AcquisitionRequest(candidate_id=check.check_id, query_ref=check.check_id, max_level=LEVEL_A)
            result = acquire_cold_start(
                request,
                backoff_provider=lambda req, ev=evidence_tuple: (ev, 0.0),
                evaluator=evaluator,
            )
            return result.final_state

        outcomes.append(
            IntegrationOutcome(
                check_id=check.check_id,
                description=check.description,
                structural_candidate_relation=check.structural_candidate_relation,
                jev_proposal=proposal,
                evidence=evidence_tuple,
                default_final_state=_run(default_evaluator),
                provenance_aware_final_state=_run(provenance_aware_evaluator),
                correct_final_state=check.correct_final_state,
            )
        )

    return tuple(outcomes)


def outcome_to_dict(outcome: IntegrationOutcome) -> dict:
    return {
        "check_id": outcome.check_id,
        "description": outcome.description,
        "structural_candidate_relation": outcome.structural_candidate_relation,
        "jev_classified_relation": outcome.jev_proposal.relation if outcome.jev_proposal else None,
        "jev_confidence": outcome.jev_proposal.positive_prob if outcome.jev_proposal else None,
        "evidence_polarities": [e.polarity for e in outcome.evidence],
        "default_final_state": outcome.default_final_state,
        "provenance_aware_final_state": outcome.provenance_aware_final_state,
        "correct_final_state": outcome.correct_final_state,
        "default_matches_ground_truth": outcome.default_matches_ground_truth,
        "provenance_aware_matches_ground_truth": outcome.provenance_aware_matches_ground_truth,
    }


__all__ = [
    "CHECKS",
    "IntegrationCheck",
    "IntegrationOutcome",
    "default_evaluator",
    "provenance_aware_evaluator",
    "run_integration_checks",
    "outcome_to_dict",
]
