"""MetaHIA V10 -- P4-U.2 : Autonomous Structural Relation Discovery v0.1.

Implements the minimal module scoped in
`documentation/P4U2_Minimal_Implementation_Scope_V0_1.md` (revised
2026-09-24 after the project owner's review of commit 28ece87), which
formalizes what `documentation/P4U2_Protocol_V0_1.md` (frozen, f6a96b2)
and the calibration campaigns C1-C7
(`documentation/P4U2_Calibration_Experiment_2026-09-23.md` through
`documentation/P4U2_Calibration_Campaign7_VoletC_RealCorpus_2026-09-24.md`,
and Gate H's freeze in
`documentation/P4U2_Gate_H_V1_0_Frozen_2026-09-24.md`) established.

Reuses `kernel2.py`'s existing `build_structural_graph()` and
`discover_paths()` UNMODIFIED. No `e20d_*` file is reactivated. No
intelligent/semantic pool selection (deferred to unscoped "P4-U.2.2").
No end-to-end "run discovery on a graph" orchestration function is
provided here -- that responsibility belongs to a future locked-
benchmark runner, mirroring the existing separation between
`p4u1_unsupervised_pattern_discovery_v0_1.py` and
`p4u1_locked_benchmark_runner_v0_1.py`.

Deliberately excluded from this minimal module (scope doc Sec. 2.3),
not implemented "just in case":
  - Cohesion_A / Cohesion_C: never validated end-to-end by C1-C7, only
    Cohesion_B (`cohesion_b_mean_distance`) was used consistently
    across every calibration campaign.
  - The topology-only null model (protocol Sec. 9 piste 1): proven to
    produce a net false positive when used alone on a rigorously
    homogeneous corpus (campaign 5, TWIN). Not implemented at all here,
    to remove the risk of a future caller reactivating it by mistake.

Two gaps identified while scoping this module, neither closed by
calibration, both handled explicitly rather than silently:
  1. Gate I never had its own percentile threshold formally frozen
     (unlike Gate H) -- `evaluate_gate_i()`'s `percentile_threshold` is
     a mandatory keyword argument, never a silent default.
  2. No frozen document specifies how a candidate group is proposed
     BEFORE Gate I runs. `group_by_signature()` below is a NEW,
     uncalibrated design decision (exact full-signature equality,
     mirroring P4-U.1's own `group_by_skeleton()`) -- explicitly a
     CANDIDATE-GENERATION HEURISTIC, never a proof of identifiability
     by itself. Chaining `group_by_signature()` straight into
     `cohesion_b_mean_distance()` on the SAME signature would trivially
     force high internal cohesion by construction; Gate I's null
     comparison (never the raw cohesion in isolation) is what prevents
     this from being circular, but the future V1-V4 locked benchmark
     must still demonstrate this mechanism does not just turn its own
     candidate definition into a circular "discovery".
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from kernel2 import (
    GraphEdge,
    StructuralGraph,
    build_structural_graph,
    discover_paths,
)

# ---------------------------------------------------------------------------
# Signature (protocol Sec. 7) -- retained as a working hypothesis for this
# first locked benchmark, not a scientifically closed definition.
# ---------------------------------------------------------------------------

MAX_DEPTH = 3
MAX_PATHS = 1000


@dataclass(frozen=True)
class Signature:
    """Structural signature of one masked observation (edge), computed
    exclusively from `kernel2.discover_paths()` (UNCHANGED), filtered to
    paths whose first step is the edge itself."""
    depth1_count: int
    depth2_count: int
    depth3_count: int
    directions: frozenset


def edge_signature(graph: StructuralGraph, edge: GraphEdge, *, max_depth: int = MAX_DEPTH, max_paths: int = MAX_PATHS) -> Signature:
    paths = discover_paths(graph, start=edge.source, max_depth=max_depth, max_paths=max_paths)
    filtered = [p for p in paths if p.steps and p.steps[0].edge_id == edge.edge_id]
    d1 = sum(1 for p in filtered if p.length == 1)
    d2 = sum(1 for p in filtered if p.length == 2)
    d3 = sum(1 for p in filtered if p.length == 3)
    directions = frozenset(p.direction_sequence for p in filtered)
    return Signature(d1, d2, d3, directions)


def compute_signatures(observations, *, max_depth: int = MAX_DEPTH, max_paths: int = MAX_PATHS) -> Tuple[StructuralGraph, Tuple[Signature, ...]]:
    """Builds the structural graph and every edge's signature, in the
    same order as `graph.edges` -- the shared starting point for
    candidate generation, Gate I, and Gate H below."""
    graph = build_structural_graph(observations)
    sigs = tuple(edge_signature(graph, edge, max_depth=max_depth, max_paths=max_paths) for edge in graph.edges)
    return graph, sigs


# ---------------------------------------------------------------------------
# Candidate-group generation (scope doc Sec. 2.2, NEW -- a heuristic, never
# a proof of identifiability). Groups edges sharing an IDENTICAL signature.
# ---------------------------------------------------------------------------

def group_by_signature(sigs: Sequence[Signature]) -> Dict[Signature, Tuple[int, ...]]:
    """CANDIDATE-GENERATION HEURISTIC, not yet calibrated by C1-C7 (which
    always evaluated Gate I/Gate H on already-constructed groups with
    known ground truth). The most literal possible operationalization of
    cadrage v0.3's 'similarity -> common structure' step: no similarity
    threshold to invent, no clustering algorithm to calibrate. A false
    candidate (two genuinely different relations coincidentally sharing
    the same coarse signature, as in the TWIN case) is expected to be
    rejected by Gate I itself (INSUFFICIENT_STRUCTURAL_INFORMATION) --
    this function does not need to be infallible, only to propose."""
    groups: Dict[Signature, List[int]] = defaultdict(list)
    for idx, sig in enumerate(sigs):
        groups[sig].append(idx)
    return {sig: tuple(idxs) for sig, idxs in groups.items()}


# ---------------------------------------------------------------------------
# Cohesion (protocol Sec. 8, point 1) -- Cohesion_B only, the sole
# statistic validated end-to-end across campaigns C1-C7.
# ---------------------------------------------------------------------------

def _signature_distance(a: Signature, b: Signature) -> float:
    d2 = abs(a.depth2_count - b.depth2_count)
    d3 = abs(a.depth3_count - b.depth3_count)
    if not a.directions and not b.directions:
        jaccard = 1.0
    else:
        union = a.directions | b.directions
        inter = a.directions & b.directions
        jaccard = (len(inter) / len(union)) if union else 1.0
    return d2 + d3 + (1.0 - jaccard)


def cohesion_b_mean_distance(sigs: Sequence[Signature]) -> float:
    """Mean intra-group signature distance, converted to a cohesion score
    (higher = more cohesive) via 1 / (1 + mean_distance)."""
    n = len(sigs)
    if n < 2:
        return 1.0
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += _signature_distance(sigs[i], sigs[j])
            count += 1
    return 1.0 / (1.0 + total / count)


# ---------------------------------------------------------------------------
# Null model for Gate I (protocol Sec. 9, piste 2 -- CORRECTED per
# campaign 5: group-membership resampling on the fixed observed pool).
# Piste 1 (topology-only) is deliberately not implemented (see module
# docstring).
# ---------------------------------------------------------------------------

def null_resample_group(pool_sigs: Sequence[Signature], group_size: int, seed: int) -> Tuple[Signature, ...]:
    rng = random.Random(seed)
    return tuple(pool_sigs[i] for i in rng.sample(range(len(pool_sigs)), group_size))


def null_distribution(pool_sigs: Sequence[Signature], group_size: int, n_null: int, seed_base: int,
                       stat_fn: Callable[[Sequence[Signature]], float]) -> Tuple[float, ...]:
    return tuple(stat_fn(null_resample_group(pool_sigs, group_size, seed_base + i)) for i in range(n_null))


def percentile_rank(observed: float, null_values: Sequence[float]) -> float:
    """Mid-rank empirical percentile (0-1): (count_strictly_below +
    0.5*count_tied) / n -- a plain '<=' convention saturates at 100% on a
    degenerate tied null (found and fixed in campaign 1 Sec. 2.2)."""
    if not null_values:
        raise ValueError("percentile_rank requires at least one null value")
    below = sum(1 for v in null_values if v < observed)
    tied = sum(1 for v in null_values if v == observed)
    return (below + 0.5 * tied) / len(null_values)


def _percentile_value(values: Sequence[float], pct: float) -> float:
    """Nearest-rank percentile VALUE (a threshold), matching P4-U.1's own
    `percentile()` convention -- distinct from `percentile_rank`, which
    ranks an observed value within a distribution instead."""
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(pct / 100.0 * (len(ordered) - 1)))))
    return ordered[idx]


# ---------------------------------------------------------------------------
# Gate I -- Identifiability (protocol Sec. 8).
# ---------------------------------------------------------------------------

GATE_I_PASS = "PASS"
GATE_I_FAIL = "FAIL"


@dataclass(frozen=True)
class GateIResult:
    status: str
    observed_cohesion: float
    percentile: float
    n_null: int


def evaluate_gate_i(candidate_sigs: Sequence[Signature], pool_sigs: Sequence[Signature], *,
                     percentile_threshold: float, n_null: int, seed_base: int) -> GateIResult:
    """`percentile_threshold` is mandatory (scope doc Sec. 2.1): Gate I
    never had its own threshold formally frozen by calibration, unlike
    Gate H's -- no silent default is offered here to prevent one from
    being fixed by accident rather than by explicit decision."""
    if len(candidate_sigs) < 2:
        raise ValueError("Gate I requires a candidate group of at least 2 members")
    observed = cohesion_b_mean_distance(candidate_sigs)
    null_vals = null_distribution(pool_sigs, len(candidate_sigs), n_null, seed_base, cohesion_b_mean_distance)
    pct = percentile_rank(observed, null_vals) * 100.0
    status = GATE_I_PASS if pct >= percentile_threshold else GATE_I_FAIL
    return GateIResult(status=status, observed_cohesion=observed, percentile=pct, n_null=len(null_vals))


def gate_i_family_threshold(pool_sigs: Sequence[Signature], group_size: int, n_candidates: int,
                             n_null: int, percentile: float, seed_base: int) -> float:
    """Family-wise max-statistic null (protocol Sec. 8 point 3, same
    discipline as P4-U.1, demonstrated necessary by campaign 4 Part 3):
    for each replicate, draw `n_candidates` independent random groups
    from the pool and record the MAXIMUM cohesion across them. Returns
    the requested percentile VALUE of this max-statistic distribution --
    a single shared threshold to compare every simultaneously-tested
    candidate's own observed cohesion against, controlling the family-
    wise false-positive rate (never a per-candidate individual null when
    more than one candidate is tested at once)."""
    maxima = []
    for i in range(n_null):
        rng = random.Random(seed_base + i)
        best = 0.0
        for _ in range(n_candidates):
            idxs = rng.sample(range(len(pool_sigs)), group_size)
            best = max(best, cohesion_b_mean_distance([pool_sigs[j] for j in idxs]))
        maxima.append(best)
    return _percentile_value(maxima, percentile)


# ---------------------------------------------------------------------------
# Rule R1 + STRUCTURAL_CLASS_HYPOTHESIS (protocol Sec. 10.1).
# ---------------------------------------------------------------------------

HYPOTHESIS_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class StructuralClassHypothesis:
    """Mirrors `kernel2.Hypothesis`'s own status discipline: UNKNOWN by
    default, never SUPPORTED without independent validation (Gate I +
    Gate H), never a promoted 'relation' field on this same object (the
    hierarchy structure/hypothesis/relation, protocol Sec. 10, keeps a
    discovered relation as a SEPARATE interpretation object)."""
    hypothesis_id: str
    member_observation_ids: Tuple[str, ...]
    structural_signature: Signature
    support: int
    contradiction_support: float
    status: str = HYPOTHESIS_UNKNOWN
    provenance: Tuple[str, ...] = ()


def trait_vector(sig: Signature) -> Tuple[int, int]:
    return (1 if sig.depth2_count > 0 else 0, 1 if sig.depth3_count > 0 else 0)


def partition_by_majority_trait(sigs: Sequence[Signature]) -> Tuple[Tuple[int, int], Tuple[int, ...]]:
    """Rule R1 (campaign 4/5, pre-registered): deterministic majority
    vote over the ALREADY-FIXED trait vector (has_depth2, has_depth3) --
    never searched or optimized over alternative partitions. This is
    the specific protection against the circularity risk the project
    owner flagged in campaign 4: no partition other than this single,
    fixed rule is ever considered for the same group."""
    if not sigs:
        raise ValueError("partition_by_majority_trait requires at least one signature")
    vectors = [trait_vector(s) for s in sigs]
    dominant = Counter(vectors).most_common(1)[0][0]
    dissenting = tuple(i for i, v in enumerate(vectors) if v != dominant)
    return dominant, dissenting


def contradiction_support_v2(sigs: Sequence[Signature]) -> float:
    """Generalizes campaign 1/2's single-trait contradiction_support into
    a majority vote over the (has_depth2, has_depth3) trait VECTOR
    (campaign 4) -- needed because a manifest-heterogeneity scenario can
    dissent on has_depth3 while a noise scenario dissents on has_depth2."""
    _, dissenting = partition_by_majority_trait(sigs)
    return len(dissenting) / len(sigs)


# ---------------------------------------------------------------------------
# Gate H v1.0 -- FROZEN (documentation/P4U2_Gate_H_V1_0_Frozen_2026-09-24.md).
# An empirical operational calibration envelope, not a universal law.
# ---------------------------------------------------------------------------

GATE_H_PERCENTILE_THRESHOLD = 95.0
GATE_H_MIN_GROUP_SIZE = 20
GATE_H_MAX_GROUP_SIZE = 40
GATE_H_MIN_DISSENTING_COUNT = 8

GATE_H_PASS = "PASS"
GATE_H_FAIL = "FAIL"
GATE_H_CALIBRATION_INSUFFICIENT = "CALIBRATION_INSUFFICIENT"


@dataclass(frozen=True)
class GateHResult:
    status: str
    dissenting_count: int
    minority_cohesion: Optional[float]
    percentile: Optional[float]
    envelope_ok: bool


def evaluate_gate_h(candidate_sigs: Sequence[Signature], pool_sigs: Sequence[Signature], *,
                     n_null: int, seed_base: int) -> GateHResult:
    """`n_null` is mandatory (scope doc correction after 28ece87): Gate H
    v1.0 froze percentile>=95%, the k>=8/group_size-in-[20,40] envelope,
    and CALIBRATION_INSUFFICIENT outside it -- it never froze N_null as
    a normative constant (only 'confirmed stable' empirically at 200-300
    during calibration, campaign 2 Part 2C). No silent default is
    offered here, matching Gate I's own `percentile_threshold`.

    A group with zero dissenting members (Rule R1 finds no disagreement
    at all) is PASS immediately -- there is no contradiction to test,
    so no null comparison and no envelope check applies. Otherwise, the
    group must be inside the calibrated envelope (group_size in
    [20,40] AND dissenting_count >= 8) before any percentile is
    computed; outside it, the result is CALIBRATION_INSUFFICIENT,
    never PASS, never FAIL, never silently defaulted either way.

    The null itself reproduces the FULL selection procedure (campaign
    5's fix for campaign 4's flawed shortcut null): each replicate draws
    a same-size null group from the pool and applies Rule R1 to it,
    using whatever majority/dissident split emerges naturally -- never a
    null that resamples a pre-sized dissident subset directly.
    """
    group_size = len(candidate_sigs)
    dominant, dissenting = partition_by_majority_trait(candidate_sigs)
    dissenting_count = len(dissenting)

    if dissenting_count == 0:
        return GateHResult(status=GATE_H_PASS, dissenting_count=0, minority_cohesion=None, percentile=None, envelope_ok=True)

    envelope_ok = (GATE_H_MIN_GROUP_SIZE <= group_size <= GATE_H_MAX_GROUP_SIZE) and (dissenting_count >= GATE_H_MIN_DISSENTING_COUNT)
    if not envelope_ok:
        return GateHResult(status=GATE_H_CALIBRATION_INSUFFICIENT, dissenting_count=dissenting_count,
                            minority_cohesion=None, percentile=None, envelope_ok=False)

    minority_sigs = [candidate_sigs[i] for i in dissenting]
    observed_cohesion = cohesion_b_mean_distance(minority_sigs)

    null_vals: List[float] = []
    n_pool = len(pool_sigs)
    for i in range(n_null):
        rng = random.Random(seed_base + i)
        idxs = rng.sample(range(n_pool), group_size)
        null_group = [pool_sigs[j] for j in idxs]
        _, null_dissenting = partition_by_majority_trait(null_group)
        if len(null_dissenting) >= 2:
            null_vals.append(cohesion_b_mean_distance([null_group[j] for j in null_dissenting]))

    if not null_vals:
        return GateHResult(status=GATE_H_CALIBRATION_INSUFFICIENT, dissenting_count=dissenting_count,
                            minority_cohesion=observed_cohesion, percentile=None, envelope_ok=True)

    pct = percentile_rank(observed_cohesion, null_vals) * 100.0
    status = GATE_H_PASS if pct >= GATE_H_PERCENTILE_THRESHOLD else GATE_H_FAIL
    return GateHResult(status=status, dissenting_count=dissenting_count, minority_cohesion=observed_cohesion,
                        percentile=pct, envelope_ok=True)
