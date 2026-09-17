"""MetaHIA E20-D — executable cross-slot discovery protocol v0.2.

Scope deliberately demonstrated by this executable protocol:
  * enumerate ordered (source_position, target_position) pairs;
  * represent each column only through structural NodeRef objects;
  * detect exact structural dependency (same reference at source/target
    positions across all evidence rows);
  * detect a position permutation between source and target columns through
    the existing generic Compare mechanism;
  * represent the discovered transformation as a RefObject;
  * preserve provenance and fail closed on ambiguity.

This is intentionally NOT a general function-learner. With finite opaque
atoms, arbitrary source->target functions are not uniquely identifiable.
E20-D therefore exposes what is structurally identified and records what is
not, rather than using semantic fallbacks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from kernel2 import (
    Node, NodeRef, RefObject, PatternRef, OBSERVATION, PATTERN,
    compare, compare_candidates, structural_equal,
    reference_equal, ref_object, resolve_structure, compare_pattern_references,
)


@dataclass(frozen=True)
class ProjectedColumn:
    position: int
    node: Node
    row_ids: Tuple[str, ...]


@dataclass(frozen=True)
class CrossSlotCandidate:
    source_position: int
    target_position: int
    transformation: RefObject
    relation_kind: str
    evidence_rows: Tuple[str, ...]
    source_target_provenance: Tuple[str, ...]


@dataclass(frozen=True)
class CrossSlotDiscovery:
    candidates: Tuple[CrossSlotCandidate, ...]
    ambiguous_pairs: Tuple[Tuple[int, int, Tuple[str, ...]], ...]
    rejected_pairs: Tuple[Tuple[int, int, str], ...]


def compare_discovered_transformations(a: CrossSlotCandidate, b: CrossSlotCandidate) -> Optional[bool]:
    """Compare two E20-D transformations through the unified PatternRef API.

    True  = same structural transformation, even with different internal
            PATTERN/SHAPE_PATTERN representations.
    False = both are structurally comparable but represent different maps.
    None  = the representations cannot yet be compared without loss.
    Reference identity is never used as a substitute for structural equality.
    """
    return compare_pattern_references(a.transformation, b.transformation)


def _column_node(observations: Sequence[Node], position: int) -> Node:
    """Create a structural column vector while preserving NodeRef identity."""
    return Node(
        node_id=f"column::{position}::" + "::".join(obs.node_id for obs in observations),
        kind=OBSERVATION,
        children=tuple(obs.children[position] for obs in observations),
        provenance=tuple(
            f"{obs.node_id}:pos:{position}" for obs in observations
        ),
    )


def _same_reference_column(
    observations: Sequence[Node], source_position: int, target_position: int
) -> bool:
    """True only when every row carries the same NodeRef object identity in
    source and target. Raw values never establish this dependency."""
    for obs in observations:
        a = obs.children[source_position]
        b = obs.children[target_position]
        if not (isinstance(a, NodeRef) and isinstance(b, NodeRef)):
            return False
        if not reference_equal(a, b):
            return False
    return True


def _discover_permutation(
    observations: Sequence[Node], source_position: int, target_position: int
) -> Optional[Node]:
    """Use the existing generic Compare to detect a permutation between the
    source and target columns. The output Pattern is a transformation over
    row positions, not a semantic function over payload values."""
    source = _column_node(observations, source_position)
    target = _column_node(observations, target_position)
    candidates = compare_candidates(source, target)
    if len(candidates) != 1:
        return None
    return candidates[0]


def _classify_compare_pattern(pattern: Node) -> str:
    """Classify a generic Compare result without semantic interpretation.

    A flat PATTERN is a positional transformation. A PATTERN containing one
    or more nested_pattern components is a recursively discovered structural
    transformation. The distinction is descriptive only; both remain the
    same kernel PATTERN representation and can be applied by the same Apply
    entry point.
    """
    if pattern.kind != PATTERN:
        return "COMPARE_OTHER"
    has_nested = any(
        isinstance(slot, object) and getattr(slot, "nested_pattern", None) is not None
        for slot in pattern.children
    )
    return "COMPARE_RECURSIVE" if has_nested else "COMPARE_PERMUTATION"


def discover_cross_slot_candidates(
    observations: Sequence[Node], *, min_evidence: int = 3
) -> CrossSlotDiscovery:
    """Enumerate every ordered source/target slot pair.

    Priority is structural identity first, then generic Compare-based
    permutation. No payload equality, semantic dictionary, or domain-specific
    transformation detector is used.
    """
    if len(observations) < min_evidence:
        raise ValueError(f"E20-D requires at least {min_evidence} observations")
    if not observations:
        return CrossSlotDiscovery((), (), ())
    width = len(observations[0].children)
    if any(obs.kind != OBSERVATION or len(obs.children) != width for obs in observations):
        raise ValueError("all observations must be OBSERVATION nodes with equal arity")

    candidates: List[CrossSlotCandidate] = []
    ambiguous: List[Tuple[int, int, Tuple[str, ...]]] = []
    rejected: List[Tuple[int, int, str]] = []

    for source in range(width):
        for target in range(width):
            if source == target:
                continue
            evidence_rows = tuple(obs.node_id for obs in observations)
            provenance = tuple(
                f"{obs.node_id}:pos{source}->pos{target}" for obs in observations
            )

            if _same_reference_column(observations, source, target):
                transformation = ref_object(
                    f"T::REF_EQ::{source}->{target}",
                    Node(
                        node_id=f"ref_equal::{source}->{target}",
                        kind=PATTERN,
                        children=tuple(),
                        provenance=provenance,
                    ),
                )
                candidates.append(
                    CrossSlotCandidate(
                        source, target, transformation, "REFERENCE_EQUALITY",
                        evidence_rows, provenance,
                    )
                )
                continue

            pattern = _discover_permutation(observations, source, target)
            if pattern is not None:
                transformation = ref_object(
                    f"T::PERM::{source}->{target}", pattern
                )
                candidates.append(
                    CrossSlotCandidate(
                        source, target, transformation, _classify_compare_pattern(pattern),
                        evidence_rows, provenance,
                    )
                )
            else:
                # Probe ambiguity explicitly using all candidates so the
                # protocol distinguishes "not identified" from "ambiguous".
                src = _column_node(observations, source)
                dst = _column_node(observations, target)
                cs = compare_candidates(src, dst)
                if len(cs) > 1:
                    ambiguous.append((source, target, evidence_rows))
                else:
                    rejected.append((source, target, "no generic structural transformation identified"))

    return CrossSlotDiscovery(tuple(candidates), tuple(ambiguous), tuple(rejected))


def replay_candidate(candidate: CrossSlotCandidate, observations: Sequence[Node]) -> Optional[Node]:
    """Replay a Compare-discovered permutation on a fresh source column.

    REFERENCE_EQUALITY candidates are a structural dependency certificate, not
    a Pattern that the current Apply implementation can execute; those are
    returned as None deliberately rather than being converted into a hidden
    special-case operation.
    """
    if candidate.relation_kind not in ("COMPARE_PERMUTATION", "COMPARE_RECURSIVE"):
        return None
    from kernel2 import apply
    pattern = resolve_structure(candidate.transformation)
    if not isinstance(pattern, Node) or pattern.kind != PATTERN:
        return None
    source_column = _column_node(observations, candidate.source_position)
    return apply(pattern, source_column)
