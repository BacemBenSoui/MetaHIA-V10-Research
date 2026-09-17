import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from m4_cold_start_evidence_v0_1 import (
    CHALLENGE,
    EXTERNAL,
    GROUNDED_ANALOGY,
    GROUNDED_DIRECT,
    HUMAN,
    LEVEL_C,
    SUPPORT,
    SYSTEM,
    UNGROUNDED_HUMAN,
    UNKNOWN,
    AcquisitionRequest,
    EvidenceRecord,
    accept_evidence,
    acquire_cold_start,
    count_independent_evidence,
    measure_n_min,
)


def ev(eid, *, candidate="C", source="S", group=None, kind=EXTERNAL,
       provenance=GROUNDED_DIRECT, polarity=SUPPORT, confidence=0.8):
    return EvidenceRecord(
        evidence_id=eid,
        candidate_id=candidate,
        relation=("opaque_relation", candidate),
        polarity=polarity,
        source_id=source,
        kind=kind,
        confidence=confidence,
        independent_group=group,
        provenance=provenance,
    )


def test_c01_unknown_is_not_promoted_without_evaluator():
    e = ev("E1", source="DOC1", group="G1")
    result = acquire_cold_start(
        AcquisitionRequest("C", "Q1", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([e], 1.0),
    )
    assert result.final_state == UNKNOWN
    assert result.evidence == (e,)


def test_c02_insufficient_level_a_escalates_to_level_b_and_c():
    e = ev("E1", source="DOC1", group="G1")
    h = ev("H1", source="HUM1", group="H1", kind=HUMAN, provenance=UNGROUNDED_HUMAN)
    calls = []

    def evaluator(_c, items):
        calls.append(tuple(x.evidence_id for x in items))
        return UNKNOWN

    result = acquire_cold_start(
        AcquisitionRequest("C", "Q2", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([e], 1.0),
        human_provider=lambda _h: ([h], 2.0),
        evaluator=evaluator,
    )
    assert [a.level for a in result.attempts] == ["A_STRUCTURAL_BACKOFF", "B_UNKNOWN_HUMAN", "C_EXPLICIT_PROVENANCE"]
    assert result.final_state == UNKNOWN
    assert result.evidence == (e, h)
    assert calls[-1] == ("E1", "H1")


def test_c03_human_grounding_cannot_be_forged_in_payload():
    forged = ev("H1", source="annotator", kind=HUMAN, provenance=GROUNDED_DIRECT)
    verdict = accept_evidence("C", forged)
    assert verdict.accepted is False
    assert verdict.reason.startswith("INVALID:")


def test_c04_system_and_m1_derivation_never_count_as_independent_evidence():
    system = ev("E1", source="machine", kind=SYSTEM, provenance=UNGROUNDED_HUMAN)
    m1 = ev("E2", source="M1_ALGEBRA::rule42")
    assert accept_evidence("C", system).accepted is False
    assert accept_evidence("C", m1).accepted is False


def test_c05_same_group_duplicates_do_not_reduce_measured_n_min():
    pool = (
        ev("E1", source="S1", group="G1"),
        ev("E2", source="S2", group="G1"),
        ev("E3", source="S3", group="G2"),
        ev("E4", source="S4", group="G3"),
    )
    assert count_independent_evidence(pool) == 3
    measurement = measure_n_min(
        context_id="C5",
        evidence_pool=pool,
        success_criterion=lambda subset: len({x.independent_group for x in subset}) >= 3,
        criterion_name="three-independent-groups",
    )
    assert measurement.n_min == 3


def test_c06_support_and_challenge_are_both_preserved():
    support = ev("E1", source="S1", group="G1", polarity=SUPPORT)
    challenge = ev("E2", source="S2", group="G2", polarity=CHALLENGE)
    result = acquire_cold_start(
        AcquisitionRequest("C", "Q6", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([support, challenge], 1.0),
    )
    assert {e.polarity for e in result.evidence} == {SUPPORT, CHALLENGE}


def test_c07_analogy_is_not_collapsed_into_direct():
    analogy = ev("E1", source="A1", group="A1", provenance=GROUNDED_ANALOGY)
    direct = ev("E2", source="D1", group="D1", provenance=GROUNDED_DIRECT)
    result = acquire_cold_start(
        AcquisitionRequest("C", "Q7", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([analogy, direct], 0.5),
    )
    assert result.evidence[0].provenance == GROUNDED_ANALOGY
    assert result.evidence[1].provenance == GROUNDED_DIRECT


def test_c08_deterministic_replay_of_same_request():
    e1 = ev("E1", source="S1", group="G1")
    e2 = ev("E2", source="S2", group="G2", polarity=CHALLENGE)

    def run_once():
        return acquire_cold_start(
            AcquisitionRequest("C", "Q8", max_level=LEVEL_C),
            backoff_provider=lambda _r: ([e1, e2], 1.25),
            evaluator=lambda _c, _items: UNKNOWN,
        )

    r1 = run_once()
    r2 = run_once()
    assert r1 == r2
    assert hashlib.sha256(repr(r1).encode()).hexdigest() == hashlib.sha256(repr(r2).encode()).hexdigest()


def test_c09_blocked_source_is_never_admitted():
    evidence = ev("E1", source="PARENT::R1")
    verdict = accept_evidence("C", evidence, blocked_source_ids=("PARENT::R1",))
    assert verdict.accepted is False
    assert verdict.reason == "BLOCKED_SOURCE"


def test_c10_human_request_alone_keeps_unknown():
    result = acquire_cold_start(
        AcquisitionRequest("C", "Q10", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([], 4.0),
        human_provider=None,
    )
    assert result.final_state == UNKNOWN
    assert result.human_request is not None
    assert all(t.to_state == UNKNOWN for t in result.transitions)
