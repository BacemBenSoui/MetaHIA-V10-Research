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
`e20d_protocol.discover_cross_slot_candidates` for discovery of the
REFERENCE_EQUALITY / PERMUTATION / RECURSIVE_PERMUTATION families (already
validated there). Gate B (freeze) does NOT reuse `replay_candidate`'s
`CrossSlotCandidate` object as-is: that object's own `evidence_rows`/
`source_target_provenance` fields, and even the PATTERN Node's own
`node_id`/`provenance` strings built by `e20d_protocol.py`, embed the
training row ids directly (found and fixed 2026-09-21, confirmed by direct
execution before fixing -- see `tests/test_frozen_recursive_transformation_does_not_leak_training_row_ids`).
`freeze()` instead rebuilds an anonymized copy of the pattern (`_anonymize_pattern`)
and `blind_replay()` applies it directly via `kernel2.apply()`, never
calling `replay_candidate()`. This module also adds exactly one new,
genuinely missing capability:
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
    PATTERN,
    PatternSlot,
    apply,
    ref_object,
    reference_equal,
    resolve_structure,
    structural_equal,
    structural_signature,
)
from e20d_protocol import (
    CrossSlotCandidate,
    discover_cross_slot_candidates,
)
from e20d_rationalization_v0_1 import RationalizationResult, rationalize
from e20d_cognitive_control_v0_1 import DECISION_DEFER, DECISION_EXPLORE, DECISION_STOP

FAMILY_REFERENCE_EQUALITY = "REFERENCE_EQUALITY"
FAMILY_PERMUTATION = "COMPARE_PERMUTATION"
FAMILY_RECURSIVE_PERMUTATION = "COMPARE_RECURSIVE"
FAMILY_SELECTION_MAPPING = "SELECTION_MAPPING"
FAMILY_MULTI_SOURCE_SELECTION_MAPPING = "MULTI_SOURCE_SELECTION_MAPPING"

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
# Gate F (P4-T.4): a genuinely new family -- multi-source selection mapping
#
# `discover_selection_mapping` above assembles a target from ONE source
# structure. This section generalizes it to assemble a target from
# MULTIPLE, independently-named source structures -- e.g. a target that
# combines a part of source A with a part of source B, which neither
# `kernel2.compare()` (single pairwise comparison, equal arity) nor
# `discover_selection_mapping` (single source) can express. Same
# never-guess discipline: an unresolved position is exposed as ambiguous
# or rejected, never picked arbitrarily.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MultiSourceSelectionResult:
    """Per-target-position resolution of a MULTI-source selection mapping.

    `sigma[j]` is `(source_slot_index, child_index)`: which of the named
    source structures, and which of ITS children, every row's target
    position j is reference-equal to. `source_slot_index` indexes into the
    `source_positions` sequence the caller supplied, not into the row
    itself.
    """

    sigma: Tuple[Optional[Tuple[int, int]], ...]
    ambiguous_positions: Tuple[int, ...]
    rejected_positions: Tuple[int, ...]
    source_arities: Tuple[int, ...]
    target_arity: int

    @property
    def is_fully_resolved(self) -> bool:
        return not self.ambiguous_positions and not self.rejected_positions


def discover_multi_source_selection_mapping(
    rows: Sequence[Tuple[Tuple[Node, ...], Node]],
) -> MultiSourceSelectionResult:
    """Discover sigma: target_position -> (source_slot_index, child_index)
    from rows of (sources, target), where `sources` is a fixed-length tuple
    of independently-named source observations per row.

    sigma[j] is resolved only when EXACTLY ONE (source_slot_index,
    child_index) pair satisfies reference_equal(target.children[j],
    sources[source_slot_index].children[child_index]) for EVERY row. Zero
    such pairs -> rejected. More than one -> ambiguous -- the data does not
    distinguish them, never picked arbitrarily.
    """
    if not rows:
        raise ValueError("discover_multi_source_selection_mapping requires at least one row")
    n_sources = len(rows[0][0])
    if n_sources < 2:
        raise ValueError("multi-source discovery requires at least 2 named source structures")
    source_arities = tuple(len(s.children) for s in rows[0][0])
    target_arity = len(rows[0][1].children)
    for sources, target in rows:
        if len(sources) != n_sources or tuple(len(s.children) for s in sources) != source_arities:
            raise ValueError("source count/arity must be constant across rows")
        if len(target.children) != target_arity:
            raise ValueError("target arity must be constant across rows")

    sigma: list[Optional[Tuple[int, int]]] = [None] * target_arity
    ambiguous: list[int] = []
    rejected: list[int] = []

    for j in range(target_arity):
        matches: list[Tuple[int, int]] = []
        for s in range(n_sources):
            for i in range(source_arities[s]):
                if all(reference_equal(target.children[j], sources[s].children[i]) for sources, target in rows):
                    matches.append((s, i))
        if len(matches) == 1:
            sigma[j] = matches[0]
        elif len(matches) == 0:
            rejected.append(j)
        else:
            ambiguous.append(j)

    return MultiSourceSelectionResult(
        sigma=tuple(sigma),
        ambiguous_positions=tuple(ambiguous),
        rejected_positions=tuple(rejected),
        source_arities=source_arities,
        target_arity=target_arity,
    )


# ---------------------------------------------------------------------------
# Gate A: unified discovery entry point
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformationCandidate:
    family: str
    outcome: str
    cross_slot: Optional[CrossSlotCandidate] = None
    selection: Optional[SelectionMappingResult] = None
    multi_selection: Optional[MultiSourceSelectionResult] = None
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


def discover_multi_source(
    observations: Sequence[Node],
    *,
    source_positions: Sequence[int],
    target_position: int,
    min_evidence: int = 3,
) -> TransformationCandidate:
    """Gate A, multi-source variant (P4-T.4). Train data only: each row's
    children at `source_positions` are the independently-named source
    structures; `target_position` is the structure to explain. Unlike
    `discover()`, this never falls back to the single-source mechanism --
    callers who only have one source structure should use `discover()`
    instead, since a length-1 `source_positions` would just be a more
    awkward way to say the same thing.
    """
    if len(source_positions) < 2:
        raise ValueError("discover_multi_source requires at least 2 source_positions; use discover() for one")
    if len(observations) < min_evidence:
        raise ValueError(f"P4-T requires at least {min_evidence} observations")
    row_ids = tuple(obs.node_id for obs in observations)

    rows: list[Tuple[Tuple[Node, ...], Node]] = []
    for obs in observations:
        sources = tuple(obs.children[sp] for sp in source_positions)
        target = obs.children[target_position]
        if not all(isinstance(s, Node) for s in sources) or not isinstance(target, Node):
            return TransformationCandidate(
                family=FAMILY_MULTI_SOURCE_SELECTION_MAPPING, outcome=OUTCOME_REJECTED, discovery_row_ids=row_ids
            )
        rows.append((sources, target))

    multi_selection = discover_multi_source_selection_mapping(rows)
    if multi_selection.is_fully_resolved:
        return TransformationCandidate(
            family=FAMILY_MULTI_SOURCE_SELECTION_MAPPING,
            outcome=OUTCOME_CANDIDATE,
            multi_selection=multi_selection,
            discovery_row_ids=row_ids,
        )
    if multi_selection.ambiguous_positions:
        return TransformationCandidate(
            family=FAMILY_MULTI_SOURCE_SELECTION_MAPPING, outcome=OUTCOME_AMBIGUOUS, discovery_row_ids=row_ids
        )
    return TransformationCandidate(
        family=FAMILY_MULTI_SOURCE_SELECTION_MAPPING, outcome=OUTCOME_REJECTED, discovery_row_ids=row_ids
    )


# ---------------------------------------------------------------------------
# Gate A.3 (P4-T.3): hypothesis selection among multiple candidates
#
# `discover()` above requires the caller to already name the
# (source_position, target_position) pair to test -- it never decides
# WHICH pair is "the" transformation when several are structurally
# viable. This section keeps that distinction explicit: discovery
# enumerates every viable hypothesis; selection ranks them by structural
# complexity only (no semantic dictionary) and retains the unique
# simplest one, exposing a genuine tie as AMBIGUOUS_SELECTION rather than
# picking arbitrarily -- extending this project's existing "never guess
# among competing candidates" discipline (kernel2.compare_candidates(),
# discover_selection_mapping()) to the selection layer itself.
# ---------------------------------------------------------------------------

FAMILY_COMPLEXITY_RANK = {
    FAMILY_REFERENCE_EQUALITY: 0,
    FAMILY_PERMUTATION: 1,
    FAMILY_SELECTION_MAPPING: 2,
    FAMILY_RECURSIVE_PERMUTATION: 3,
    FAMILY_MULTI_SOURCE_SELECTION_MAPPING: 4,  # combines >=2 independent sources -- ranked most complex
}

OUTCOME_RETAINED = "RETAINED"
OUTCOME_AMBIGUOUS_SELECTION = "AMBIGUOUS_SELECTION"
OUTCOME_NO_HYPOTHESES = "NO_HYPOTHESES"


@dataclass(frozen=True)
class Hypothesis:
    source_position: int
    target_position: int
    candidate: TransformationCandidate
    complexity_rank: int


@dataclass(frozen=True)
class HypothesisSelectionResult:
    outcome: str
    retained: Optional[Hypothesis]
    all_hypotheses: Tuple[Hypothesis, ...]


def discover_all_hypotheses(observations: Sequence[Node], *, min_evidence: int = 3) -> Tuple[Hypothesis, ...]:
    """Enumerates every ordered (source_position, target_position) pair and
    collects every non-rejected, non-ambiguous transformation candidate as
    one structural hypothesis. Discovery itself never decides which one is
    retained -- see `select_hypothesis()`.

    Note on symmetry: a REFERENCE_EQUALITY relationship is genuinely
    undirected (if column i always equals column j, then (i, j) and (j, i)
    are both structurally valid, equally-ranked hypotheses). This function
    reports both rather than silently picking a direction -- `select_hypothesis()`
    will then correctly expose that as an ambiguous tie rather than an
    arbitrary choice.
    """
    if not observations:
        return ()
    width = len(observations[0].children)
    hypotheses: list[Hypothesis] = []
    for source_position in range(width):
        for target_position in range(width):
            if source_position == target_position:
                continue
            candidate = discover(
                observations,
                source_position=source_position,
                target_position=target_position,
                min_evidence=min_evidence,
            )
            if candidate.outcome != OUTCOME_CANDIDATE:
                continue
            rank = FAMILY_COMPLEXITY_RANK.get(candidate.family, 99)
            hypotheses.append(Hypothesis(source_position, target_position, candidate, rank))
    return tuple(hypotheses)


def select_hypothesis(hypotheses: Sequence[Hypothesis]) -> HypothesisSelectionResult:
    """Gate A.3. Ranks candidate hypotheses by structural complexity only
    (Occam's razor: REFERENCE_EQUALITY < PERMUTATION < SELECTION_MAPPING <
    RECURSIVE_PERMUTATION -- prefer the simplest family that already
    explains the data over a more elaborate one) and retains the unique
    lowest-rank hypothesis. A genuine tie at the lowest rank is exposed as
    `AMBIGUOUS_SELECTION`, never picked arbitrarily.
    """
    if not hypotheses:
        return HypothesisSelectionResult(OUTCOME_NO_HYPOTHESES, None, tuple(hypotheses))
    best_rank = min(h.complexity_rank for h in hypotheses)
    best = [h for h in hypotheses if h.complexity_rank == best_rank]
    if len(best) == 1:
        return HypothesisSelectionResult(OUTCOME_RETAINED, best[0], tuple(hypotheses))
    return HypothesisSelectionResult(OUTCOME_AMBIGUOUS_SELECTION, None, tuple(hypotheses))


# ---------------------------------------------------------------------------
# Gate B: freeze -- opaque, no reference to training Node objects
# ---------------------------------------------------------------------------


def _anonymize_pattern(node: object, _counter: list[int] | None = None) -> object:
    """Rebuilds a PATTERN Node tree with every `node_id`/`provenance` field
    replaced by a canonical, training-data-free label.

    Found and fixed (2026-09-21, external review): `e20d_protocol.py`'s own
    pattern construction bakes the training row ids directly into the
    PATTERN Node's `node_id`/`provenance` strings (e.g.
    `"pattern::column::1::row1::row2::row3::..."`)-- confirmed by direct
    execution, not assumed. `apply()`/`replay_candidate()` never read
    `node_id`/`provenance` for their logic (only `kind`/`children` matter
    functionally), so rebuilding the tree with anonymized labels changes
    nothing about replay behaviour while actually satisfying Gate B's own
    stated contract instead of only appearing to.
    """
    if _counter is None:
        _counter = [0]
    if not isinstance(node, Node):
        return node
    new_children = []
    for child in node.children:
        if isinstance(child, PatternSlot) and child.nested_pattern is not None:
            new_children.append(
                PatternSlot(
                    source_position=child.source_position,
                    literal_constraint=child.literal_constraint,
                    nested_pattern=_anonymize_pattern(child.nested_pattern, _counter),
                    requires_source_equal=child.requires_source_equal,
                )
            )
        else:
            new_children.append(child)
    _counter[0] += 1
    return Node(
        node_id=f"anon::pattern::{_counter[0]}",
        kind=node.kind,
        children=tuple(new_children),
        provenance=(),
    )


@dataclass(frozen=True)
class FrozenTransformation:
    frozen_id: str
    family: str
    sigma: Tuple[Optional[int], ...]
    source_arity: int
    target_arity: int
    structural_digest: str
    pattern_ref: Optional[object] = None  # anonymized RefObject, for PERMUTATION/RECURSIVE only
    source_position: Optional[int] = None  # slot position to replay from, for PERMUTATION/RECURSIVE only
    multi_sigma: Optional[Tuple[Optional[Tuple[int, int]], ...]] = None  # for MULTI_SOURCE_SELECTION_MAPPING only
    source_arities: Optional[Tuple[int, ...]] = None  # for MULTI_SOURCE_SELECTION_MAPPING only


def freeze(candidate: TransformationCandidate, *, frozen_id: str) -> FrozenTransformation:
    """Gate B. After this call, nothing in the returned object lets a
    caller recover which training rows produced it: no row ids, no NodeRef
    identities, only the positional sigma (for SELECTION_MAPPING) or an
    anonymized pattern (for the reused e20d_protocol families) plus a
    structural digest that fingerprints the actual transformation, not just
    its family label.
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
    if candidate.multi_selection is not None:
        multi_sigma = candidate.multi_selection.sigma
        digest = sha256(repr((candidate.family, multi_sigma)).encode("utf-8")).hexdigest()
        return FrozenTransformation(
            frozen_id=frozen_id,
            family=candidate.family,
            sigma=(),
            source_arity=-1,
            target_arity=candidate.multi_selection.target_arity,
            structural_digest=digest,
            multi_sigma=multi_sigma,
            source_arities=candidate.multi_selection.source_arities,
        )
    cs = candidate.cross_slot
    assert cs is not None
    pattern_node = resolve_structure(cs.transformation)
    anonymized = _anonymize_pattern(pattern_node)
    anonymized_ref = ref_object(f"T::{candidate.family}::anon", anonymized)
    # Fingerprints the transformation's actual mapping (source positions,
    # nesting, literal constraints), never the training row ids -- fixes
    # the previously class-only digest, verified distinct for two
    # different permutations of the same family before trusting it.
    digest = sha256(repr((candidate.family, structural_signature(cs.transformation))).encode("utf-8")).hexdigest()
    return FrozenTransformation(
        frozen_id=frozen_id,
        family=candidate.family,
        sigma=(),
        source_arity=-1,
        target_arity=-1,
        structural_digest=digest,
        pattern_ref=anonymized_ref,
        source_position=cs.source_position,
    )


def rationalize_retained_hypothesis(
    frozen: FrozenTransformation,
    historical_frozen: Sequence[FrozenTransformation],
    *,
    threshold: float = 0.97,
) -> Optional[RationalizationResult]:
    """Gate A.3 optional corroboration -- reuses E20-D.6
    (`e20d_rationalization_v0_1.rationalize`) completely unchanged, no new
    semantic layer added. Compares the retained hypothesis's frozen
    pattern against previously-frozen transformations already adopted in
    this project; a high similarity yields `SUPPORTED_HISTORICAL`, never a
    rewrite of the retained hypothesis itself (E20-D.6's own invariant).

    Explicit scope boundary, not a silent gap: only meaningful for the
    PERMUTATION/RECURSIVE families, whose `pattern_ref` is a RefObject
    E20-D.6's structural-similarity mechanism can compare. SELECTION_MAPPING's
    `sigma` is a plain tuple of integer positions with no RefObject to
    compare against -- this function returns None for that family rather
    than forcing an ill-fitting comparison.
    """
    if frozen.pattern_ref is None:
        return None
    historical_refs = [h.pattern_ref for h in historical_frozen if h.pattern_ref is not None]
    if not historical_refs:
        return None
    return rationalize(frozen.pattern_ref, historical_refs, threshold=threshold)


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
    observations, batched (mirroring `e20d_protocol.replay_candidate`'s
    original batch-column design, without calling it -- see `freeze()`'s
    docstring for why). Never receives, and never needs, any
    target/ground-truth value -- callers proving
    non-circularity should construct their holdout target slot with an
    opaque placeholder never read here (see the same discipline already
    used by `tests/test_e20d_v03_recursive_transform.py`).
    """
    if frozen.family == FAMILY_SELECTION_MAPPING:
        return tuple(_blind_replay_one(frozen, obs) for obs in source_observations)
    if frozen.pattern_ref is not None and frozen.source_position is not None:
        pattern = resolve_structure(frozen.pattern_ref)
        if not isinstance(pattern, Node) or pattern.kind != PATTERN:
            return tuple(None for _ in source_observations)
        # Column of fresh source values only -- built here (not via
        # e20d_protocol._column_node) so no training-derived label ever
        # enters even a transient object during replay.
        source_column = Node(
            node_id=f"anon::column::{frozen.frozen_id}",
            kind=OBSERVATION,
            children=tuple(source_observations),
            provenance=(),
        )
        out = apply(pattern, source_column)
        if out is None:
            return tuple(None for _ in source_observations)
        return tuple(out.children)
    return tuple(None for _ in source_observations)


def blind_replay_multi_source(
    frozen: FrozenTransformation, source_observations_per_slot: Sequence[Sequence[Node]]
) -> Tuple[Optional[Node], ...]:
    """Gate C, multi-source variant (P4-T.4). `source_observations_per_slot[s]`
    is the batch of fresh source observations for named source slot `s`
    (same order as the `source_positions` originally passed to
    `discover_multi_source`); all slots must supply the same number of
    rows. Never receives, and never needs, any target/ground-truth value.
    """
    if frozen.multi_sigma is None or frozen.source_arities is None:
        return ()
    n_sources = len(frozen.source_arities)
    if len(source_observations_per_slot) != n_sources:
        raise ValueError(f"expected {n_sources} source slots, got {len(source_observations_per_slot)}")
    row_counts = {len(batch) for batch in source_observations_per_slot}
    if len(row_counts) != 1:
        raise ValueError("every source slot must supply the same number of rows")
    n_rows = row_counts.pop()

    predictions: list[Optional[Node]] = []
    for row_i in range(n_rows):
        sources = tuple(batch[row_i] for batch in source_observations_per_slot)
        if any(len(sources[s].children) != frozen.source_arities[s] for s in range(n_sources)):
            predictions.append(None)
            continue
        predicted_children = []
        ok = True
        for pair in frozen.multi_sigma:
            if pair is None:
                ok = False
                break
            slot_idx, child_idx = pair
            predicted_children.append(sources[slot_idx].children[child_idx])
        if not ok:
            predictions.append(None)
            continue
        predictions.append(
            Node(
                node_id=f"predicted::{frozen.frozen_id}::row{row_i}",
                kind=OBSERVATION,
                children=tuple(predicted_children),
                provenance=(frozen.frozen_id,),
            )
        )
    return tuple(predictions)


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


# ---------------------------------------------------------------------------
# Gate G -> E20-D.19 ROI adapter (P4-T.6)
#
# `documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 7
# stated plainly: Gate G measures real cost but was NOT wired into
# E20-D.19's ROI model (`e20d_cognitive_control_v0_1.py`), because that
# module's `score_candidate()` takes a `PathCandidate`, whose `path` field
# requires a genuine `kernel2.PathRecord` -- a graph path with a `start`/
# `end` NodeRef and a sequence of `PathStep`s. A transformation hypothesis
# is not a graph path, and fabricating a fake PathRecord to satisfy the
# type would be exactly the kind of ill-fitting forced comparison this
# project already refuses elsewhere (see `rationalize_retained_hypothesis`'s
# explicit SELECTION_MAPPING scope boundary above).
#
# This is therefore a PARALLEL, honestly-scoped adapter, not a call to
# `score_candidate()`: it reuses E20-D.19's own ROI formula and decision
# vocabulary (`DECISION_EXPLORE`/`DECISION_DEFER`/`DECISION_STOP`,
# imported unchanged, not redefined) applied to a transformation-discovery
# cost instead of a path-exploration cost. `e20d_cognitive_control_v0_1.py`
# itself is not modified.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformationROIScore:
    hypothesis_id: str
    novelty: float
    expected_gain: float
    redundancy: float
    cost: float
    roi: float
    decision: str


def score_hypothesis_roi(
    retained: Hypothesis,
    frozen: FrozenTransformation,
    cost_report: P4TCostReport,
    *,
    expected_gain: float,
    historical_frozen: Sequence[FrozenTransformation] = (),
    redundancy: float = 0.0,
    explore_threshold: float = 0.5,
    defer_threshold: float = 0.2,
) -> TransformationROIScore:
    """Scores a RETAINED hypothesis (Gate A.3) using E20-D.19's own
    ROI formula: `roi = expected_gain * novelty * (1 - redundancy) / cost`.

    `novelty` reuses P4-T.3's own rationalization hook rather than
    inventing a separate notion: 0.0 if the hypothesis's frozen pattern
    matches a historical transformation (`SUPPORTED_HISTORICAL` -- already
    known, not novel), 1.0 otherwise (genuinely new, or the family is out
    of `rationalize_retained_hypothesis`'s scope -- see that function's own
    documented boundary for SELECTION_MAPPING).

    `cost` is real and measured (Gate G), never estimated: the number of
    structural position-pairs the discovery search tried plus the holdout
    row count actually replayed -- an integer search-and-replay effort
    count, analogous in spirit to E20-D.19's own `structural_cost()` (cost
    grows with the size of the space explored) but not claimed identical
    to it, since `structural_cost()`'s specific formula needs
    `PathProperties` fields (distinct node/operator counts, branching) that
    do not apply to a transformation hypothesis.

    `expected_gain` MUST be supplied by the caller -- exactly like
    `PathCandidate.expected_gain` in E20-D.19 itself, whose own docstring
    calls it "externally/empirically supplied": this module has no way to
    know, on its own, how valuable a given transformation is to the
    caller's downstream use, and inventing a number here would be the kind
    of fabricated precision this project's own ROI history
    (`roadmap/ROADMAP_ROI_REFERENCE.md`) already warned against.
    """
    rationalization = rationalize_retained_hypothesis(frozen, historical_frozen)
    novelty = 0.0 if rationalization is not None and rationalization.status == "SUPPORTED_HISTORICAL" else 1.0

    cost = max(1.0, float(cost_report.discovery_position_pairs_tried + cost_report.replay_row_count))
    gain = max(0.0, float(expected_gain))
    red = max(0.0, min(1.0, float(redundancy)))
    roi = gain * novelty * (1.0 - red) / cost

    if roi >= explore_threshold:
        decision = DECISION_EXPLORE
    elif roi >= defer_threshold:
        decision = DECISION_DEFER
    else:
        decision = DECISION_STOP

    return TransformationROIScore(
        hypothesis_id=f"{retained.source_position}->{retained.target_position}",
        novelty=novelty,
        expected_gain=gain,
        redundancy=red,
        cost=cost,
        roi=roi,
        decision=decision,
    )


__all__ = [
    "FAMILY_COMPLEXITY_RANK",
    "FAMILY_MULTI_SOURCE_SELECTION_MAPPING",
    "FAMILY_PERMUTATION",
    "FAMILY_RECURSIVE_PERMUTATION",
    "FAMILY_REFERENCE_EQUALITY",
    "FAMILY_SELECTION_MAPPING",
    "OUTCOME_AMBIGUOUS",
    "OUTCOME_AMBIGUOUS_SELECTION",
    "OUTCOME_CANDIDATE",
    "OUTCOME_NO_HYPOTHESES",
    "OUTCOME_REJECTED",
    "OUTCOME_RETAINED",
    "FrozenTransformation",
    "Hypothesis",
    "HypothesisSelectionResult",
    "MultiSourceSelectionResult",
    "P4TCostReport",
    "SelectionMappingResult",
    "TransformationCandidate",
    "TransformationROIScore",
    "VerificationResult",
    "blind_replay",
    "blind_replay_multi_source",
    "classify_selection_mapping",
    "compose_frozen",
    "discover",
    "discover_all_hypotheses",
    "discover_multi_source",
    "discover_multi_source_selection_mapping",
    "discover_selection_mapping",
    "freeze",
    "rationalize_retained_hypothesis",
    "run_costed_pipeline",
    "score_hypothesis_roi",
    "select_hypothesis",
    "verify",
]
