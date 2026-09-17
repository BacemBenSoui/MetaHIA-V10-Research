"""Apply/Applicable unification (ported 2026-09-16, see
documentation/CORPUS_V2_0_RAPPORT_TESTS_ET_CORRECTIONS_2026-09-16.md).

apply() and is_applicable() are single public dispatchers mirroring
compare(): dispatch on pattern.kind alone (PATTERN -> apply_pattern()/
pattern_is_applicable(), SHAPE_PATTERN -> apply_tree_shape()/
shape_pattern_is_applicable()), never on any inspection of what the pattern
"means". Neither underlying function is changed; both remain directly
callable -- these tests confirm the dispatchers are pure passthroughs, not a
second implementation that could drift from the ones already validated.
"""
from __future__ import annotations

from kernel2 import (
    OBSERVATION,
    Node,
    apply,
    apply_pattern,
    apply_tree_shape,
    compare,
    compare_tree_shapes,
    is_applicable,
    pattern_is_applicable,
    shape_pattern_is_applicable,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def test_apply_matches_apply_pattern_exactly_on_a_permutation_pattern():
    o1, o2 = _obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C")
    pattern = compare(o1, o2)
    unseen = _obs("h1", "O", "P", "Q", "C")
    assert apply(pattern, unseen) == apply_pattern(pattern, unseen)


def test_apply_matches_apply_tree_shape_exactly_on_a_shape_pattern():
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")
    inner_b = _obs("inner_b", "OP", "Q", "Y", "_ib")
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")
    shape_pattern = compare_tree_shapes(a, b)

    fresh_inner = _obs("f1i", "OP", "P1", "P2", "_f")
    fresh = _obs("f1", "OP", fresh_inner, "P3", "OUT2")
    assert apply(shape_pattern, fresh) == apply_tree_shape(shape_pattern, fresh)


def test_apply_raises_on_a_pattern_of_the_wrong_kind():
    not_a_pattern = _obs("x", "O", "A", "B", "C")
    try:
        apply(not_a_pattern, not_a_pattern)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_is_applicable_matches_pattern_is_applicable_exactly():
    o1, o2 = _obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C")
    pattern = compare(o1, o2)
    matching = _obs("h1", "O", "P", "Q", "C")
    mismatching = _obs("h2", "DIFFERENT", "P", "Q", "C")
    assert is_applicable(pattern, matching) == pattern_is_applicable(pattern, matching) == True
    assert is_applicable(pattern, mismatching) == pattern_is_applicable(pattern, mismatching) == False


def test_is_applicable_matches_shape_pattern_is_applicable_exactly():
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")
    inner_b = _obs("inner_b", "OP", "Q", "Y", "_ib")
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")
    shape_pattern = compare_tree_shapes(a, b)

    fresh_ok_inner = _obs("f1i", "OP", "P1", "P2", "_f")
    fresh_ok = _obs("f1", "OP", fresh_ok_inner, "P3", "OUT2")
    fresh_bad = _obs("f2", "OP", "P1", "P2", "OUT2")  # wrong arity

    assert is_applicable(shape_pattern, fresh_ok) == shape_pattern_is_applicable(shape_pattern, fresh_ok) == True
    assert is_applicable(shape_pattern, fresh_bad) == shape_pattern_is_applicable(shape_pattern, fresh_bad) == False


def test_is_applicable_raises_on_a_pattern_of_the_wrong_kind():
    not_a_pattern = _obs("x", "O", "A", "B", "C")
    try:
        is_applicable(not_a_pattern, not_a_pattern)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_check_then_apply_idiom_works_uniformly_for_both_pattern_kinds():
    """The concrete consequence of the unification: a caller can write one
    generic function that works for either pattern kind without needing to
    know in advance which one it received -- this used to crash with an
    unhandled ValueError for SHAPE_PATTERN before is_applicable() existed."""
    def generic_caller(pattern, observation):
        if not is_applicable(pattern, observation):
            return "SKIPPED"
        return apply(pattern, observation)

    o1, o2 = _obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C")
    perm_pattern = compare(o1, o2)
    unseen = _obs("h1", "O", "P", "Q", "C")
    assert generic_caller(perm_pattern, unseen) == apply_pattern(perm_pattern, unseen)

    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")
    inner_b = _obs("inner_b", "OP", "Q", "Y", "_ib")
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")
    shape_pattern = compare_tree_shapes(a, b)
    fresh_bad = _obs("f2", "OP", "P1", "P2", "OUT2")  # wrong arity: not applicable
    assert generic_caller(shape_pattern, fresh_bad) == "SKIPPED"  # no crash
