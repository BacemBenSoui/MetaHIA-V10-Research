"""MetaHIA V10 -- P4-U.1 : set-valued holdout replay adapter (v0.1).

Implements Gate C exactly as redefined by
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
Sec. 10, following the project owner's own resolution of the Gate B /
Gate C tension found while calibrating v0.2
(`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
Sec. 20): `REPLICATED(start)` is an EXISTENCE property -- at least one
admissible holdout path from `start` whose structural skeleton AND
co-reference structure match a frozen pattern -- never a UNIQUENESS
property. This is a deliberate divergence from
`kernel2.replay_path_pattern_holdout()`'s own semantics
(`max_candidates_per_step=1` by default: a node with more than one
valid continuation at some step returns `AMBIGUOUS`, treated by v0.2
as a failure). A hub node with several valid continuations is not
necessarily an epistemic failure -- it can be a genuine one-to-many
relation in the graph, and Gate B (unchanged, see the core module) is
what already requires such concentration to be statistically
significant in the first place.

`kernel2.py` IS NOT MODIFIED BY THIS MODULE. This is a parallel
adapter that reuses `kernel2.discover_paths()` and `reference_equal()`
UNMODIFIED to enumerate candidate continuations from a given start and
check their structural compatibility with a `FrozenPatternU1`; it
never touches `kernel2.replay_path_pattern()` /
`replay_path_pattern_holdout()`, which remain available, unmodified,
as an optional secondary diagnostic (`legacy_unique_replay_status`,
Sec. 10.3) -- never the primary Gate C criterion.

Anti-circularity (protocol Sec. 10.5), never to be violated: every
function in this module decides compatibility PURELY from a frozen
pattern's own `skeleton`/`structure` fields and the holdout graph
itself -- none of them accept, and must never be made to accept, a
witness, an expected label, or any other ground-truth hint to pick a
branch. The witness may only score this module's REPLICATED/FAILED
output after it has been produced, exactly as for P4-T.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from kernel2 import (
    Node,
    NodeRef,
    PathPattern,
    PathRecord,
    build_structural_graph,
    discover_paths,
    reference_equal,
    replay_path_pattern_holdout,
)
from p4u1_unsupervised_pattern_discovery_v0_1 import (
    FrozenPatternU1,
    admissible_starts,
    skeleton_key,
)

REPLAY_NO_PATH = "NO_PATH"
REPLAY_ONE_PATH = "ONE_PATH"
REPLAY_MULTI_PATH = "MULTI_PATH"

GATE_C_REPLICATED = "REPLICATED"
GATE_C_FAILED = "FAILED"


def _position_groups_satisfied(path: PathRecord, position_groups: Sequence[Sequence[int]]) -> bool:
    """True iff every group of positions recorded in a frozen pattern's
    `structure` (`PathPattern.position_groups`, Sec. 12) is actually
    co-referent (same `NodeRef`, via `kernel2.reference_equal`) along
    THIS ONE concrete path's `node_sequence`. A group of size < 2 is
    not a constraint (a position with no proven co-reference partner)
    and always trivially holds -- mirrors
    `generalize_path_pattern()`'s own intersection semantics, applied
    here to verify a single candidate against an already-frozen
    partition instead of deriving one from several examples."""
    nodes = path.node_sequence
    for group in position_groups:
        if len(group) < 2:
            continue
        anchor = nodes[group[0]]
        if not all(reference_equal(anchor, nodes[pos]) for pos in group[1:]):
            return False
    return True


def skeleton_matching_paths_from_start(
    pattern: FrozenPatternU1,
    holdout_observations: Sequence[Node],
    start: NodeRef,
    *,
    max_paths: Optional[int] = None,
) -> Tuple[PathRecord, ...]:
    """Every `PathRecord` of EXACTLY `pattern.depth` from `start` in the
    holdout graph whose operator/direction skeleton equals
    `pattern.skeleton` -- BEFORE checking co-reference structure. This
    is the set that decides `NO_PATH` / `ONE_PATH` / `MULTI_PATH`
    (protocol Sec. 10.6: "exactement une continuation admissible,
    COMPATIBLE OU NON" -- deliberately not yet filtered by
    `_position_groups_satisfied`). Reuses `kernel2.discover_paths()`
    UNMODIFIED, exactly as the core module's `discover_candidates`
    does on the train side."""
    graph = build_structural_graph(holdout_observations)
    effective_max_paths = sys.maxsize if max_paths is None else max_paths
    candidates = discover_paths(
        graph, start=start, max_depth=pattern.depth, allow_reverse=True, max_paths=effective_max_paths
    )
    return tuple(p for p in candidates if p.length == pattern.depth and skeleton_key(p) == pattern.skeleton)


def compatible_paths_from_start(
    pattern: FrozenPatternU1,
    holdout_observations: Sequence[Node],
    start: NodeRef,
    *,
    max_paths: Optional[int] = None,
) -> Tuple[PathRecord, ...]:
    """Subset of `skeleton_matching_paths_from_start` that also
    satisfies `pattern.structure` (`_position_groups_satisfied`) --
    the set whose non-emptiness defines `REPLICATED(start)` (Sec. 10.2)."""
    matches = skeleton_matching_paths_from_start(pattern, holdout_observations, start, max_paths=max_paths)
    return tuple(p for p in matches if _position_groups_satisfied(p, pattern.structure))


@dataclass(frozen=True)
class SetValuedReplayResult:
    """Per-start result of the set-valued replay (Sec. 10.2/10.6).

    `replay_status` is the diagnostic branching classification over
    ALL skeleton-matching continuations (compatible or not);
    `replicated` is the actual Gate C existence decision, computed
    only from `compatible_paths`. The two are deliberately independent:
    `MULTI_PATH` does not imply `replicated=True` (several branches can
    all fail the co-reference structure), and `ONE_PATH` does not imply
    `replicated=False` (a single branch can be the correct one)."""

    start: NodeRef
    replay_status: str  # NO_PATH | ONE_PATH | MULTI_PATH
    replicated: bool
    skeleton_matching_paths: Tuple[PathRecord, ...]
    compatible_paths: Tuple[PathRecord, ...]

    @property
    def n_valid_continuations(self) -> int:
        return len(self.compatible_paths)


def replay_set_valued(
    pattern: FrozenPatternU1,
    holdout_observations: Sequence[Node],
    start: NodeRef,
    *,
    max_paths: Optional[int] = None,
) -> SetValuedReplayResult:
    """The per-start set-valued replay decision (Sec. 10.2): existence
    of at least one compatible continuation, never uniqueness. Decided
    purely from `pattern` and `holdout_observations` -- no witness, no
    expected label, nothing beyond the frozen structural pattern and
    the holdout graph itself (Sec. 10.5)."""
    matches = skeleton_matching_paths_from_start(pattern, holdout_observations, start, max_paths=max_paths)
    compatible = tuple(p for p in matches if _position_groups_satisfied(p, pattern.structure))
    if not matches:
        status = REPLAY_NO_PATH
    elif len(matches) == 1:
        status = REPLAY_ONE_PATH
    else:
        status = REPLAY_MULTI_PATH
    return SetValuedReplayResult(
        start=start,
        replay_status=status,
        replicated=bool(compatible),
        skeleton_matching_paths=matches,
        compatible_paths=compatible,
    )


@dataclass(frozen=True)
class SetValuedReplicationResult:
    """Aggregate over every admissible start (Sec. 11, redefined)."""

    per_start: Tuple[SetValuedReplayResult, ...]

    @property
    def n_starts_admissible(self) -> int:
        return len(self.per_start)

    @property
    def support_holdout(self) -> int:
        """Number of starts for which `REPLICATED(start)` holds --
        the existence-based statistic that replaces the old
        uniqueness-based `support_holdout` (Sec. 10.2)."""
        return sum(1 for r in self.per_start if r.replicated)

    @property
    def coverage(self) -> float:
        """Redefined coverage (Sec. 11): starts for which at least one
        admissible trajectory matches the FrozenPattern, divided by all
        admissible starts -- existence-based, not uniqueness-based."""
        if not self.per_start:
            return 0.0
        return self.support_holdout / self.n_starts_admissible

    @property
    def mean_valid_continuations_per_replicating_start(self) -> Optional[float]:
        """New diagnostic (Sec. 11): average, over REPLICATED starts
        ONLY, of the number of compatible continuations found from that
        start. `None` when no start replicated (undefined, not zero --
        there is nothing to average). A high value alongside high
        coverage is the expected signature of a genuinely concentrated
        ("hub") structure; a value near 1 alongside high coverage would
        instead look like a flat, one-to-one structure."""
        replicating_counts = [r.n_valid_continuations for r in self.per_start if r.replicated]
        if not replicating_counts:
            return None
        return sum(replicating_counts) / len(replicating_counts)


def replay_on_all_admissible_starts_set_valued(
    pattern: FrozenPatternU1,
    holdout_observations: Sequence[Node],
    *,
    max_paths: Optional[int] = None,
) -> SetValuedReplicationResult:
    """Rejoue `pattern` (set-valued, Sec. 10.2) sur TOUS les starts
    admissibles du holdout (`admissible_starts`, core module,
    UNMODIFIED, Sec. 11) -- jamais un sous-ensemble choisi à la main."""
    starts = admissible_starts(holdout_observations)
    results = tuple(
        replay_set_valued(pattern, holdout_observations, start, max_paths=max_paths) for start in starts
    )
    return SetValuedReplicationResult(per_start=results)


@dataclass(frozen=True)
class GateCResultSetValued:
    outcome: str  # GATE_C_REPLICATED | GATE_C_FAILED
    replication: SetValuedReplicationResult
    null_percentile_value: float


def evaluate_gate_c_set_valued(
    replication: SetValuedReplicationResult,
    holdout_null_max_dist: Sequence[int],
    *,
    k_min: int,
    coverage_min: float,
    null_percentile: float = 99.0,
) -> GateCResultSetValued:
    """Quantitative Gate C (protocol v0.3 Sec. 10.2), same three
    conditions as v0.2's Gate C and the same form as `evaluate_gate_c`
    in the core module -- only the underlying statistic changed, from
    uniqueness-based to existence-based `support_holdout`/`coverage`.
    `holdout_null_max_dist` is produced the same way as before, by
    `null_max_support_distribution` (core module) applied to
    `G_holdout` -- a discovery-style statistic, unrelated to replay,
    unchanged by this module."""
    from p4u1_unsupervised_pattern_discovery_v0_1 import percentile as _percentile

    null_pct_value = _percentile(holdout_null_max_dist, null_percentile)
    replicated = (
        replication.support_holdout >= k_min
        and replication.support_holdout > null_pct_value
        and replication.coverage >= coverage_min
    )
    return GateCResultSetValued(GATE_C_REPLICATED if replicated else GATE_C_FAILED, replication, null_pct_value)


def legacy_unique_replay_status(pattern: PathPattern, holdout_observations: Sequence[Node], start: NodeRef) -> str:
    """Secondary diagnostic only (Sec. 10.3): the ORIGINAL,
    unmodified `kernel2.replay_path_pattern_holdout()` uniqueness-based
    status (`REPLAYED` / `NOT_FOUND` / `AMBIGUOUS`) for the same
    `start`. Requires the LIVE `PathPattern` (with real operator
    objects), not a leak-free `FrozenPatternU1` -- unlike every other
    function in this module, which decides Gate C from the frozen
    pattern alone. Never used to decide `REPLICATED`/`FAILED`; recorded
    purely so a runner can compare, per start, how the new
    existence-based decision diverges from the old uniqueness-based
    one (exactly the divergence that motivated this module)."""
    return replay_path_pattern_holdout(pattern, holdout_observations, start).status


__all__ = [
    "REPLAY_NO_PATH",
    "REPLAY_ONE_PATH",
    "REPLAY_MULTI_PATH",
    "GATE_C_REPLICATED",
    "GATE_C_FAILED",
    "skeleton_matching_paths_from_start",
    "compatible_paths_from_start",
    "SetValuedReplayResult",
    "replay_set_valued",
    "SetValuedReplicationResult",
    "replay_on_all_admissible_starts_set_valued",
    "GateCResultSetValued",
    "evaluate_gate_c_set_valued",
    "legacy_unique_replay_status",
]
