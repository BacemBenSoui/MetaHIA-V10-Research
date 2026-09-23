"""Permanent invariant tests for P4-U.1 -- Unsupervised Compositional
Pattern Discovery v0.1 (`p4u1_unsupervised_pattern_discovery_v0_1.py`).

Uses small, hand-constructed observation sets throughout -- no
dependency on the real locked benchmark corpus (not yet written). Every
mechanism required by
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
is checked here on deterministic, controlled data before any real
corpus is trusted.
"""
from __future__ import annotations

import dataclasses

import pytest

from kernel2 import OBSERVATION, Node, node_ref
from p4u1_unsupervised_pattern_discovery_v0_1 import (
    REJECTION_MIN_DEPTH,
    REJECTION_NOT_NULL_SIGNIFICANT,
    REJECTION_SUB_THRESHOLD,
    GATE_B_RETAINED,
    GATE_C_FAILED,
    GATE_C_REPLICATED,
    CandidateSupport,
    admissible_starts,
    discover_candidates,
    evaluate_gate_b,
    evaluate_gate_c,
    freeze_pattern,
    group_by_skeleton,
    null_generator,
    null_max_support_distribution,
    percentile,
    replay_on_all_admissible_starts,
    skeleton_key,
)


def _obs(fact_id: str, rel: str, subj: str, obj: str) -> Node:
    return Node(fact_id, OBSERVATION, (node_ref(rel), node_ref(subj), node_ref(obj)))


def _forward_candidate(candidates, rel_a="REL_A", rel_b="REL_B"):
    """Selects the FORWARD/FORWARD skeleton -- discover_paths()'s own
    documented allow_reverse=True default (kernel2.py) also returns the
    reverse-traversal mirror as a second, genuinely distinct depth-2
    skeleton (found directly, not assumed, before trusting any test
    against it): tests must never assume depth alone identifies a
    unique candidate."""
    return next(c for c in candidates if c.skeleton == ((rel_a, "FORWARD"), (rel_b, "FORWARD")))


# ---------------------------------------------------------------------------
# 1. skeleton_key / group_by_skeleton / discover_candidates.
# ---------------------------------------------------------------------------


def test_skeleton_key_and_discover_candidates_find_a_depth_2_composition():
    """A --REL_A--> B --REL_B--> C, repeated for 3 independent triples,
    must be discovered as a depth-2 candidate with support 3 -- forward
    and its reverse-traversal mirror both appear (discover_paths()'s
    own documented allow_reverse=True default, kernel2.py, unmodified
    here), each a genuinely distinct skeleton, so both are expected,
    not just one."""
    observations = []
    for i in range(3):
        observations.append(_obs(f"a{i}", "REL_A", f"A{i}", f"B{i}"))
        observations.append(_obs(f"b{i}", "REL_B", f"B{i}", f"C{i}"))
    candidates = discover_candidates(tuple(observations), min_depth=2, max_depth=3)
    depth2 = [c for c in candidates if c.depth == 2]
    assert len(depth2) == 2
    forward = next(c for c in depth2 if c.skeleton == (("REL_A", "FORWARD"), ("REL_B", "FORWARD")))
    reverse = next(c for c in depth2 if c.skeleton == (("REL_B", "REVERSE"), ("REL_A", "REVERSE")))
    assert forward.support == 3
    assert reverse.support == 3


def test_discover_candidates_filters_out_depth_below_min_depth():
    observations = [_obs(f"a{i}", "REL_A", f"A{i}", f"B{i}") for i in range(5)]
    candidates_min1 = discover_candidates(tuple(observations), min_depth=1, max_depth=3)
    candidates_min2 = discover_candidates(tuple(observations), min_depth=2, max_depth=3)
    assert any(c.depth == 1 for c in candidates_min1)
    assert not any(c.depth < 2 for c in candidates_min2)


def test_discover_candidates_excludes_trivial_same_relation_wedges():
    """A --REL_A--> B <--REL_A-- A2 (two sources sharing the same
    target via the SAME relation) produces a real depth-2 path
    (REL_A FORWARD, REL_A REVERSE) that walks the SAME relation
    backward then forward -- never a genuine two-relation composition,
    and must be excluded from candidacy entirely (found to dominate
    the null-max statistic otherwise; see `_is_trivial_wedge`'s own
    docstring)."""
    observations = [
        _obs("a1", "REL_A", "S1", "T"),
        _obs("a2", "REL_A", "S2", "T"),
    ]
    candidates = discover_candidates(tuple(observations), min_depth=2, max_depth=2)
    assert not any(c.skeleton == (("REL_A", "FORWARD"), ("REL_A", "REVERSE")) for c in candidates)
    assert not any(c.skeleton == (("REL_A", "REVERSE"), ("REL_A", "FORWARD")) for c in candidates)


def test_discover_candidates_keeps_genuine_two_relation_reverse_traversal():
    """The mirror of a genuine composition (different operators, one
    step reversed relative to the other) is NOT a trivial wedge and
    must still be discovered -- the filter targets same-operator
    reversal specifically, not reversal in general."""
    observations = [_obs("a", "REL_A", "A0", "B0"), _obs("b", "REL_B", "B0", "C0")]
    candidates = discover_candidates(tuple(observations), min_depth=2, max_depth=2)
    skeletons = {c.skeleton for c in candidates}
    assert (("REL_B", "REVERSE"), ("REL_A", "REVERSE")) in skeletons


def test_group_by_skeleton_separates_distinct_skeletons():
    observations = []
    for i in range(3):
        observations.append(_obs(f"a{i}", "REL_A", f"A{i}", f"B{i}"))
        observations.append(_obs(f"b{i}", "REL_B", f"B{i}", f"C{i}"))
    for i in range(2):
        observations.append(_obs(f"x{i}", "REL_X", f"X{i}", f"Y{i}"))
        observations.append(_obs(f"y{i}", "REL_Y", f"Y{i}", f"Z{i}"))
    candidates = discover_candidates(tuple(observations), min_depth=2, max_depth=2)
    skeletons = {c.skeleton for c in candidates}
    assert (("REL_A", "FORWARD"), ("REL_B", "FORWARD")) in skeletons
    assert (("REL_X", "FORWARD"), ("REL_Y", "FORWARD")) in skeletons


# ---------------------------------------------------------------------------
# 2. null_generator -- degree-preserving, label-stratified, deterministic.
# ---------------------------------------------------------------------------


def _build_corpus(n=12):
    observations = []
    for i in range(n):
        observations.append(_obs(f"a{i}", "REL_A", f"A{i}", f"B{i}"))
        observations.append(_obs(f"b{i}", "REL_B", f"B{i}", f"C{i}"))
    return tuple(observations)


def test_null_generator_preserves_node_and_edge_counts_per_label():
    observations = _build_corpus()
    null_obs = null_generator(observations, seed=0)
    assert len(null_obs) == len(observations)

    def label_counts(obs_seq):
        counts = {}
        for o in obs_seq:
            rel = o.children[0].ref_id
            counts[rel] = counts.get(rel, 0) + 1
        return counts

    assert label_counts(null_obs) == label_counts(observations)


def test_null_generator_never_introduces_an_entity_outside_the_original_pool():
    """Deliberately weaker guarantee than exact per-node degree
    preservation (see the module's own docstring for why: exact degree
    preservation makes any depth-2 composition's support a mathematical
    invariant, found by direct execution, not a design preference). Not
    every original entity is guaranteed to be reused (independent
    sampling can skip one by chance), but no entity outside the
    original per-label pool can ever appear."""
    observations = _build_corpus()
    null_obs = null_generator(observations, seed=1)

    def pool_by_label(obs_seq):
        pools: dict = {}
        for o in obs_seq:
            rel, source, target = o.children
            pools.setdefault(rel.ref_id, set()).update({source.ref_id, target.ref_id})
        return pools

    original_pools = pool_by_label(observations)
    null_pools = pool_by_label(null_obs)
    assert set(null_pools.keys()) == set(original_pools.keys())
    for label, entities in null_pools.items():
        assert entities <= original_pools[label]


def test_null_generator_is_deterministic_per_seed():
    observations = _build_corpus()
    null_a = null_generator(observations, seed=42)
    null_b = null_generator(observations, seed=42)
    pairs_a = [(o.children[1].ref_id, o.children[2].ref_id) for o in null_a]
    pairs_b = [(o.children[1].ref_id, o.children[2].ref_id) for o in null_b]
    assert pairs_a == pairs_b


def test_null_generator_actually_changes_the_edge_arrangement():
    observations = _build_corpus(n=20)
    null_obs = null_generator(observations, seed=7)
    original_pairs = [(o.children[1].ref_id, o.children[2].ref_id) for o in observations]
    null_pairs = [(o.children[1].ref_id, o.children[2].ref_id) for o in null_obs]
    assert original_pairs != null_pairs


def test_null_generator_never_creates_a_self_loop():
    observations = _build_corpus(n=20)
    for seed in range(5):
        null_obs = null_generator(observations, seed=seed)
        for o in null_obs:
            _rel, source, target = o.children
            assert source.ref_id != target.ref_id


# ---------------------------------------------------------------------------
# 3. null_max_support_distribution / percentile.
# ---------------------------------------------------------------------------


def test_null_max_support_distribution_has_the_right_length_and_is_non_negative():
    observations = _build_corpus(n=10)
    dist = null_max_support_distribution(observations, min_depth=2, max_depth=2, n_null=15, seed_base=0)
    assert len(dist) == 15
    assert all(v >= 0 for v in dist)


def test_percentile_is_nearest_rank_no_interpolation():
    values = [10, 20, 30, 40, 50]
    assert percentile(values, 0.0) == 10
    assert percentile(values, 100.0) == 50
    assert percentile(values, 50.0) in values  # nearest-rank, not an interpolated 30.0-only guarantee, but must be a real observed value


def test_percentile_rejects_an_empty_sample():
    with pytest.raises(ValueError):
        percentile([], 99.0)


# ---------------------------------------------------------------------------
# 4. evaluate_gate_b -- quantitative, ordered rejection reasons.
# ---------------------------------------------------------------------------


def _candidate(skeleton, depth, support, paths=()):
    return CandidateSupport(skeleton=skeleton, depth=depth, support=support, paths=paths)


def test_gate_b_rejects_below_min_depth_even_with_high_support():
    candidate = _candidate((("REL_A", "FORWARD"),), depth=1, support=1000)
    result = evaluate_gate_b(candidate, null_max_dist=(1, 2, 3), min_depth=2, s_min=1)
    assert result.outcome != GATE_B_RETAINED
    assert result.rejection_reason == REJECTION_MIN_DEPTH


def test_gate_b_rejects_below_s_min():
    candidate = _candidate((("REL_A", "FORWARD"), ("REL_B", "FORWARD")), depth=2, support=2)
    result = evaluate_gate_b(candidate, null_max_dist=(0, 0, 0), min_depth=2, s_min=5)
    assert result.rejection_reason == REJECTION_SUB_THRESHOLD


def test_gate_b_rejects_not_null_significant():
    candidate = _candidate((("REL_A", "FORWARD"), ("REL_B", "FORWARD")), depth=2, support=5)
    result = evaluate_gate_b(candidate, null_max_dist=(10, 10, 10), min_depth=2, s_min=1)
    assert result.rejection_reason == REJECTION_NOT_NULL_SIGNIFICANT


def test_gate_b_retains_a_genuinely_strong_candidate_and_returns_a_real_pattern():
    observations = _build_corpus(n=6)
    candidates = discover_candidates(observations, min_depth=2, max_depth=2)
    candidate = _forward_candidate(candidates)
    result = evaluate_gate_b(candidate, null_max_dist=(0, 1, 1, 2), min_depth=2, s_min=2)
    assert result.outcome == GATE_B_RETAINED
    assert result.rejection_reason is None
    assert result.pattern is not None


# ---------------------------------------------------------------------------
# 5. freeze_pattern -- leak-free, deterministic digest.
# ---------------------------------------------------------------------------


def test_freeze_pattern_never_carries_training_identity_fields():
    observations = _build_corpus(n=6)
    candidates = discover_candidates(observations, min_depth=2, max_depth=2)
    candidate = _forward_candidate(candidates)
    result = evaluate_gate_b(candidate, null_max_dist=(0,), min_depth=2, s_min=2)
    frozen = freeze_pattern(result.pattern, frozen_id="test", support_train=candidate.support, metadata={})
    field_names = {f.name for f in dataclasses.fields(frozen)}
    assert "source_path_ids" not in field_names
    assert "node_id" not in field_names
    assert "holdout" not in " ".join(field_names).lower()


def test_freeze_pattern_digest_is_deterministic_and_skeleton_specific():
    observations = _build_corpus(n=6)
    candidates = discover_candidates(observations, min_depth=2, max_depth=2)
    candidate = _forward_candidate(candidates)
    result = evaluate_gate_b(candidate, null_max_dist=(0,), min_depth=2, s_min=2)
    frozen_a = freeze_pattern(result.pattern, frozen_id="a", support_train=candidate.support, metadata={})
    frozen_b = freeze_pattern(result.pattern, frozen_id="b", support_train=candidate.support, metadata={})
    assert frozen_a.structural_digest == frozen_b.structural_digest  # same pattern -> same digest, frozen_id irrelevant

    other_observations = []
    for i in range(6):
        other_observations.append(_obs(f"x{i}", "REL_X", f"X{i}", f"Y{i}"))
        other_observations.append(_obs(f"y{i}", "REL_Y", f"Y{i}", f"Z{i}"))
    other_candidates = discover_candidates(tuple(other_observations), min_depth=2, max_depth=2)
    other_candidate = _forward_candidate(other_candidates, rel_a="REL_X", rel_b="REL_Y")
    other_result = evaluate_gate_b(other_candidate, null_max_dist=(0,), min_depth=2, s_min=2)
    frozen_other = freeze_pattern(other_result.pattern, frozen_id="c", support_train=other_candidate.support, metadata={})
    assert frozen_other.structural_digest != frozen_a.structural_digest


# ---------------------------------------------------------------------------
# 6. admissible_starts / replay_on_all_admissible_starts / evaluate_gate_c.
# ---------------------------------------------------------------------------


def test_admissible_starts_excludes_dead_end_nodes():
    observations = [_obs("a", "REL_A", "SOURCE", "SINK")]
    starts = admissible_starts(observations)
    ref_ids = {n.ref_id for n in starts}
    assert "SOURCE" in ref_ids
    assert "SINK" not in ref_ids  # SINK has no outgoing edge


def test_replay_on_all_admissible_starts_computes_real_coverage():
    train = _build_corpus(n=6)
    candidates = discover_candidates(train, min_depth=2, max_depth=2)
    candidate = _forward_candidate(candidates)
    gate_b = evaluate_gate_b(candidate, null_max_dist=(0,), min_depth=2, s_min=2)
    assert gate_b.outcome == GATE_B_RETAINED

    # Holdout: 3 fresh entities replicate the pattern, 2 do not (dead-end after step 1).
    holdout = []
    for i in range(3):
        holdout.append(_obs(f"ha{i}", "REL_A", f"HA{i}", f"HB{i}"))
        holdout.append(_obs(f"hb{i}", "REL_B", f"HB{i}", f"HC{i}"))
    for i in range(3, 5):
        holdout.append(_obs(f"ha{i}", "REL_A", f"HA{i}", f"HB{i}"))  # no REL_B continuation

    replication = replay_on_all_admissible_starts(gate_b.pattern, tuple(holdout))
    assert replication.support_holdout == 3
    # Admissible = every node with an outgoing edge: HA0-4 (5, all have a REL_A
    # edge) PLUS HB0-2 (3, each still has its own outgoing REL_B edge, even
    # though replaying the 2-hop pattern FROM a mid-chain node never
    # reproduces it) = 8 -- found by direct execution, not assumed in advance.
    assert replication.n_starts_admissible == 8
    assert replication.coverage == pytest.approx(3 / 8)


def test_gate_c_replicated_only_when_all_three_conditions_hold():
    from p4u1_unsupervised_pattern_discovery_v0_1 import ReplicationResult

    strong = ReplicationResult(support_holdout=10, n_starts_admissible=10, n_starts_producing=10)
    result = evaluate_gate_c(strong, holdout_null_max_dist=(1, 2, 3), k_min=2, coverage_min=0.5)
    assert result.outcome == GATE_C_REPLICATED

    weak_support = ReplicationResult(support_holdout=1, n_starts_admissible=10, n_starts_producing=1)
    result = evaluate_gate_c(weak_support, holdout_null_max_dist=(1, 2, 3), k_min=2, coverage_min=0.05)
    assert result.outcome == GATE_C_FAILED  # below k_min

    not_null_significant = ReplicationResult(support_holdout=5, n_starts_admissible=10, n_starts_producing=5)
    result = evaluate_gate_c(not_null_significant, holdout_null_max_dist=(5, 5, 5), k_min=2, coverage_min=0.1)
    assert result.outcome == GATE_C_FAILED  # not above null percentile

    low_coverage = ReplicationResult(support_holdout=10, n_starts_admissible=100, n_starts_producing=10)
    result = evaluate_gate_c(low_coverage, holdout_null_max_dist=(1,), k_min=2, coverage_min=0.5)
    assert result.outcome == GATE_C_FAILED  # coverage 0.1 < 0.5
