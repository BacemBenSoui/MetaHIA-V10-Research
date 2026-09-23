"""Permanent invariant tests for the P4-U.1 set-valued replay adapter
(`p4u1_set_valued_replay_v0_1.py`), implementing Gate C exactly as
redefined by
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
Sec. 10.

The central scenario in this file (`test_hub_with_multiple_valid_...`)
is the concrete demonstration that this module resolves the Gate B /
Gate C tension documented in
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
Sec. 20: a hub node with several valid continuations, which
`kernel2.replay_path_pattern_holdout()` (unmodified) always reports as
`AMBIGUOUS`, is correctly recognized as `REPLICATED` here -- decided
purely structurally, never by consulting which branch is "the right
one" (Sec. 10.5).

**Real finding recorded while writing these tests, not assumed in
advance**: `kernel2.discover_paths()`'s own no-revisit-within-a-path
invariant (a node already visited earlier in the same path is never
stepped into again -- kernel2.py's own `walk()`, confirmed by direct
reading) means every `PathRecord` it ever returns has pairwise DISTINCT
positions in its `node_sequence`. Consequently `generalize_path_pattern()`'s
`position_groups` (Sec. 12's `structure` field) is always the trivial
all-singleton partition for any candidate reached through the standard
discovery pipeline -- `_position_groups_satisfied` is exercised as a
real, uniformly-applied check (never skipped, since `PathPattern.position_groups`
is a general field this adapter must not silently ignore), but it is a
no-op in practice today. `test_position_groups_satisfied_...` below
tests its logic directly on hand-built `PathRecord` objects (which,
unlike `discover_paths()`'s own output, CAN carry a repeated position),
precisely to keep this check honestly verified even though the current
pipeline can never trigger its rejecting branch.
"""
from __future__ import annotations

import inspect

import pytest

from kernel2 import OBSERVATION, Node, NodeRef, PathRecord, PathStep, node_ref
from p4u1_unsupervised_pattern_discovery_v0_1 import (
    FrozenPatternU1,
    discover_candidates,
    evaluate_gate_b,
    freeze_pattern,
)
from p4u1_set_valued_replay_v0_1 import (
    GATE_C_FAILED,
    GATE_C_REPLICATED,
    REPLAY_MULTI_PATH,
    REPLAY_NO_PATH,
    REPLAY_ONE_PATH,
    _position_groups_satisfied,
    compatible_paths_from_start,
    evaluate_gate_c_set_valued,
    legacy_unique_replay_status,
    replay_on_all_admissible_starts_set_valued,
    replay_set_valued,
    skeleton_matching_paths_from_start,
)


def _obs(fact_id: str, rel: str, subj: str, obj: str) -> Node:
    return Node(fact_id, OBSERVATION, (node_ref(rel), node_ref(subj), node_ref(obj)))


def _frozen(skeleton, depth, structure=(), support_train=1):
    return FrozenPatternU1(
        frozen_id="test",
        skeleton=skeleton,
        depth=depth,
        structure=structure,
        support_train=support_train,
        structural_digest="irrelevant-for-these-tests",
        discovery_metadata={},
    )


REL_A_B_SKELETON = (("REL_A", "FORWARD"), ("REL_B", "FORWARD"))


def _three_branch_hub_corpus():
    """H --REL_A--> C1 --REL_B--> G1
       H --REL_A--> C2 --REL_B--> G2
       H --REL_A--> C3 --REL_B--> G3

    Three genuinely distinct depth-2 skeleton-matching branches from H
    -- exactly the shape that made kernel2.replay_path_pattern_holdout()
    (max_candidates_per_step=1 by default) return AMBIGUOUS at H."""
    return (
        _obs("a1", "REL_A", "H", "C1"), _obs("b1", "REL_B", "C1", "G1"),
        _obs("a2", "REL_A", "H", "C2"), _obs("b2", "REL_B", "C2", "G2"),
        _obs("a3", "REL_A", "H", "C3"), _obs("b3", "REL_B", "C3", "G3"),
    )


def _real_frozen_pattern_for(observations):
    """Runs the real discovery + Gate B + freeze pipeline (core module,
    UNMODIFIED) to get a genuine `FrozenPatternU1` -- not a hand-rolled
    stand-in -- for tests that want full pipeline realism."""
    candidates = discover_candidates(observations, min_depth=2, max_depth=2)
    candidate = next(c for c in candidates if c.skeleton == REL_A_B_SKELETON)
    gate_b = evaluate_gate_b(candidate, null_max_dist=(0,), min_depth=2, s_min=2)
    assert gate_b.outcome == "RETAINED"
    return freeze_pattern(gate_b.pattern, frozen_id="test", support_train=candidate.support, metadata={})


# ---------------------------------------------------------------------------
# 1. skeleton_matching_paths_from_start -- purely a skeleton filter.
# ---------------------------------------------------------------------------


def test_skeleton_matching_paths_from_start_finds_all_branches_from_a_hub():
    observations = _three_branch_hub_corpus()
    pattern = _frozen(REL_A_B_SKELETON, depth=2)
    matches = skeleton_matching_paths_from_start(pattern, observations, node_ref("H"))
    assert len(matches) == 3
    assert {p.end.ref_id for p in matches} == {"G1", "G2", "G3"}


def test_skeleton_matching_paths_from_start_excludes_wrong_skeleton():
    observations = (_obs("a", "REL_X", "H", "C"), _obs("b", "REL_Y", "C", "G"))
    pattern = _frozen(REL_A_B_SKELETON, depth=2)
    matches = skeleton_matching_paths_from_start(pattern, observations, node_ref("H"))
    assert matches == ()


# ---------------------------------------------------------------------------
# 2. The central scenario -- hub existence-based replication vs kernel2's
#    legacy uniqueness-based AMBIGUOUS, on the SAME data.
# ---------------------------------------------------------------------------


def test_hub_with_multiple_valid_continuations_is_replicated():
    observations = _three_branch_hub_corpus()
    pattern = _real_frozen_pattern_for(observations)

    result = replay_set_valued(pattern, observations, node_ref("H"))

    assert result.replay_status == REPLAY_MULTI_PATH
    assert result.replicated is True
    assert len(result.compatible_paths) == 3  # no real co-reference constraint to fail (see module docstring)


def test_legacy_status_is_ambiguous_at_the_same_hub_where_the_adapter_says_replicated():
    """Direct confirmation of the divergence this module exists to
    resolve: kernel2.replay_path_pattern_holdout() (UNMODIFIED) reports
    AMBIGUOUS at the very same hub where the set-valued adapter above
    correctly reports REPLICATED=True."""
    observations = _three_branch_hub_corpus()
    candidates = discover_candidates(observations, min_depth=2, max_depth=2)
    candidate = next(c for c in candidates if c.skeleton == REL_A_B_SKELETON)
    gate_b = evaluate_gate_b(candidate, null_max_dist=(0,), min_depth=2, s_min=2)

    status = legacy_unique_replay_status(gate_b.pattern, observations, node_ref("H"))
    assert status == "AMBIGUOUS"


# ---------------------------------------------------------------------------
# 3. _position_groups_satisfied -- direct unit test of the constraint
#    logic itself, on hand-built PathRecords (see module-docstring
#    finding: discover_paths() itself can never produce a repeated
#    position, so this branch is otherwise unreachable today).
# ---------------------------------------------------------------------------


def _hand_built_path(node_ids):
    steps = tuple(
        PathStep(
            edge_id=f"e{i}", observation_id=f"o{i}", operator=node_ref(f"REL_{i}"),
            direction="FORWARD", source=NodeRef(node_ids[i]), target=NodeRef(node_ids[i + 1]),
        )
        for i in range(len(node_ids) - 1)
    )
    return PathRecord(path_id="hand-built", start=NodeRef(node_ids[0]), end=NodeRef(node_ids[-1]), steps=steps, provenance=())


def test_position_groups_satisfied_true_when_the_constrained_positions_genuinely_coincide():
    path = _hand_built_path(["H", "C", "H"])  # position 0 and 2 both NodeRef("H")
    assert _position_groups_satisfied(path, ((0, 2),)) is True


def test_position_groups_satisfied_false_when_the_constrained_positions_differ():
    path = _hand_built_path(["H", "C", "X"])
    assert _position_groups_satisfied(path, ((0, 2),)) is False


def test_position_groups_satisfied_trivially_true_for_singleton_groups():
    path = _hand_built_path(["H", "C", "X"])
    assert _position_groups_satisfied(path, ((0,), (1,), (2,))) is True


# ---------------------------------------------------------------------------
# 4. Anti-circularity (protocol Sec. 10.5).
# ---------------------------------------------------------------------------


def test_replay_set_valued_signature_never_accepts_a_witness_or_ground_truth():
    forbidden = {"witness", "label", "expected", "target", "ground_truth", "oracle"}
    for fn in (replay_set_valued, skeleton_matching_paths_from_start, compatible_paths_from_start,
               replay_on_all_admissible_starts_set_valued):
        params = set(inspect.signature(fn).parameters.keys())
        assert forbidden.isdisjoint(params), f"{fn.__name__} accepts a forbidden parameter: {params & forbidden}"


# ---------------------------------------------------------------------------
# 5. Aggregate replication -- coverage, support, and the new diagnostic.
# ---------------------------------------------------------------------------


def test_replay_on_all_admissible_starts_set_valued_computes_coverage_and_support():
    observations = list(_three_branch_hub_corpus())  # H: MULTI_PATH, 3 compatible continuations
    observations.append(_obs("a4", "REL_A", "H2", "C4"))
    observations.append(_obs("b4", "REL_B", "C4", "G4"))  # H2: ONE_PATH, 1 compatible continuation
    observations.append(_obs("dead", "REL_A", "DEAD_SOURCE", "DEAD_SINK"))  # DEAD_SOURCE: NO_PATH

    pattern = _real_frozen_pattern_for(_three_branch_hub_corpus())
    replication = replay_on_all_admissible_starts_set_valued(pattern, tuple(observations))

    assert replication.support_holdout == 2  # H and H2 replicate; DEAD_SOURCE does not
    # Admissible starts: H, C1, C2, C3, H2, C4, DEAD_SOURCE = 7
    assert replication.n_starts_admissible == 7
    assert replication.coverage == pytest.approx(2 / 7)
    # H has 3 compatible continuations, H2 has 1 -> mean over replicating starts = 2.0
    assert replication.mean_valid_continuations_per_replicating_start == pytest.approx((3 + 1) / 2)


def test_mean_valid_continuations_is_none_when_nothing_replicates():
    observations = (_obs("a", "REL_A", "H", "C"),)  # dead end, no REL_B continuation at all
    pattern = _real_frozen_pattern_for(_three_branch_hub_corpus())
    replication = replay_on_all_admissible_starts_set_valued(pattern, observations)
    assert replication.support_holdout == 0
    assert replication.mean_valid_continuations_per_replicating_start is None


def test_no_path_and_one_path_statuses():
    pattern = _frozen(REL_A_B_SKELETON, depth=2, structure=())
    no_continuation = (_obs("a", "REL_A", "H", "C"),)  # dead end, no REL_B
    assert replay_set_valued(pattern, no_continuation, node_ref("H")).replay_status == REPLAY_NO_PATH

    one_continuation = (_obs("a", "REL_A", "H", "C"), _obs("b", "REL_B", "C", "G"))
    result = replay_set_valued(pattern, one_continuation, node_ref("H"))
    assert result.replay_status == REPLAY_ONE_PATH
    assert result.replicated is True  # no structural constraint, so the lone branch qualifies


# ---------------------------------------------------------------------------
# 6. evaluate_gate_c_set_valued -- same three conditions as the core
#    module's evaluate_gate_c, applied to the new statistic.
# ---------------------------------------------------------------------------


def test_evaluate_gate_c_set_valued_replicated_only_when_all_three_conditions_hold():
    observations = []
    for hub in ("H1", "H2", "H3"):
        observations.append(_obs(f"a_{hub}", "REL_A", hub, f"C_{hub}"))
        observations.append(_obs(f"b_{hub}", "REL_B", f"C_{hub}", f"G_{hub}"))
    pattern = _real_frozen_pattern_for(_three_branch_hub_corpus())
    replication = replay_on_all_admissible_starts_set_valued(pattern, tuple(observations))
    assert replication.support_holdout == 3

    strong = evaluate_gate_c_set_valued(replication, holdout_null_max_dist=(0, 0, 0), k_min=2, coverage_min=0.1)
    assert strong.outcome == GATE_C_REPLICATED

    below_k_min = evaluate_gate_c_set_valued(replication, holdout_null_max_dist=(0, 0, 0), k_min=10, coverage_min=0.1)
    assert below_k_min.outcome == GATE_C_FAILED

    not_null_significant = evaluate_gate_c_set_valued(
        replication, holdout_null_max_dist=(3, 3, 3), k_min=2, coverage_min=0.1
    )
    assert not_null_significant.outcome == GATE_C_FAILED

    low_coverage = evaluate_gate_c_set_valued(replication, holdout_null_max_dist=(0,), k_min=2, coverage_min=0.99)
    assert low_coverage.outcome == GATE_C_FAILED


# ---------------------------------------------------------------------------
# 7. Determinism.
# ---------------------------------------------------------------------------


def test_replay_set_valued_is_deterministic():
    observations = _three_branch_hub_corpus()
    pattern = _real_frozen_pattern_for(observations)
    result_a = replay_set_valued(pattern, observations, node_ref("H"))
    result_b = replay_set_valued(pattern, observations, node_ref("H"))
    assert result_a.replicated == result_b.replicated
    assert result_a.replay_status == result_b.replay_status
    assert {p.path_id for p in result_a.compatible_paths} == {p.path_id for p in result_b.compatible_paths}
