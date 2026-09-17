"""E16 — competing regularities (Corpus V2.0 roadmap, documentation/CORPUS_V2_0_ROADMAP_2026-09-16.md).

Dimension tested, alone: several observation pairs -- nominally about "the
same operator" -- support genuinely DIFFERENT, mutually incompatible local
patterns. This is distinct from the ambiguity fixed earlier (E13-A.2 follow-
up): ambiguity is several permutations tying on ONE pair; here, several
DIFFERENT pairs each unambiguously yield their own valid pattern, and those
patterns disagree with each other.

PASS criterion (from the roadmap): the engine represents several competing
hypotheses without arbitrarily erasing one (consistent with E4/Hypothesis).
FAIL criterion: a regularity is silently overwritten by another.

group_into_hypotheses() (kernel.py) is the mechanism under test: it groups
pairs into Hypothesis objects using compare() itself as the "is this the same
regularity" test (reusing the existing PATTERN-vs-PATTERN abstraction, not a
new bespoke equality notion).
"""
from __future__ import annotations

from kernel2 import OBSERVATION, Node, apply_pattern, group_into_hypotheses


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def test_two_genuinely_different_patterns_both_survive_as_separate_hypotheses():
    """Pair 1 swaps positions (1,2); pair 2 -- same operator symbol "O", same
    arity -- swaps positions (2,3) instead. These are structurally different
    transformations (compare() on the two patterns must fail to merge them,
    since a mismatched source_position is exactly the incompatibility check
    already used for cross-family abstraction). Neither may be dropped."""
    pair1 = (_obs("s1", "O", "A", "B", "K", "C"), _obs("s2", "O", "B", "A", "K", "C"))
    pair2 = (_obs("s3", "O", "M", "B2", "C2", "D"), _obs("s4", "O", "M", "C2", "B2", "D"))

    hypotheses = group_into_hypotheses([pair1, pair2])

    assert len(hypotheses) == 2  # neither pattern silently overwrote the other
    mappings = {tuple(slot.source_position for slot in h.pattern.children) for h in hypotheses}
    assert mappings == {(0, 2, 1, 3, 4), (0, 1, 3, 2, 4)}

    all_supporting = {oid for h in hypotheses for oid in h.supporting_ids}
    assert all_supporting == {"s1", "s2", "s3", "s4"}  # every pair's evidence is on record somewhere
    assert all(h.status == "SUPPORTED" for h in hypotheses)


def test_a_third_pair_reinforcing_the_first_pattern_merges_rather_than_competing():
    """A pair from a DIFFERENT operator (NOR) that shares pair1's exact
    transformation (swap positions 1,2, positions 3/4 frozen-but-different
    literals) must merge into hypothesis 0 -- generalizing it, exactly like
    E13-A.2's cross-family abstraction -- not spawn a third, redundant
    hypothesis. This is the negative control proving group_into_hypotheses
    does not over-fragment compatible evidence into false "competitors"."""
    pair1 = (_obs("s1", "O", "A", "B", "K", "C"), _obs("s2", "O", "B", "A", "K", "C"))
    pair2 = (_obs("s3", "O", "M", "B2", "C2", "D"), _obs("s4", "O", "M", "C2", "B2", "D"))
    pair3 = (_obs("s5", "NOR", "X", "Y", "Z", "W"), _obs("s6", "NOR", "Y", "X", "Z", "W"))

    hypotheses = group_into_hypotheses([pair1, pair2, pair3])

    assert len(hypotheses) == 2  # still exactly two competing regularities, not three
    reinforced = next(h for h in hypotheses if "s5" in h.supporting_ids)
    assert set(reinforced.supporting_ids) == {"s1", "s2", "s5", "s6"}
    # generalized: operator identity is no longer a fixed literal (O vs NOR differ)
    assert reinforced.pattern.children[0].literal_constraint is None


def test_grouping_is_order_independent():
    """Feeding the same pairs in a different order must yield the same set of
    competing regularities -- the grouping reflects the data, not the order
    pairs happened to arrive in."""
    pair1 = (_obs("s1", "O", "A", "B", "K", "C"), _obs("s2", "O", "B", "A", "K", "C"))
    pair2 = (_obs("s3", "O", "M", "B2", "C2", "D"), _obs("s4", "O", "M", "C2", "B2", "D"))
    pair3 = (_obs("s5", "NOR", "X", "Y", "Z", "W"), _obs("s6", "NOR", "Y", "X", "Z", "W"))

    forward = group_into_hypotheses([pair1, pair2, pair3])
    backward = group_into_hypotheses([pair3, pair2, pair1])

    def signature(hs):
        return {
            frozenset(h.supporting_ids): tuple(slot.source_position for slot in h.pattern.children)
            for h in hs
        }

    assert signature(forward) == signature(backward)


def test_each_competing_hypothesis_still_predicts_correctly_on_its_own_terms():
    """Both surviving hypotheses remain independently usable: applying each
    to unseen data matching its own frozen literals produces the prediction
    that specific regularity implies -- neither is degraded by the other's
    presence in the same grouping run."""
    pair1 = (_obs("s1", "O", "A", "B", "K", "C"), _obs("s2", "O", "B", "A", "K", "C"))
    pair2 = (_obs("s3", "O", "M", "B2", "C2", "D"), _obs("s4", "O", "M", "C2", "B2", "D"))
    hypotheses = group_into_hypotheses([pair1, pair2])

    h_swap12 = next(h for h in hypotheses if h.pattern.children[1].source_position == 2)
    h_swap23 = next(h for h in hypotheses if h.pattern.children[2].source_position == 3)

    unseen_for_swap12 = _obs("h1", "O", "P", "Q", "K", "C")
    predicted1 = apply_pattern(h_swap12.pattern, unseen_for_swap12)
    assert predicted1.children == ("O", "Q", "P", "K", "C")

    unseen_for_swap23 = _obs("h2", "O", "M", "P", "Q", "D")
    predicted2 = apply_pattern(h_swap23.pattern, unseen_for_swap23)
    assert predicted2.children == ("O", "M", "Q", "P", "D")


def test_a_pair_yielding_no_pattern_at_all_is_skipped_not_treated_as_a_third_hypothesis():
    """A non-commutative pair (E13-A.2's SUB precedent) contributes no local
    pattern -- it must be silently skipped by the grouping, not turned into
    an empty/spurious hypothesis, and must not affect the two real ones."""
    pair1 = (_obs("s1", "O", "A", "B", "K", "C"), _obs("s2", "O", "B", "A", "K", "C"))
    pair2 = (_obs("s3", "O", "M", "B2", "C2", "D"), _obs("s4", "O", "M", "C2", "B2", "D"))
    non_commutative = (_obs("s7", "SUB", "M", "N", "K", "D1"), _obs("s8", "SUB", "N", "M", "K", "D2"))

    hypotheses = group_into_hypotheses([pair1, non_commutative, pair2])
    assert len(hypotheses) == 2
    all_supporting = {oid for h in hypotheses for oid in h.supporting_ids}
    assert "s7" not in all_supporting and "s8" not in all_supporting
