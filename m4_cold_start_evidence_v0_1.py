"""MetaHIA M4 — Cold-start / Evidence Acquisition v0.1.

Purpose
-------
M4 turns UNKNOWN into an explicit acquisition workflow without making
acquisition, derivation, or external information equivalent to truth.

Core contract
-------------
- DERIVED != EVIDENCE != EPISTEMIC STATUS.
- Evidence independence is explicit and counted by independent_group/source_id.
- Human input can never be relabeled as GROUNDED_DIRECT.
- Analogy evidence remains GROUNDED_ANALOGY unless independently replaced by a
  direct source.
- The acquisition layer does not decide SUPPORT/CONTRADICTION; an evaluator
  supplied by the caller owns that decision.
- Every acquisition attempt is append-only and auditable.
- No semantic dictionary is required.

Levels
------
A — STRUCTURAL_BACKOFF: use already available structural/retrieval mechanisms.
B — UNKNOWN_HUMAN: if no admissible evidence is obtained, retain UNKNOWN and
    optionally request human input.
C — EXPLICIT_PROVENANCE: classify accepted evidence as GROUNDED_DIRECT,
    GROUNDED_ANALOGY, or UNGROUNDED_HUMAN according to its origin.

M4 is an orchestration/evidence-contract layer. It intentionally does not
modify kernel2.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple


# Evidence polarities and provenance values are deliberately opaque protocol
# markers, not semantic relation labels.
SUPPORT = "SUPPORT"
CHALLENGE = "CHALLENGE"

OBSERVATION = "OBSERVATION"
EXTERNAL = "EXTERNAL"
HUMAN = "HUMAN"
RETRIEVED = "RETRIEVED"
SYSTEM = "SYSTEM"

GROUNDED_DIRECT = "GROUNDED_DIRECT"
GROUNDED_ANALOGY = "GROUNDED_ANALOGY"
UNGROUNDED_HUMAN = "UNGROUNDED_HUMAN"

UNKNOWN = "UNKNOWN"
DERIVED = "DERIVED"
SUPPORTED = "SUPPORTED"
CONTRADICTED = "CONTRADICTED"

LEVEL_A = "A_STRUCTURAL_BACKOFF"
LEVEL_B = "B_UNKNOWN_HUMAN"
LEVEL_C = "C_EXPLICIT_PROVENANCE"

TRANSITION_ACQUIRED = "ACQUIRED"
TRANSITION_NO_EVIDENCE = "NO_EVIDENCE"
TRANSITION_HUMAN_REQUESTED = "HUMAN_REQUESTED"
TRANSITION_EVALUATED = "EVALUATED"


@dataclass(frozen=True)
class EvidenceRecord:
    """One piece of evidence with explicit provenance/independence metadata."""

    evidence_id: str
    candidate_id: str
    relation: Any
    polarity: str
    source_id: str
    kind: str
    confidence: float = 1.0
    location: Optional[str] = None
    independent_group: Optional[str] = None
    provenance: str = GROUNDED_DIRECT
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.polarity not in (SUPPORT, CHALLENGE):
            raise ValueError("invalid evidence polarity")
        if self.kind not in (OBSERVATION, EXTERNAL, HUMAN, RETRIEVED, SYSTEM):
            raise ValueError("invalid evidence kind")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be within [0,1]")
        if self.provenance not in (
            GROUNDED_DIRECT,
            GROUNDED_ANALOGY,
            UNGROUNDED_HUMAN,
        ):
            raise ValueError("invalid provenance")
        if self.kind == HUMAN and self.provenance != UNGROUNDED_HUMAN:
            raise ValueError("human evidence cannot be GROUNDED_DIRECT/GROUNDED_ANALOGY")
        if self.kind == EXTERNAL and self.provenance == UNGROUNDED_HUMAN:
            raise ValueError("external evidence cannot be UNGROUNDED_HUMAN")
        if self.kind == SYSTEM and self.provenance in (
            GROUNDED_DIRECT,
            GROUNDED_ANALOGY,
        ):
            raise ValueError("SYSTEM evidence cannot masquerade as grounded external evidence")


@dataclass(frozen=True)
class EvidenceAcceptance:
    accepted: bool
    reason: str
    independent_key: Optional[str] = None


@dataclass(frozen=True)
class AcquisitionRequest:
    candidate_id: str
    query_ref: str
    context: Mapping[str, Any] = field(default_factory=dict)
    max_level: str = LEVEL_C


@dataclass(frozen=True)
class HumanRequest:
    request_id: str
    candidate_id: str
    query_ref: str
    reason: str


@dataclass(frozen=True)
class AcquisitionTransition:
    candidate_id: str
    from_state: str
    to_state: str
    reason: str
    evidence_ids: Tuple[str, ...] = ()
    level: Optional[str] = None


@dataclass(frozen=True)
class AcquisitionAttempt:
    attempt_id: str
    candidate_id: str
    level: str
    query_ref: str
    source_ids: Tuple[str, ...]
    independent_groups: Tuple[str, ...]
    accepted_evidence_ids: Tuple[str, ...]
    rejected_evidence_ids: Tuple[str, ...]
    cost: float
    result_state: str
    transition_reason: str


@dataclass(frozen=True)
class AcquisitionResult:
    candidate_id: str
    initial_state: str
    final_state: str
    evidence: Tuple[EvidenceRecord, ...]
    attempts: Tuple[AcquisitionAttempt, ...]
    transitions: Tuple[AcquisitionTransition, ...]
    human_request: Optional[HumanRequest] = None

    @property
    def independent_evidence_count(self) -> int:
        return count_independent_evidence(self.evidence)

    @property
    def provenance_complete(self) -> bool:
        try:
            for evidence in self.evidence:
                evidence.validate()
            return True
        except ValueError:
            return False


@dataclass(frozen=True)
class NMinMeasurement:
    context_id: str
    n_min: Optional[int]
    tested_sizes: Tuple[int, ...]
    admissible_subsets: int
    successful_subsets: int
    criterion_name: str


@dataclass(frozen=True)
class ColdStartLedger:
    """Append-only ledger for M4 acquisition activity."""

    attempts: Tuple[AcquisitionAttempt, ...] = ()
    transitions: Tuple[AcquisitionTransition, ...] = ()

    def append(
        self,
        *,
        attempt: AcquisitionAttempt,
        transition: AcquisitionTransition,
    ) -> "ColdStartLedger":
        return ColdStartLedger(
            attempts=self.attempts + (attempt,),
            transitions=self.transitions + (transition,),
        )

    def validate(self) -> None:
        if len(self.transitions) != len(self.attempts):
            raise ValueError("ledger attempt/transition cardinality mismatch")
        for attempt in self.attempts:
            if attempt.cost < 0:
                raise ValueError("attempt cost cannot be negative")
        for transition in self.transitions:
            if not transition.candidate_id:
                raise ValueError("transition candidate_id is required")


def independent_key(evidence: EvidenceRecord) -> str:
    """Collapse evidence by independent_group, then source_id."""
    evidence.validate()
    return evidence.independent_group or evidence.source_id


def count_independent_evidence(evidence: Iterable[EvidenceRecord]) -> int:
    return len({independent_key(item) for item in evidence})


def split_independent_evidence(
    evidence: Iterable[EvidenceRecord],
) -> Tuple[Tuple[EvidenceRecord, ...], Tuple[EvidenceRecord, ...]]:
    """Return one representative per independent group plus duplicates."""
    primary = []
    duplicate = []
    seen: set[str] = set()
    for item in evidence:
        key = independent_key(item)
        if key in seen:
            duplicate.append(item)
        else:
            seen.add(key)
            primary.append(item)
    return tuple(primary), tuple(duplicate)


def accept_evidence(
    candidate_id: str,
    evidence: EvidenceRecord,
    *,
    blocked_source_ids: Sequence[str] = (),
    blocked_evidence_ids: Sequence[str] = (),
) -> EvidenceAcceptance:
    """Apply M4 evidence-contract guards without evaluating truth."""
    try:
        evidence.validate()
    except ValueError as exc:
        return EvidenceAcceptance(False, f"INVALID:{exc}")

    if evidence.candidate_id != candidate_id:
        return EvidenceAcceptance(False, "CANDIDATE_MISMATCH")
    if evidence.evidence_id in set(blocked_evidence_ids):
        return EvidenceAcceptance(False, "SELF_OR_BLOCKED_EVIDENCE")
    if evidence.evidence_id == candidate_id:
        return EvidenceAcceptance(False, "SELF_EVIDENCE_ID")
    if evidence.source_id == candidate_id:
        return EvidenceAcceptance(False, "SELF_SOURCE")
    if evidence.source_id in set(blocked_source_ids):
        return EvidenceAcceptance(False, "BLOCKED_SOURCE")
    if evidence.source_id.startswith("M1_ALGEBRA"):
        return EvidenceAcceptance(False, "DERIVATION_IS_NOT_EVIDENCE")
    if evidence.kind == SYSTEM:
        return EvidenceAcceptance(False, "SYSTEM_IS_NOT_INDEPENDENT_EVIDENCE")

    return EvidenceAcceptance(True, "ACCEPTED", independent_key(evidence))


def classify_provenance(*, kind: str, direct: bool, analogy: bool) -> str:
    """Assign provenance; ambiguous grounding declarations fail closed."""
    if kind == HUMAN:
        return UNGROUNDED_HUMAN
    if direct and analogy:
        raise ValueError("direct and analogy provenance are mutually exclusive")
    if analogy:
        return GROUNDED_ANALOGY
    if direct:
        return GROUNDED_DIRECT
    raise ValueError("direct or analogy provenance must be explicitly declared")


def build_evidence(
    *,
    evidence_id: str,
    candidate_id: str,
    relation: Any,
    polarity: str,
    source_id: str,
    kind: str,
    confidence: float = 1.0,
    location: Optional[str] = None,
    independent_group: Optional[str] = None,
    direct: bool = True,
    analogy: bool = False,
    metadata: Optional[Mapping[str, Any]] = None,
) -> EvidenceRecord:
    evidence = EvidenceRecord(
        evidence_id=evidence_id,
        candidate_id=candidate_id,
        relation=relation,
        polarity=polarity,
        source_id=source_id,
        kind=kind,
        confidence=confidence,
        location=location,
        independent_group=independent_group,
        provenance=classify_provenance(kind=kind, direct=direct, analogy=analogy),
        metadata=dict(metadata or {}),
    )
    evidence.validate()
    return evidence


def _normalize_provider_output(output: Any) -> Tuple[Tuple[EvidenceRecord, ...], float]:
    if output is None:
        return (), 0.0
    if isinstance(output, tuple) and len(output) == 2 and isinstance(output[1], (int, float)):
        raw, cost = output
    else:
        raw, cost = output, 0.0
    if raw is None:
        return (), float(cost)
    return tuple(raw), float(cost)


def acquire_cold_start(
    request: AcquisitionRequest,
    *,
    initial_state: str = UNKNOWN,
    backoff_provider: Optional[Callable[[AcquisitionRequest], Any]] = None,
    human_provider: Optional[Callable[[HumanRequest], Any]] = None,
    evaluator: Optional[
        Callable[[str, Sequence[EvidenceRecord]], str]
    ] = None,
    blocked_source_ids: Sequence[str] = (),
    blocked_evidence_ids: Sequence[str] = (),
) -> AcquisitionResult:
    """Execute the bounded M4 acquisition workflow.

    Providers return EvidenceRecord objects only.  The evaluator, when supplied,
    is the sole authority allowed to change the epistemic state after evidence
    acquisition.
    """
    if request.max_level not in (LEVEL_A, LEVEL_B, LEVEL_C):
        raise ValueError("invalid max_level")

    attempts: list[AcquisitionAttempt] = []
    transitions: list[AcquisitionTransition] = []
    accepted_all: list[EvidenceRecord] = []
    attempt_index = 0
    human_request: Optional[HumanRequest] = None
    state = initial_state

    def record_attempt(
        level: str,
        evidence: Sequence[EvidenceRecord],
        rejected: Sequence[str],
        cost: float,
        result_state: str,
        reason: str,
        *,
        from_state: str,
    ) -> None:
        nonlocal attempt_index
        attempt_index += 1
        accepted_ids = tuple(e.evidence_id for e in evidence)
        sources = tuple(e.source_id for e in evidence)
        groups = tuple(dict.fromkeys(independent_key(e) for e in evidence))
        attempt = AcquisitionAttempt(
            attempt_id=f"M4-A{attempt_index:03d}",
            candidate_id=request.candidate_id,
            level=level,
            query_ref=request.query_ref,
            source_ids=sources,
            independent_groups=groups,
            accepted_evidence_ids=accepted_ids,
            rejected_evidence_ids=tuple(rejected),
            cost=float(cost),
            result_state=result_state,
            transition_reason=reason,
        )
        transition = AcquisitionTransition(
            candidate_id=request.candidate_id,
            from_state=from_state,
            to_state=result_state,
            reason=reason,
            evidence_ids=accepted_ids,
            level=level,
        )
        attempts.append(attempt)
        transitions.append(transition)

    # Level A: structural/retrieval backoff.
    if backoff_provider is not None:
        raw, cost = _normalize_provider_output(backoff_provider(request))
        accepted: list[EvidenceRecord] = []
        rejected: list[str] = []
        for evidence in raw:
            verdict = accept_evidence(
                request.candidate_id,
                evidence,
                blocked_source_ids=blocked_source_ids,
                blocked_evidence_ids=blocked_evidence_ids,
            )
            if verdict.accepted:
                accepted.append(evidence)
            else:
                rejected.append(f"{evidence.evidence_id}:{verdict.reason}")

        accepted_all.extend(accepted)
        if accepted:
            next_state = (
                evaluator(request.candidate_id, tuple(accepted_all))
                if evaluator is not None
                else UNKNOWN
            )
            reason = (
                "EVIDENCE_ACQUIRED_AND_EVALUATED"
                if evaluator is not None
                else "EVIDENCE_ACQUIRED_NO_EVALUATOR"
            )
            record_attempt(
                LEVEL_A,
                accepted,
                rejected,
                cost,
                next_state,
                reason,
                from_state=state,
            )
            state = next_state
            if state != UNKNOWN or evaluator is None:
                return AcquisitionResult(
                    candidate_id=request.candidate_id,
                    initial_state=initial_state,
                    final_state=state,
                    evidence=tuple(accepted_all),
                    attempts=tuple(attempts),
                    transitions=tuple(transitions),
                    human_request=None,
                )
            # Evidence was admissible but insufficient. Continue through the
            # cold-start escalation rather than manufacturing a terminal state.

        else:
            record_attempt(
                LEVEL_A,
                (),
                rejected,
                cost,
                UNKNOWN,
                TRANSITION_NO_EVIDENCE,
                from_state=state,
            )
            state = UNKNOWN

    if request.max_level == LEVEL_A:
        return AcquisitionResult(
            candidate_id=request.candidate_id,
            initial_state=initial_state,
            final_state=state,
            evidence=tuple(accepted_all),
            attempts=tuple(attempts),
            transitions=tuple(transitions),
            human_request=None,
        )

    # Level B: remain UNKNOWN and request human evidence.  Merely requesting
    # human input must not alter epistemic state.
    human_request = HumanRequest(
        request_id=f"M4-H{len(attempts)+1:03d}",
        candidate_id=request.candidate_id,
        query_ref=request.query_ref,
        reason="NO_ADMISSIBLE_EVIDENCE_AFTER_STRUCTURAL_BACKOFF",
    )
    attempts.append(
        AcquisitionAttempt(
            attempt_id=f"M4-A{len(attempts)+1:03d}",
            candidate_id=request.candidate_id,
            level=LEVEL_B,
            query_ref=request.query_ref,
            source_ids=(),
            independent_groups=(),
            accepted_evidence_ids=(),
            rejected_evidence_ids=(),
            cost=0.0,
            result_state=UNKNOWN,
            transition_reason=TRANSITION_HUMAN_REQUESTED,
        )
    )
    transitions.append(
        AcquisitionTransition(
            candidate_id=request.candidate_id,
            from_state=state,
            to_state=UNKNOWN,
            reason=TRANSITION_HUMAN_REQUESTED,
            evidence_ids=(),
            level=LEVEL_B,
        )
    )

    if request.max_level == LEVEL_B or human_provider is None:
        return AcquisitionResult(
            candidate_id=request.candidate_id,
            initial_state=initial_state,
            final_state=UNKNOWN,
            evidence=tuple(accepted_all),
            attempts=tuple(attempts),
            transitions=tuple(transitions),
            human_request=human_request,
        )

    # Level C: explicit provenance for human-supplied evidence.
    raw, cost = _normalize_provider_output(human_provider(human_request))
    accepted_human: list[EvidenceRecord] = []
    rejected_human: list[str] = []
    for evidence in raw:
        verdict = accept_evidence(
            request.candidate_id,
            evidence,
            blocked_source_ids=blocked_source_ids,
            blocked_evidence_ids=blocked_evidence_ids,
        )
        if verdict.accepted:
            if evidence.kind != HUMAN or evidence.provenance != UNGROUNDED_HUMAN:
                rejected_human.append(f"{evidence.evidence_id}:INVALID_HUMAN_PROVENANCE")
            else:
                accepted_human.append(evidence)
        else:
            rejected_human.append(f"{evidence.evidence_id}:{verdict.reason}")

    accepted_all.extend(accepted_human)
    next_state = (
        evaluator(request.candidate_id, tuple(accepted_all))
        if accepted_all and evaluator is not None
        else UNKNOWN
    )
    reason = (
        "HUMAN_EVIDENCE_ACQUIRED_AND_EVALUATED"
        if accepted_human and evaluator is not None
        else "HUMAN_EVIDENCE_ACQUIRED_NO_EVALUATOR" if accepted_human else "NO_ADMISSIBLE_HUMAN_EVIDENCE"
    )
    record_attempt(
        LEVEL_C,
        accepted_human,
        rejected_human,
        cost,
        next_state,
        reason,
        from_state=UNKNOWN,
    )

    return AcquisitionResult(
        candidate_id=request.candidate_id,
        initial_state=initial_state,
        final_state=next_state,
        evidence=tuple(accepted_all),
        attempts=tuple(attempts),
        transitions=tuple(transitions),
        human_request=human_request,
    )


def measure_n_min(
    *,
    context_id: str,
    evidence_pool: Sequence[EvidenceRecord],
    success_criterion: Callable[[Sequence[EvidenceRecord]], bool],
    max_n: Optional[int] = None,
    criterion_name: str = "caller_supplied_criterion",
) -> NMinMeasurement:
    """Find the smallest number of independent evidence groups satisfying a criterion.

    For scientific transparency, all combinations are tested for the requested
    sizes. The method is intended for small controlled pools; callers should
    instrument/limit larger experiments rather than silently approximating.
    Duplicate evidence from the same independent group does not inflate n.
    """
    primary, _duplicates = split_independent_evidence(evidence_pool)
    pool = tuple(primary)
    limit = min(len(pool), max_n or len(pool))
    tested_sizes: list[int] = []
    admissible = 0
    successful = 0

    for n in range(1, limit + 1):
        tested_sizes.append(n)
        for subset in combinations(pool, n):
            admissible += 1
            if success_criterion(subset):
                successful += 1
                return NMinMeasurement(
                    context_id=context_id,
                    n_min=n,
                    tested_sizes=tuple(tested_sizes),
                    admissible_subsets=admissible,
                    successful_subsets=successful,
                    criterion_name=criterion_name,
                )

    return NMinMeasurement(
        context_id=context_id,
        n_min=None,
        tested_sizes=tuple(tested_sizes),
        admissible_subsets=admissible,
        successful_subsets=successful,
        criterion_name=criterion_name,
    )


__all__ = [
    "SUPPORT",
    "CHALLENGE",
    "OBSERVATION",
    "EXTERNAL",
    "HUMAN",
    "RETRIEVED",
    "SYSTEM",
    "GROUNDED_DIRECT",
    "GROUNDED_ANALOGY",
    "UNGROUNDED_HUMAN",
    "UNKNOWN",
    "DERIVED",
    "SUPPORTED",
    "CONTRADICTED",
    "LEVEL_A",
    "LEVEL_B",
    "LEVEL_C",
    "EvidenceRecord",
    "EvidenceAcceptance",
    "AcquisitionRequest",
    "HumanRequest",
    "AcquisitionTransition",
    "AcquisitionAttempt",
    "AcquisitionResult",
    "NMinMeasurement",
    "ColdStartLedger",
    "independent_key",
    "count_independent_evidence",
    "split_independent_evidence",
    "accept_evidence",
    "classify_provenance",
    "build_evidence",
    "acquire_cold_start",
    "measure_n_min",
]
