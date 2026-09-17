"""MetaHIA E20-D.19 — structural exploration control by ROI.

Additive layer over the K3 kernel. It does not interpret semantic labels and
never decides whether a path/link is semantically meaningful. It ranks
structural candidates using structural cost, structural novelty, redundancy,
and an externally/empirically supplied expected epistemic gain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from kernel2 import PathProperties, PathRecord, path_properties, structural_equal


DECISION_EXPLORE = "EXPLORE"
DECISION_DEFER = "DEFER"
DECISION_STOP = "STOP"


@dataclass(frozen=True)
class PathCandidate:
    path: PathRecord
    structural_novelty: float
    expected_gain: float
    estimated_cost: float
    redundancy: float = 0.0


@dataclass(frozen=True)
class CognitiveScore:
    path_id: str
    novelty: float
    expected_gain: float
    redundancy: float
    cost: float
    roi: float
    decision: str
    provenance: Tuple[str, ...]


def _clip01(value: float) -> float:
    value = float(value)
    return max(0.0, min(1.0, value))


def structural_cost(props: PathProperties) -> float:
    """Purely structural exploration cost. Lower is cheaper."""
    cost = 1.0
    cost += float(props.length)
    cost += 0.5 * max(0, props.distinct_node_count - 1)
    cost += 0.75 * max(0, props.distinct_operator_count - 1)
    cost += 0.5 if props.reversed_traversal else 0.0
    cost += 0.5 * max(0, props.branching_at_start - 1)
    cost += 0.5 * max(0, props.branching_at_end - 1)
    return cost


def score_candidate(
    candidate: PathCandidate,
    *,
    explore_threshold: float = 0.5,
    defer_threshold: float = 0.2,
) -> CognitiveScore:
    """Score a candidate without semantic interpretation.

    ROI = expected_gain * novelty * (1 - redundancy) / cost.
    Decision uses only structural/epistemic-control signals and thresholds.
    """
    if explore_threshold < defer_threshold:
        raise ValueError("explore_threshold must be >= defer_threshold")
    novelty = _clip01(candidate.structural_novelty)
    gain = max(0.0, float(candidate.expected_gain))
    redundancy = _clip01(candidate.redundancy)
    cost = max(1e-9, float(candidate.estimated_cost))
    roi = gain * novelty * (1.0 - redundancy) / cost

    if roi >= explore_threshold:
        decision = DECISION_EXPLORE
    elif roi >= defer_threshold:
        decision = DECISION_DEFER
    else:
        decision = DECISION_STOP

    return CognitiveScore(
        path_id=candidate.path.path_id,
        novelty=novelty,
        expected_gain=gain,
        redundancy=redundancy,
        cost=cost,
        roi=roi,
        decision=decision,
        provenance=tuple(candidate.path.provenance),
    )


def path_redundancy(path: PathRecord, known_paths: Iterable[PathRecord]) -> float:
    """Return 1.0 for structural duplicate, 0.0 otherwise.

    The comparison deliberately ignores path identity/provenance and compares
    only the structural form. It does not inspect semantic labels.
    """
    target_props = path_properties(path)
    target_ops = target_props.operator_sequence
    target_dirs = target_props.direction_sequence
    target_binding = path.node_sequence

    for known in known_paths:
        known_props = path_properties(known)
        if (
            len(target_ops) == len(known_props.operator_sequence)
            and all(structural_equal(a, b) for a, b in zip(target_ops, known_props.operator_sequence))
            and target_dirs == known_props.direction_sequence
            and len(target_binding) == len(known.node_sequence)
            and all(a.ref_id == b.ref_id for a, b in zip(target_binding, known.node_sequence))
        ):
            return 1.0
    return 0.0


def build_candidate(
    path: PathRecord,
    *,
    expected_gain: float,
    structural_novelty: float,
    known_paths: Sequence[PathRecord] = (),
    estimated_cost: Optional[float] = None,
) -> PathCandidate:
    """Build a candidate using structural cost unless explicitly overridden."""
    props = path_properties(path)
    cost = structural_cost(props) if estimated_cost is None else float(estimated_cost)
    redundancy = path_redundancy(path, known_paths)
    return PathCandidate(
        path=path,
        structural_novelty=structural_novelty,
        expected_gain=expected_gain,
        estimated_cost=cost,
        redundancy=redundancy,
    )


def rank_candidates(
    candidates: Iterable[PathCandidate],
    *,
    explore_threshold: float = 0.5,
    defer_threshold: float = 0.2,
) -> Tuple[CognitiveScore, ...]:
    """Return candidates sorted by descending ROI; ties use path_id.

    No semantic tie-breaker is used.
    """
    scores = [
        score_candidate(
            candidate,
            explore_threshold=explore_threshold,
            defer_threshold=defer_threshold,
        )
        for candidate in candidates
    ]
    return tuple(sorted(scores, key=lambda s: (-s.roi, s.path_id)))


def select_reinjection_candidates(
    candidates: Iterable[PathCandidate],
    *,
    explore_threshold: float = 0.5,
    defer_threshold: float = 0.2,
) -> Tuple[CognitiveScore, ...]:
    """Return only candidates cognitively authorized for structural re-entry."""
    ranked = rank_candidates(
        candidates,
        explore_threshold=explore_threshold,
        defer_threshold=defer_threshold,
    )
    return tuple(item for item in ranked if item.decision == DECISION_EXPLORE)
