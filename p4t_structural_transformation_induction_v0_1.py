"""P4-T -- Structural Transformation Induction (Gates A-G), v0.1.

Replaces "cross-domain transfer with a target endpoint" (P4-R) as the
primary experimental path toward E20-D's closure criteria, per an external
review of the already-committed `e20d_protocol.py` (E20-D v0.2/v0.3,
committed in 92d396d, well before this module): reference-equality,
permutation, and recursive-permutation discovery from paired
source/target observations, with fail-closed ambiguity and ungrounded
replay verified there directly by this project's own adversarial probes
(constant-target rejected, many-to-one rejected).

This module does NOT modify `e20d_protocol.py` or `kernel2.py`. It reuses
`e20d_protocol.discover_cross_slot_candidates`/`replay_candidate` for the
REFERENCE_EQUALITY / PERMUTATION / RECURSIVE_PERMUTATION families (already
validated there), and adds exactly one new, genuinely missing capability:
arity-changing selection mappings (projection, duplication, and their
composition), which `kernel2.compare()`/`compare_candidates()` cannot
express because they require equal arity between the two sides being
compared.

Gate structure (from the external review's proposed protocol):
  A. Discovery      -- train pairs only; system infers the transformation.
  B. Freeze         -- serialize to an opaque form with no reference back
                        to the training Node objects.
  C. Blind replay   -- fresh source-only inputs; target is never consulted.
  D. Independent witness -- compare prediction to ground truth, only now.
  E. Anti-cheating  -- ambiguity, contradiction, many-to-one, constant,
                        fresh operators/NodeRefs, nested structures,
                        provenance -- exercised in the test file, not here.
  F. Multiple transformation families, with explicit rejection of anything
     not expressible in this vocabulary (no semantic fallback).
  G. Cost measurement, honestly scoped: real counts and wall-clock timing,
     NOT yet wired into e20d_cognitive_control_v0_1.py's ROI/score_candidate
     (that function is coupled to PathRecord/PathCandidate, not to a
     transformation-discovery candidate -- wiring it in is future work,
     not claimed done here).

Scientific scope, stated plainly: this demonstrates STRUCTURAL
TRANSFORMATION INDUCTION FROM PAIRED OBSERVATIONS, not unsupervised
relation discovery from an unstructured graph. E20-D remains OPEN.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Optional, Sequence, Tuple

from kernel2 import (
    Node,
    NodeRef,
    OBSERVATION,
    reference_equal,
    structural_equal,
)
from e20d_protocol import (
    CrossSlotCandidate,
    discover_cross_slot_candidates,
    replay_candidate,
)

FAMILY_REFERENCE_EQUALITY = "REFERENCE_EQUALITY"
FAMILY_PERMUTATION = "COMPARE_PERMUTATION"
FAMILY_RECURSIVE_PERMUTATION = "COMPARE_RECURSIVE"
FAMILY_SELECTION_MAPPING = "SELECTION_MAPPING"

OUTCOME_CANDIDATE = "CANDIDATE"
OUTCOME_AMBIGUOUS = "AMBIGUOUS"
OUTCOME_REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Gate F: generalized selection mapping (projection / duplication / composed)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SelectionMappingResult:
    """Per-target-position resolution of a source->target selection mapping.

    `sigma[j]` is the unique source position that every row's target
    position j is reference-equal to. A position with zero or more than one
    consistent source candidate is never guessed: it is recorded in
    `rejected_positions` / `ambiguous_positions` instead.
    """

    sigma: Tuple[Optional[int], ...]
    ambiguous_positions: Tuple[int, ...]
    rejected_positions: Tuple[int, ...]
    source_arity: int
    target_arity: int

    @property
    def is_fully_resolved(self) -> bool:
        return not self.ambiguous_positions and not self.rejected_positions


def discover_selection_mapping(
    pairs: Sequence[Tuple[Node, Node]],
) -> SelectionMappingResult:
    """Discover sigma: target_position -> source_position from OBSERVATION pairs.

    `pairs` is a sequence of (source_obs, target_obs) rows. Unlike
    `kernel2.compare()`, source and target arity may differ -- this is what
    makes projection (target_arity < source_arity) and duplication (a source
    position reused at more than one target position) expressible at all.

    sigma[j] is resolved only when EXACTLY ONE source position i satisfies
    reference_equal(target.children[j], source.children[i]) for EVERY row.
    Zero such positions -> rejected (not identifiable in this vocabulary).
    More than one -> ambiguous (the data does not distinguish them; never
    picked arbitrarily). This is the same "never guess among competing
    candidates" discipline `kernel2.compare_candidates()` already applies,
    extended to arity-changing mappings it cannot itself express.
    """
    if not pairs:
        raise ValueError("discover_selection_mapping requires at least one row")
    source_arity = len(pairs[0][0].children)
    target_arity = len(pairs[0][1].children)
    for src, tgt in pairs:
        if src.kind != OBSERVATION or tgt.kind != OBSERVATION:
            raise ValueError("both source and target must be OBSERVATION nodes")
        if len(src.children) != source_arity or len(tgt.children) != target_arity:
            raise ValueError("source/target arity must be constant across rows")

    sigma: list[Optional[int]] = [None] * target_arity
    ambiguous: list[int] = []
    rejected: list[int] = []

    for j in range(target_arity):
        matches = []
        for i in range(source_arity):
            if all(reference_equal(tgt.children[j], src.children[i]) for src, tgt in pairs):
                matches.append(i)
        if len(matches) == 1:
            sigma[j] = matches[0]
        elif len(matches) == 0:
            rejected.append(j)
        else:
            ambiguous.append(j)

    return SelectionMappingResult(
        sigma=tuple(sigma),
        ambiguous_positions=tuple(ambiguous),
        rejected_positions=tuple(rejected),
        source_arity=source_arity,
        target_arity=target_arity,
    )


def classify_selection_mapping(result: SelectionMappingResult) -> str:
    """Descriptive-only classification of a resolved selection mapping.

    Purely informative (which family name a human reads in a report); the
    mechanism and its safety properties are identical across these labels.
    """
    if not result.is_fully_resolved:
        return "UNRESOLVED"
    sigma = [s for s in result.sigma if s is not None]
    if result.source_arity == result.target_arity and sorted(sigma) == list(range(result.source_arity)):
        if sigma == list(range(result.source_arity)):
            return "IDENTITY"
        return "PROJECTION_PERMUTATION"  # bijective reorder, i.e. plain permutation
    if result.target_arity < result.source_arity and len(set(sigma)) == len(sigma):
        return "PROJECTION"
    if len(set(sigma)) < len(sigma):
        return "DUPLICATION"
    return "PROJECTION_PERMUTATION"


# ---------------------------------------------------------------------------
# Gate A: unified discovery entry point
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformationCandidate:
    family: str
    outcome: str
    cross_slot: Optional[CrossSlotCandidate] = None
    selection: Optional[SelectionMappingResult] = None
    discovery_row_ids: Tuple[str, ...] = field(default_factory=tuple)


def discover(
    observations: Sequence[Node],
    *,
    source_position: int,
    target_position: int,
    min_evidence: int = 3,
) -> TransformationCandidate:
    """Gate A. Train data only: `observations` are full rows; the
    transformation is discovered strictly between `source_position` and
    `target_position` within each row -- exactly `e20d_protocol.py`'s own
    row convention (a row's children include a source slot and a target
    slot at fixed positions), extended to also try arity-changing selection
    mappings when the same-arity mechanisms find nothing.
    """
    cross = discover_cross_slot_candidates(observations, min_evidence=min_evidence)
    row_ids = tuple(obs.node_id for obs in observations)
    for candidate in cross.candidates:
        if (candidate.source_position, candidate.target_position) == (source_position, target_position):
            return TransformationCandidate(
                family=candidate.relation_kind,
                outcome=OUTCOME_CANDIDATE,
                cross_slot=candidate,
                discovery_row_ids=row_ids,
            )
    for src_p, tgt_p, rows in cross.ambiguous_pairs:
        if (src_p, tgt_p) == (source_position, target_position):
            return TransformationCandidate(family=FAMILY_SELECTION_MAPPING, outcome=OUTCOME_AMBIGUOUS, discovery_row_ids=row_ids)

    pairs = [(obs.children[source_position], obs.children[target_position]) for obs in observations]
    if not all(isinstance(s, Node) and isinstance(t, Node) for s, t in pairs):
        return TransformationCandidate(family=FAMILY_SELECTION_MAPPING, outcome=OUTCOME_REJECTED, discovery_row_ids=row_ids)
    selection = discover_selection_mapping(pairs)
    if selection.is_fully_resolved:
        return TransformationCandidate(
            family=FAMILY_SELECTION_MAPPING,
            outcome=OUTCOME_CANDIDATE,
            selection=selection,
            discovery_row_ids=row_ids,
        )
    if selection.ambiguous_positions:
        return TransformationCandidate(family=FAMILY_SELECTION_MAPPING, outcome=OUTCOME_AMBIGUOUS, discovery_row_ids=row_ids)
    return TransformationCandidate(family=FAMILY_SELECTION_MAPPING, outcome=OUTCOME_REJECTED, discovery_row_ids=row_ids)


# ---------------------------------------------------------------------------
# Gate B: freeze -- opaque, no reference to training Node objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrozenTransformation:
    frozen_id: str
    family: str
    sigma: Tuple[Optional[int], ...]
    source_arity: int
    target_arity: int
    structural_digest: str
    cross_slot_transformation: Optional[object] = None  # opaque RefObject, for PERMUTATION/RECURSIVE only


def freeze(candidate: TransformationCandidate, *, frozen_id: str) -> FrozenTransformation:
    """Gate B. After this call, nothing in the returned object lets a
    caller recover which training rows produced it: no row ids, no NodeRef
    identities, only the positional sigma (for SELECTION_MAPPING) or the
    already-opaque RefObject (for the reused e20d_protocol families) plus a
    structural digest for tamper detection.
    """
    if candidate.outcome != OUTCOME_CANDIDATE:
        raise ValueError(f"cannot freeze a non-candidate outcome: {candidate.outcome}")
    if candidate.selection is not None:
        sigma = candidate.selection.sigma
        digest = sha256(repr((candidate.family, sigma)).encode("utf-8")).hexdigest()
        return FrozenTransformation(
            frozen_id=frozen_id,
            family=candidate.family,
            sigma=sigma,
            source_arity=candidate.selection.source_arity,
            target_arity=candidate.selection.target_arity,
            structural_digest=digest,
        )
    cs = candidate.cross_slot
    assert cs is not None
    digest = sha256(repr((candidate.family, cs.relation_kind)).encode("utf-8")).hexdigest()
    return FrozenTransformation(
        frozen_id=frozen_id,
        family=candidate.family,
        sigma=(),
        source_arity=-1,
        target_arity=-1,
        structural_digest=digest,
        cross_slot_transformation=cs,
    )


# ---------------------------------------------------------------------------
# Gate C: blind replay -- source only, target never consulted
# ---------------------------------------------------------------------------


def _blind_replay_one(frozen: FrozenTransformation, source_obs: Node) -> Optional[Node]:
    if len(source_obs.children) != frozen.source_arity:
        return None
    predicted_children = tuple(
        source_obs.children[i] if i is not None else None for i in frozen.sigma
    )
    if any(c is None for c in predicted_children):
        return None
    return Node(
        node_id=f"predicted::{frozen.frozen_id}::{source_obs.node_id}",
        kind=OBSERVATION,
        children=predicted_children,
        provenance=(frozen.frozen_id, source_obs.node_id),
    )


def blind_replay(frozen: FrozenTransformation, source_observations: Sequence[Node]) -> Tuple[Optional[Node], ...]:
    """Gate C. Applies the frozen transformation to fresh source
    observations, batched (matching `e20d_protocol.replay_candidate`'s own
    batch-column design for the reused families). Never receives, and
    never needs, any target/ground-truth value -- callers proving
    non-circularity should construct their holdout target slot with an
    opaque placeholder never read here (see the same discipline already
    used by `tests/test_e20d_v03_recursive_transform.py`).
    """
    if frozen.family == FAMILY_SELECTION_MAPPING:
        return tuple(_blind_replay_one(frozen, obs) for obs in source_observations)
    if frozen.cross_slot_transformation is not None:
        cs = frozen.cross_slot_transformation
        width = cs.source_position + 1
        synthetic_rows = [
            Node(
                node_id=f"synthetic::{frozen.frozen_id}::{i}",
                kind=OBSERVATION,
                children=tuple(
                    source_obs if pos == cs.source_position else NodeRef(f"_unused_{pos}")
                    for pos in range(width)
                ),
                provenance=(source_obs.node_id,),
            )
            for i, source_obs in enumerate(source_observations)
        ]
        out = replay_candidate(cs, synthetic_rows)
        if out is None:
            return tuple(None for _ in source_observations)
        return tuple(out.children)
    return tuple(None for _ in source_observations)


def compose_frozen(outer: FrozenTransformation, inner: FrozenTransformation, *, frozen_id: str) -> FrozenTransformation:
    """Gate F (composition). Chains two already-frozen SELECTION_MAPPING
    transformations end to end: applying the result is equivalent to
    applying `inner` then `outer` -- a genuine transformation-of-
    transformations, not a re-run of discovery on the composed data.
    """
    if outer.family != FAMILY_SELECTION_MAPPING or inner.family != FAMILY_SELECTION_MAPPING:
        raise ValueError("compose_frozen only supports two SELECTION_MAPPING transformations")
    if outer.source_arity != inner.target_arity:
        raise ValueError("outer.source_arity must match inner.target_arity to compose")
    composed_sigma = tuple(
        inner.sigma[i] if i is not None else None for i in outer.sigma
    )
    digest = sha256(repr((FAMILY_SELECTION_MAPPING, composed_sigma)).encode("utf-8")).hexdigest()
    return FrozenTransformation(
        frozen_id=frozen_id,
        family=FAMILY_SELECTION_MAPPING,
        sigma=composed_sigma,
        source_arity=inner.source_arity,
        target_arity=outer.target_arity,
        structural_digest=digest,
    )


# ---------------------------------------------------------------------------
# Gate D: independent witness
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationResult:
    match: bool
    predicted: Optional[Node]
    ground_truth: Node


def verify(predicted: Optional[Node], ground_truth: Node) -> VerificationResult:
    """Gate D. Called only after Gate C has already produced a prediction --
    never before, and this module never calls it internally."""
    if predicted is None:
        return VerificationResult(False, None, ground_truth)
    return VerificationResult(structural_equal(predicted, ground_truth), predicted, ground_truth)


# ---------------------------------------------------------------------------
# Gate G: cost measurement (honestly scoped -- not yet wired to E20-D.19 ROI)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P4TCostReport:
    discovery_seconds: float
    discovery_row_count: int
    discovery_position_pairs_tried: int
    replay_seconds: float
    replay_row_count: int
    verify_seconds: float


def run_costed_pipeline(
    train_observations: Sequence[Node],
    holdout_source_observations: Sequence[Node],
    holdout_ground_truth: Sequence[Node],
    *,
    source_position: int,
    target_position: int,
    frozen_id: str,
    min_evidence: int = 3,
) -> Tuple[TransformationCandidate, Optional[FrozenTransformation], Tuple[VerificationResult, ...], P4TCostReport]:
    """Runs Gates A -> B -> C -> D end to end on real data and returns a
    real, measured cost report (Gate G) alongside the results. No cost
    number here is estimated or invented -- every field is a direct
    measurement of this exact run.
    """
    width = len(train_observations[0].children) if train_observations else 0
    position_pairs_tried = max(0, width * (width - 1))

    t0 = time.perf_counter()
    candidate = discover(
        train_observations,
        source_position=source_position,
        target_position=target_position,
        min_evidence=min_evidence,
    )
    discovery_seconds = time.perf_counter() - t0

    frozen = None
    predictions: Tuple[Optional[Node], ...] = ()
    t1 = time.perf_counter()
    if candidate.outcome == OUTCOME_CANDIDATE:
        frozen = freeze(candidate, frozen_id=frozen_id)
        predictions = blind_replay(frozen, holdout_source_observations)
    replay_seconds = time.perf_counter() - t1

    t2 = time.perf_counter()
    verifications = tuple(
        verify(predicted, truth) for predicted, truth in zip(predictions, holdout_ground_truth)
    )
    verify_seconds = time.perf_counter() - t2

    report = P4TCostReport(
        discovery_seconds=discovery_seconds,
        discovery_row_count=len(train_observations),
        discovery_position_pairs_tried=position_pairs_tried,
        replay_seconds=replay_seconds,
        replay_row_count=len(holdout_source_observations),
        verify_seconds=verify_seconds,
    )
    return candidate, frozen, verifications, report


__all__ = [
    "FAMILY_PERMUTATION",
    "FAMILY_RECURSIVE_PERMUTATION",
    "FAMILY_REFERENCE_EQUALITY",
    "FAMILY_SELECTION_MAPPING",
    "OUTCOME_AMBIGUOUS",
    "OUTCOME_CANDIDATE",
    "OUTCOME_REJECTED",
    "FrozenTransformation",
    "P4TCostReport",
    "SelectionMappingResult",
    "TransformationCandidate",
    "VerificationResult",
    "blind_replay",
    "classify_selection_mapping",
    "compose_frozen",
    "discover",
    "discover_selection_mapping",
    "freeze",
    "run_costed_pipeline",
    "verify",
]
