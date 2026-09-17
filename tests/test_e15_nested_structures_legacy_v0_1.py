"""E15 — nested structures (Corpus V2.0 roadmap, documentation/CORPUS_V2_0_ROADMAP_2026-09-16.md).

Dimension tested, alone: observations are composite Node trees, not flat
tuples of opaque labels -- some children are themselves OBSERVATION nodes.

PASS criterion (from the roadmap): compare() applied recursively to
sub-structures discovers a regularity at depth >= 2.
FAIL criterion: the recursion does not terminate, or nothing is discovered
beyond the root level.

Key point this dimension is designed to expose: WITHOUT recursion, a pair of
outer observations whose only difference is a nested sub-structure has
exactly one varying position and no partner to permute it against -- the
flat mechanism alone would report "no permutation reconciles them" (None),
even though a real regularity exists one level deeper. This is verified
below (test_without_recursion_the_pair_would_be_falsely_incomparable) before
showing the recursive mechanism actually finds it.
"""
from __future__ import annotations

from kernel2 import (
    OBSERVATION,
    Node,
    _all_reconciling_permutations,
    apply_pattern,
    compare,
    pattern_is_applicable,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def test_without_recursion_the_pair_would_be_falsely_incomparable():
    """Sanity check that this test genuinely exercises depth >= 2, not a case
    the flat (E13-A.2/E14) mechanism could already handle: with only one
    varying position (the nested child) and nothing else to permute it
    against, the identity is the only "permutation" available, and identity
    can never reconcile a varying position (see kernel.py's own invariant)."""
    inner_a = _obs("inner_a", "O", "A", "B", "C")
    inner_b = _obs("inner_b", "O", "B", "A", "C")
    outer_a = _obs("outer_a", "WRAP", inner_a)
    outer_b = _obs("outer_b", "WRAP", inner_b)

    varying = [p for p in range(2) if outer_a.children[p] != outer_b.children[p]]
    assert varying == [1]  # only the nested position differs
    assert _all_reconciling_permutations(outer_a.children, outer_b.children, varying) == []


def test_compare_discovers_a_regularity_one_level_deep():
    """The exact same pair as above, through the real compare(): recursion
    into the nested OBSERVATION finds the inner swap pattern, where the flat
    mechanism alone would have returned None."""
    inner_a = _obs("inner_a", "O", "A", "B", "C")
    inner_b = _obs("inner_b", "O", "B", "A", "C")
    outer_a = _obs("outer_a", "WRAP", inner_a)
    outer_b = _obs("outer_b", "WRAP", inner_b)

    pattern = compare(outer_a, outer_b)
    assert pattern is not None
    assert len(pattern.children) == 2
    assert pattern.children[0].literal_constraint == "WRAP"  # outer frozen slot, untouched
    outer_slot = pattern.children[1]
    assert outer_slot.nested_pattern is not None
    assert outer_slot.source_position == 1  # self: not permuted at the outer level

    inner_pattern = outer_slot.nested_pattern
    assert inner_pattern.children[0].literal_constraint == "O"
    assert inner_pattern.children[1].source_position == 2
    assert inner_pattern.children[2].source_position == 1
    assert inner_pattern.children[3].literal_constraint == "C"


def test_apply_pattern_recurses_into_the_nested_prediction():
    """Applying the discovered nested pattern to unseen data must transform
    the inner sub-structure, not copy it through unchanged."""
    inner_a = _obs("inner_a", "O", "A", "B", "C")
    inner_b = _obs("inner_b", "O", "B", "A", "C")
    outer_a = _obs("outer_a", "WRAP", inner_a)
    outer_b = _obs("outer_b", "WRAP", inner_b)
    pattern = compare(outer_a, outer_b)

    unseen_inner = _obs("h_inner", "O", "P", "Q", "C")
    unseen_outer = _obs("h_outer", "WRAP", unseen_inner)
    predicted = apply_pattern(pattern, unseen_outer)
    assert predicted is not None
    assert predicted.children[0] == "WRAP"
    predicted_inner = predicted.children[1]
    assert isinstance(predicted_inner, Node)
    assert predicted_inner.children == ("O", "Q", "P", "C")


def test_pattern_is_applicable_checks_the_nested_slot_recursively():
    inner_a = _obs("inner_a", "O", "A", "B", "C")
    inner_b = _obs("inner_b", "O", "B", "A", "C")
    pattern = compare(_obs("outer_a", "WRAP", inner_a), _obs("outer_b", "WRAP", inner_b))

    matching = _obs("h1", "WRAP", _obs("h1_inner", "O", "P", "Q", "C"))
    assert pattern_is_applicable(pattern, matching) is True

    wrong_inner_operator = _obs("h2", "WRAP", _obs("h2_inner", "DIFFERENT", "P", "Q", "C"))
    assert pattern_is_applicable(pattern, wrong_inner_operator) is False

    not_a_node_at_all = _obs("h3", "WRAP", "just_a_string")
    assert pattern_is_applicable(pattern, not_a_node_at_all) is False


def test_abstraction_recurses_into_nested_patterns_across_two_families():
    """Depth >= 2 must also survive the abstraction step (Compare(D1, D2)):
    two independent outer families, each wrapping a DIFFERENT inner operator,
    abstract into a general pattern whose nested_pattern is itself fully
    generalized -- proving recursive Compare, not just recursive discovery."""
    d1 = compare(
        _obs("o1", "WRAP", _obs("o1_inner", "O", "A", "B", "C")),
        _obs("o2", "WRAP", _obs("o2_inner", "O", "B", "A", "C")),
    )
    d2 = compare(
        _obs("a1", "WRAP", _obs("a1_inner", "AND", "P", "Q", "R")),
        _obs("a2", "WRAP", _obs("a2_inner", "AND", "Q", "P", "R")),
    )
    general = compare(d1, d2)
    assert general is not None
    outer_slot = general.children[1]
    assert outer_slot.nested_pattern is not None
    # the inner operator identity ("O" vs "AND") and output ("C" vs "R") were
    # each frozen-but-different across the two families: generalized away.
    assert all(slot.literal_constraint is None for slot in outer_slot.nested_pattern.children)

    unseen_inner = _obs("h_inner", "NOR", "X", "Y", "Z")
    predicted = apply_pattern(general, _obs("h_outer", "WRAP", unseen_inner))
    assert predicted is not None
    assert predicted.children[1].children == ("NOR", "Y", "X", "Z")


def test_recursion_terminates_and_finds_nothing_deeper_than_where_a_regularity_exists():
    """FAIL-criterion guard: a nested position whose inner content is
    identical on both sides (no inner regularity to find) must not cause
    infinite recursion or a spurious nested pattern -- it is simply frozen,
    like any other unchanged position. A separate swappable pair of plain
    positions is included so the pair is resolvable at all (an identical
    nested child alone, with nothing else varying, is trivially "no
    difference to reify" -- see test_compare_returns_none_for_identical_observations)."""
    same_inner = _obs("same_inner", "O", "A", "B", "C")
    outer_a = _obs("outer_a", "WRAP", same_inner, "X", "Y")
    outer_b = _obs("outer_b", "WRAP", same_inner, "Y", "X")
    pattern = compare(outer_a, outer_b)
    assert pattern is not None
    assert pattern.children[1].nested_pattern is None
    assert pattern.children[1].literal_constraint == same_inner  # frozen: identical nested Node on both sides
    assert pattern.children[2].source_position == 3  # the unrelated swap still resolved normally
    assert pattern.children[3].source_position == 2


def test_existing_e13a2_and_e14_results_are_unaffected_by_e15():
    """Regression guard: flat (non-nested) observations must behave exactly
    as before -- E15's recursion only ever triggers when a varying position
    actually holds Node values on both sides."""
    from loader import load_micro_corpus

    corpus = load_micro_corpus()
    for family, (a, b) in corpus.families.items():
        pattern = compare(a, b)
        assert pattern is not None, f"E15 regressed family {family!r}"
        assert all(slot.nested_pattern is None for slot in pattern.children)
