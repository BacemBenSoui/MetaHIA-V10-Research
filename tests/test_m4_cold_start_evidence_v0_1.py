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
    LEVEL_A,
    LEVEL_B,
    LEVEL_C,
    SUPPORT,
    SYSTEM,
    UNGROUNDED_HUMAN,
    UNKNOWN,
    AcquisitionRequest,
    ColdStartLedger,
    EvidenceRecord,
    accept_evidence,
    acquire_cold_start,
    build_evidence,
    count_independent_evidence,
    measure_n_min,
)


def _ev(eid, candidate="C1", source="S1", group=None, kind=EXTERNAL, provenance=GROUNDED_DIRECT, polarity=SUPPORT):
    return EvidenceRecord(
        evidence_id=eid,
        candidate_id=candidate,
        relation=("opaque", candidate),
        polarity=polarity,
        source_id=source,
        kind=kind,
        confidence=0.9,
        independent_group=group,
        provenance=provenance,
    )


def test_human_cannot_be_direct_grounding():
    evidence = _ev("E1", source="H1", kind=HUMAN, provenance=GROUNDED_DIRECT)
    verdict = accept_evidence("C1", evidence)
    assert verdict.accepted is False
    assert verdict.reason.startswith("INVALID:")
    assert "human evidence cannot" in verdict.reason


def test_independence_deduplicates_group():
    items = (_ev("E1", source="S1", group="G1"), _ev("E2", source="S2", group="G1"), _ev("E3", source="S3", group="G2"))
    assert count_independent_evidence(items) == 2


def test_self_derivation_is_not_evidence():
    evidence = _ev("E1", source="M1_ALGEBRA::C1")
    verdict = accept_evidence("C1", evidence)
    assert verdict.accepted is False
    assert verdict.reason == "DERIVATION_IS_NOT_EVIDENCE"


def test_backoff_with_direct_evidence_can_be_evaluated():
    evidence = _ev("E1", source="DOC1", group="DOC1")

    def provider(_request):
        return ([evidence], 1.5)

    def evaluator(_candidate, items):
        assert len(items) == 1
        return "SUPPORTED"

    result = acquire_cold_start(
        AcquisitionRequest("C1", "Q1", max_level=LEVEL_C),
        backoff_provider=provider,
        evaluator=evaluator,
    )
    assert result.final_state == "SUPPORTED"
    assert result.evidence[0].provenance == GROUNDED_DIRECT
    assert result.attempts[0].cost == 1.5


def test_empty_backoff_preserves_unknown_and_requests_human():
    result = acquire_cold_start(
        AcquisitionRequest("C1", "Q1", max_level=LEVEL_B),
        backoff_provider=lambda _r: ([], 2.0),
    )
    assert result.final_state == UNKNOWN
    assert result.human_request is not None
    assert result.attempts[-1].level == LEVEL_B


def test_human_evidence_is_explicitly_ungrounded_human():
    human_evidence = _ev("H1", source="annotator-1", kind=HUMAN, provenance=UNGROUNDED_HUMAN, group="H1")

    result = acquire_cold_start(
        AcquisitionRequest("C1", "Q1", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([], 0.0),
        human_provider=lambda _hr: ([human_evidence], 3.0),
        evaluator=lambda _c, _items: "SUPPORTED",
    )
    assert result.final_state == "SUPPORTED"
    assert result.evidence[0].provenance == UNGROUNDED_HUMAN


def test_human_direct_attempt_is_rejected_without_state_promotion():
    bad = _ev("H1", source="annotator-1", kind=HUMAN, provenance=GROUNDED_DIRECT, group="H1")
    # Constructor above intentionally produces an invalid object only via direct
    # dataclass creation; the acquisition contract must reject it before use.
    result = acquire_cold_start(
        AcquisitionRequest("C1", "Q1", max_level=LEVEL_C),
        backoff_provider=lambda _r: ([], 0.0),
        human_provider=lambda _hr: ([bad], 3.0),
        evaluator=lambda _c, _items: "SUPPORTED",
    )
    assert result.final_state == UNKNOWN
    assert result.evidence == ()


def test_n_min_counts_independent_groups_not_raw_records():
    pool = (
        _ev("E1", source="S1", group="G1"),
        _ev("E2", source="S2", group="G1"),
        _ev("E3", source="S3", group="G2"),
        _ev("E4", source="S4", group="G3"),
    )
    measurement = measure_n_min(
        context_id="ctx-1",
        evidence_pool=pool,
        success_criterion=lambda subset: len({x.independent_group for x in subset}) >= 2,
        criterion_name="two-independent-groups",
    )
    assert measurement.n_min == 2


def test_n_min_reports_unreachable_criterion():
    pool = (_ev("E1", source="S1", group="G1"),)
    measurement = measure_n_min(
        context_id="ctx-2",
        evidence_pool=pool,
        success_criterion=lambda subset: len(subset) >= 2,
        criterion_name="two-items",
    )
    assert measurement.n_min is None


def test_ledger_is_append_only_and_validates():
    ledger = ColdStartLedger()
    attempt_result = acquire_cold_start(
        AcquisitionRequest("C1", "Q1", max_level=LEVEL_B),
        backoff_provider=lambda _r: ([], 0.0),
    )
    for attempt, transition in zip(attempt_result.attempts, attempt_result.transitions):
        ledger = ledger.append(attempt=attempt, transition=transition)
    ledger.validate()
    assert len(ledger.attempts) == len(attempt_result.attempts)


def test_challenge_is_preserved_without_semantic_interpretation():
    support = _ev("E1", source="S1", group="G1", polarity=SUPPORT)
    challenge = _ev("E2", source="S2", group="G2", polarity=CHALLENGE)
    assert {x.polarity for x in (support, challenge)} == {SUPPORT, CHALLENGE}


def test_builder_rejects_ambiguous_provenance():
    try:
        build_evidence(
            evidence_id="E0",
            candidate_id="C1",
            relation=("opaque", 0),
            polarity=SUPPORT,
            source_id="DOC0",
            kind=EXTERNAL,
            direct=False,
            analogy=False,
        )
    except ValueError as exc:
        assert "explicitly declared" in str(exc)
    else:
        raise AssertionError("ambiguous provenance was silently accepted")


def test_builder_rejects_direct_and_analogy_together():
    try:
        build_evidence(
            evidence_id="E00",
            candidate_id="C1",
            relation=("opaque", 0),
            polarity=SUPPORT,
            source_id="DOC0",
            kind=EXTERNAL,
            direct=True,
            analogy=True,
        )
    except ValueError as exc:
        assert "mutually exclusive" in str(exc)
    else:
        raise AssertionError("conflicting provenance flags were silently accepted")


def test_builder_sets_provenance_deterministically():
    direct = build_evidence(
        evidence_id="E1",
        candidate_id="C1",
        relation=("opaque", 1),
        polarity=SUPPORT,
        source_id="DOC1",
        kind=EXTERNAL,
        direct=True,
        analogy=False,
    )
    analogy = build_evidence(
        evidence_id="E2",
        candidate_id="C1",
        relation=("opaque", 2),
        polarity=SUPPORT,
        source_id="DOC2",
        kind=EXTERNAL,
        direct=False,
        analogy=True,
    )
    assert direct.provenance == GROUNDED_DIRECT
    assert analogy.provenance == GROUNDED_ANALOGY
