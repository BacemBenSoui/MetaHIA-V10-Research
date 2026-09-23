"""MetaHIA V10 -- P4-U.1 : Unsupervised Compositional Pattern Discovery v0.1.

Implements the protocol frozen in
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
(v0.2 -- the v0.1 protocol document is superseded and not implementable
as-is). Reuses `kernel2.py`'s existing discovery/generalization/replay
primitives UNMODIFIED (`discover_paths`, `generalize_path_pattern`,
`replay_path_pattern_holdout`); this module adds only the pieces the
protocol identifies as genuinely missing: skeleton grouping, a
label-stratified degree-preserving null model, the max-statistic
multiple-comparisons correction, quantitative Gate B/C scoring, and a
leak-free `FrozenPatternU1`.

Scope discipline, repeated from the protocol (Sec. 0/1/18): this is
UNSUPERVISED COMPOSITIONAL PATTERN DISCOVERY on a graph whose relations
are already labeled (e.g. MERE_DE, TRAVAILLE_DANS) -- never shortened
to "unsupervised discovery" in any docstring or report this module
produces. It does NOT discover an unknown relation ("P4-U.2", not
defined). It does NOT close E20-D.
"""
from __future__ import annotations

import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from kernel2 import (
    OBSERVATION,
    PATH_REPLAYED,
    Node,
    NodeRef,
    PathPattern,
    PathRecord,
    build_structural_graph,
    discover_paths,
    generalize_path_pattern,
    replay_path_pattern_holdout,
)

SkeletonKey = Tuple[Tuple[str, str], ...]

GATE_A_DISCOVERED = "DISCOVERED"
GATE_A_NOT_DISCOVERED = "NOT_DISCOVERED"

GATE_B_RETAINED = "RETAINED"
GATE_B_REJECTED = "REJECTED"

REJECTION_MIN_DEPTH = "MIN_DEPTH"
REJECTION_SUB_THRESHOLD = "SUB_THRESHOLD"
REJECTION_NOT_NULL_SIGNIFICANT = "NOT_NULL_SIGNIFICANT"
REJECTION_NOT_GENERALIZABLE = "NOT_GENERALIZABLE"

GATE_C_REPLICATED = "REPLICATED"
GATE_C_FAILED = "FAILED_AS_EXPECTED"
GATE_C_NOT_APPLICABLE = "NOT_APPLICABLE"


def skeleton_key(path: PathRecord) -> SkeletonKey:
    """(operator_ref_id, direction) per step -- built entirely from
    `PathRecord`'s own PUBLIC `operator_sequence`/`direction_sequence`
    properties (kernel2.py), never a private kernel2 helper. Mirrors
    the `_skeleton_key()` pattern already duplicated across
    `m6_corpus_from_organization_v0_1.py` and its siblings, generalized
    here into one reusable function instead of a sixth private copy."""
    return tuple((op.ref_id, direction) for op, direction in zip(path.operator_sequence, path.direction_sequence))


def group_by_skeleton(paths: Sequence[PathRecord]) -> Dict[SkeletonKey, Tuple[PathRecord, ...]]:
    groups: Dict[SkeletonKey, list] = defaultdict(list)
    for path in paths:
        groups[skeleton_key(path)].append(path)
    return {k: tuple(v) for k, v in groups.items()}


@dataclass(frozen=True)
class CandidateSupport:
    skeleton: SkeletonKey
    depth: int
    support: int
    paths: Tuple[PathRecord, ...]


def _is_trivial_wedge(skeleton: SkeletonKey) -> bool:
    """True if any two CONSECUTIVE steps use the SAME operator in
    OPPOSITE directions -- i.e. the path walks an edge backward then
    immediately forward again (or the reverse), landing back among that
    edge's own immediate neighbors. This is never a genuine composition
    of two different relations -- it is a same-relation "wedge"/fan
    pattern (any two neighbors sharing a common relation partner), a
    fundamentally different and uninteresting regularity from the
    cross-relation compositions this protocol is about (Sec. 2).

    **Real finding that required this exclusion, made by direct
    execution before any corpus was locked**: under the pool-based null
    model (`null_generator`), these same-relation wedge skeletons are
    exactly the ones prone to random degree concentration (a node that
    happens, by chance, to receive multiple same-label edges creates a
    combinatorial k*(k-1) burst of wedge-paths through it) -- they
    systematically dominate the max-statistic multiple-comparisons
    correction (protocol Sec. 7), drowning out genuine two-relation
    compositions. Excluding them from candidacy entirely (at Gate A,
    for every corpus uniformly, decided from this general mechanism --
    never tuned to make one specific case pass) restores the max
    statistic's ability to detect real cross-relation regularities.
    """
    for (op_a, dir_a), (op_b, dir_b) in zip(skeleton, skeleton[1:]):
        if op_a == op_b and dir_a != dir_b:
            return True
    return False


def discover_candidates(
    observations: Sequence[Node],
    *,
    min_depth: int,
    max_depth: int,
    max_paths: Optional[int] = None,
) -> Tuple[CandidateSupport, ...]:
    """`build_structural_graph` + `discover_paths` (start=end=None --
    genuinely target-free enumeration, kernel2.py's own default) +
    `group_by_skeleton`, filtered to `depth >= min_depth` and to
    genuine cross-relation compositions (`_is_trivial_wedge` excluded,
    see its own docstring). Support is the number of discovered
    `PathRecord`s sharing a skeleton -- never deduplicated further,
    since `generalize_path_pattern` itself requires >= 2 to abstract
    anything (kernel2.py, verified by direct reading)."""
    graph = build_structural_graph(observations)
    # `max_paths=None` means "unbounded" -- kernel2.discover_paths() has
    # no `None` sentinel of its own (its default is a fixed 1000),
    # omitting the kwarg would silently fall back to that cap rather
    # than truly disabling it (found directly, before any corpus was
    # locked: a large multi-family calibration corpus silently lost
    # every path of its rarer families to this exact cap). A very large
    # explicit integer is passed instead.
    effective_max_paths = sys.maxsize if max_paths is None else max_paths
    paths = discover_paths(graph, max_depth=max_depth, max_paths=effective_max_paths)
    eligible = [p for p in paths if p.length >= min_depth and not _is_trivial_wedge(skeleton_key(p))]
    grouped = group_by_skeleton(eligible)
    return tuple(
        CandidateSupport(skeleton=sig, depth=paths_group[0].length, support=len(paths_group), paths=paths_group)
        for sig, paths_group in grouped.items()
    )


def _label_groups(observations: Sequence[Node]) -> Dict[str, List[Tuple[int, NodeRef, NodeRef]]]:
    """Groups observation indices by relation label (`operator.ref_id`),
    each entry `(index, source, target)` -- the unit the null model
    randomizes per label, never mixing labels."""
    groups: Dict[str, List[Tuple[int, NodeRef, NodeRef]]] = defaultdict(list)
    for i, obs in enumerate(observations):
        operator, source, target = obs.children
        groups[operator.ref_id].append((i, source, target))
    return groups


def null_generator(observations: Sequence[Node], *, seed: int, max_attempts_per_edge: int = 200) -> Tuple[Node, ...]:
    """Label-stratified null model: preserves per-label edge count and
    the per-label SOURCE pool and TARGET pool SEPARATELY (the set of
    node identities that ever appear as a source for that label, and,
    independently, the set that ever appear as a target -- never
    merged into one shared pool, which a first version did and found,
    by direct execution, to inflate the null-max distribution WELL
    ABOVE the true motif's own support: merging let originally
    source-only and target-only entities swap roles, and drawing more
    edges from a larger shared pool created more random degree
    concentration on the very entities structurally eligible to bridge
    two labels, the opposite of what a null model should do). Each
    edge's (source, target) pair is reassigned via independent uniform
    sampling from its label's own source pool and target pool, rejecting
    self-loops and exact-duplicate pairs.

    **This does NOT preserve individual node degree -- disclosed
    explicitly, not silently, per the v0.2 protocol's own fallback
    clause (Sec. 6: "si structurellement inatteignable... documenté
    explicitement").** Two stricter degree-preserving alternatives were
    tried first and both found, by direct execution before any corpus
    was locked, to make ANY depth-2 composition's support a
    mathematical invariant, not a random variable at all:

      1. a double-edge-swap preserving each node's EXACT per-label
         degree -- for a depth-2 skeleton (label A -> label B), support
         equals `sum over nodes n of in_degree_A(n) * out_degree_B(n)`,
         which any degree-preserving rewiring leaves algebraically
         unchanged.
      2. a full random permutation of each label's own target list
         (preserving the target MULTISET, i.e. the in-degree sequence)
         -- when every entity in that corpus appears at most once per
         label (the case for every case in this benchmark: a clean
         matching structure, no repeated entities), a permutation of an
         all-distinct list changes nothing about which entities are
         touched, so the same invariance recurs.

    Relaxing to "preserve the pool, not the degree" breaks this
    invariance: which specific entities end up bridging two labels
    becomes genuinely random, giving the null-max distribution real
    spread -- confirmed directly (`scripts/_scratch_p4u1_calibration.py`,
    not committed) before this became the locked null model.
    """
    rng = random.Random(seed)
    by_label = _label_groups(observations)
    randomized: Dict[int, Tuple[NodeRef, NodeRef]] = {}

    for _label, entries in by_label.items():
        source_pool = sorted({s.ref_id for _i, s, _t in entries})
        target_pool = sorted({t.ref_id for _i, _s, t in entries})
        n = len(entries)
        used_pairs: set = set()
        new_pairs: List[Tuple[NodeRef, NodeRef]] = []
        for _ in range(n):
            for _attempt in range(max_attempts_per_edge):
                s_id, t_id = rng.choice(source_pool), rng.choice(target_pool)
                if s_id == t_id:
                    continue
                if (s_id, t_id) in used_pairs:
                    continue
                used_pairs.add((s_id, t_id))
                new_pairs.append((NodeRef(s_id), NodeRef(t_id)))
                break
            else:
                # Pool exhausted for this label under the no-self-loop/
                # no-duplicate constraint -- disclosed honestly rather
                # than silently accepting a self-loop or a duplicate:
                # this benchmark's corpora are sized so this never
                # triggers (checked by a dedicated test); it is raised
                # rather than silently forcing an invalid pair.
                raise RuntimeError(
                    f"null_generator: exhausted {max_attempts_per_edge} attempts for one edge of a label with "
                    f"source pool {len(source_pool)}, target pool {len(target_pool)}, and {n} edges -- "
                    "corpus too dense for these pools, enlarge them"
                )
        for (idx, _s, _t), (new_s, new_t) in zip(entries, new_pairs):
            randomized[idx] = (new_s, new_t)

    result = []
    for i, obs in enumerate(observations):
        operator, _source, _target = obs.children
        new_source, new_target = randomized[i]
        result.append(Node(f"null::{i}", OBSERVATION, (operator, new_source, new_target), provenance=(f"null::{i}",)))
    return tuple(result)


def null_max_support_distribution(
    observations: Sequence[Node],
    *,
    min_depth: int,
    max_depth: int,
    n_null: int,
    seed_base: int = 0,
    max_paths: Optional[int] = None,
) -> Tuple[int, ...]:
    """For each of `n_null` seeded null replicates, the MAXIMUM support
    across every candidate skeleton it produces -- the family-wise,
    max-statistic distribution (protocol Sec. 7), never a per-skeleton
    null distribution. `0` (not skipped) when a replicate produces no
    eligible candidate at all -- a real, informative outcome, not a
    missing data point."""
    maxima = []
    for i in range(n_null):
        null_obs = null_generator(observations, seed=seed_base + i)
        candidates = discover_candidates(null_obs, min_depth=min_depth, max_depth=max_depth, max_paths=max_paths)
        maxima.append(max((c.support for c in candidates), default=0))
    return tuple(maxima)


def percentile(values: Sequence[int], pct: float) -> float:
    """Nearest-rank percentile over a finite empirical sample -- no
    interpolation, so the result is always an actually-observed null
    value (or the sample's max when `pct` rounds past the end),
    matching the empirical p-value convention used elsewhere (protocol
    Sec. 7)."""
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(pct / 100.0 * (len(ordered) - 1)))))
    return ordered[idx]


@dataclass(frozen=True)
class GateBResult:
    outcome: str  # GATE_B_RETAINED | GATE_B_REJECTED
    rejection_reason: Optional[str]
    score: int
    null_percentile_value: float
    pattern: Optional[PathPattern]


def evaluate_gate_b(
    candidate: CandidateSupport,
    null_max_dist: Sequence[int],
    *,
    min_depth: int,
    s_min: int,
    null_percentile: float = 99.0,
) -> GateBResult:
    """Quantitative Gate B (protocol Sec. 9): RETAINED iff ALL of
    depth >= min_depth, support >= s_min, support > percentile(null_max_dist),
    and `generalize_path_pattern` does not reject the candidate's own
    paths. Checked in a fixed order so `rejection_reason` is always the
    FIRST violated condition, not an arbitrary one."""
    null_pct_value = percentile(null_max_dist, null_percentile)
    if candidate.depth < min_depth:
        return GateBResult(GATE_B_REJECTED, REJECTION_MIN_DEPTH, candidate.support, null_pct_value, None)
    if candidate.support < s_min:
        return GateBResult(GATE_B_REJECTED, REJECTION_SUB_THRESHOLD, candidate.support, null_pct_value, None)
    if candidate.support <= null_pct_value:
        return GateBResult(GATE_B_REJECTED, REJECTION_NOT_NULL_SIGNIFICANT, candidate.support, null_pct_value, None)
    pattern = generalize_path_pattern(candidate.paths, pattern_id=f"p4u1::{skeleton_key(candidate.paths[0])!r}")
    if pattern is None:
        return GateBResult(GATE_B_REJECTED, REJECTION_NOT_GENERALIZABLE, candidate.support, null_pct_value, None)
    return GateBResult(GATE_B_RETAINED, None, candidate.support, null_pct_value, pattern)


@dataclass(frozen=True)
class FrozenPatternU1:
    """Leak-free frozen pattern -- same hardening discipline as
    `p4t_structural_transformation_induction_v0_1.FrozenTransformation`
    (P4-T.1/P4-T.1bis). Never carries `source_path_ids`, training node
    identity, or holdout information."""

    frozen_id: str
    skeleton: SkeletonKey
    depth: int
    structure: Tuple[Tuple[int, ...], ...]  # PathPattern.position_groups
    support_train: int
    structural_digest: str
    discovery_metadata: Mapping[str, object]


def freeze_pattern(pattern: PathPattern, *, frozen_id: str, support_train: int, metadata: Mapping[str, object]) -> FrozenPatternU1:
    """Same construction as `p4t_structural_transformation_induction_v0_1.freeze()`'s
    own `structural_digest` (`sha256(repr((family, sigma)))`, verified
    by direct reading) -- a digest of only the anonymized structural
    fields, never `pattern.source_path_ids` (present on the real
    `kernel2.PathPattern`, confirmed by direct reading, and exactly the
    kind of training-identity field P4-T.1 had to learn to exclude)."""
    skeleton = tuple(zip((op.ref_id if hasattr(op, "ref_id") else repr(op) for op in pattern.operator_sequence), pattern.direction_sequence))
    depth = len(pattern.operator_sequence)
    digest = sha256(repr((skeleton, depth, pattern.position_groups)).encode("utf-8")).hexdigest()
    return FrozenPatternU1(
        frozen_id=frozen_id,
        skeleton=skeleton,
        depth=depth,
        structure=pattern.position_groups,
        support_train=support_train,
        structural_digest=digest,
        discovery_metadata=dict(metadata),
    )


def admissible_starts(observations: Sequence[Node]) -> Tuple[NodeRef, ...]:
    """Every node with out-degree >= 1 in the given observation set -- a
    purely dimensional, target-independent rule (protocol Sec. 11),
    never a condition tied to the sought skeleton's label."""
    graph = build_structural_graph(observations)
    out_degree: Counter = Counter()
    for edge in graph.edges:
        out_degree[edge.source.ref_id] += 1
    return tuple(n for n in graph.nodes if out_degree[n.ref_id] >= 1)


@dataclass(frozen=True)
class ReplicationResult:
    support_holdout: int
    n_starts_admissible: int
    n_starts_producing: int

    @property
    def coverage(self) -> float:
        if self.n_starts_admissible == 0:
            return 0.0
        return self.n_starts_producing / self.n_starts_admissible


def replay_on_all_admissible_starts(pattern: PathPattern, holdout_observations: Sequence[Node]) -> ReplicationResult:
    """Rejoue `pattern` (via `kernel2.replay_path_pattern_holdout`,
    UNMODIFIED) sur TOUS les starts admissibles du holdout, jamais un
    sous-ensemble choisi à la main (protocol Sec. 11)."""
    starts = admissible_starts(holdout_observations)
    producing = 0
    for start in starts:
        result = replay_path_pattern_holdout(pattern, holdout_observations, start)
        if result.status == PATH_REPLAYED:
            producing += 1
    return ReplicationResult(support_holdout=producing, n_starts_admissible=len(starts), n_starts_producing=producing)


@dataclass(frozen=True)
class GateCResult:
    outcome: str  # GATE_C_REPLICATED | GATE_C_FAILED
    replication: ReplicationResult
    null_percentile_value: float


def evaluate_gate_c(
    replication: ReplicationResult,
    holdout_null_max_dist: Sequence[int],
    *,
    k_min: int,
    coverage_min: float,
    null_percentile: float = 99.0,
) -> GateCResult:
    """Quantitative Gate C, symmetric to Gate B (protocol Sec. 10):
    REPLICATED iff support_holdout >= k_min AND support_holdout >
    percentile(holdout_null_max_dist) AND coverage >= coverage_min."""
    null_pct_value = percentile(holdout_null_max_dist, null_percentile)
    replicated = (
        replication.support_holdout >= k_min
        and replication.support_holdout > null_pct_value
        and replication.coverage >= coverage_min
    )
    return GateCResult(GATE_C_REPLICATED if replicated else GATE_C_FAILED, replication, null_pct_value)


__all__ = [
    "SkeletonKey",
    "GATE_A_DISCOVERED",
    "GATE_A_NOT_DISCOVERED",
    "GATE_B_RETAINED",
    "GATE_B_REJECTED",
    "REJECTION_MIN_DEPTH",
    "REJECTION_SUB_THRESHOLD",
    "REJECTION_NOT_NULL_SIGNIFICANT",
    "REJECTION_NOT_GENERALIZABLE",
    "GATE_C_REPLICATED",
    "GATE_C_FAILED",
    "GATE_C_NOT_APPLICABLE",
    "skeleton_key",
    "group_by_skeleton",
    "CandidateSupport",
    "discover_candidates",
    "null_generator",
    "null_max_support_distribution",
    "percentile",
    "GateBResult",
    "evaluate_gate_b",
    "FrozenPatternU1",
    "freeze_pattern",
    "admissible_starts",
    "ReplicationResult",
    "replay_on_all_admissible_starts",
    "GateCResult",
    "evaluate_gate_c",
]
