"""E18 — recurrent tree-shape reassociation (ported 2026-09-16 from an
independently-authored external variant, after two rounds of adversarial
verification by execution -- see
documentation/CORPUS_V2_0_RAPPORT_TESTS_ET_CORRECTIONS_2026-09-16.md).

compare()'s flat position-permutation search (E13-A.2) is structurally
incapable of discovering a regrouping of a nested, same-operator-recurrent
application (a nested Node isn't a fixed-arity tuple position). E18 adds
compare_tree_shapes()/apply_tree_shape()/shape_pattern_is_applicable() as a
second Compare/Apply/Applicable mechanism for exactly that case, reached via
compare()'s own fallback when the flat search finds nothing -- not a
separately-named entry point the caller must know to use.

Every test below either reproduces a real bug found and fixed BEFORE this
port (so it never regresses silently after being merged into this kernel),
or exercises the mechanism's own stated scope limits.
"""
from __future__ import annotations

from kernel2 import (
    OBSERVATION,
    SHAPE_PATTERN,
    Node,
    apply,
    apply_tree_shape,
    compare,
    compare_tree_shapes,
    is_applicable,
    shape_pattern_is_applicable,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def test_discovers_a_regrouping_the_flat_search_cannot_express():
    """OP(OP(X,Q),Y) -> OP(X,OP(Q,Y)): a pure regrouping with leaf order
    preserved. The flat position-permutation search (_compare_observations)
    cannot express this at all (the two sides don't even have the same
    top-level arity as flat tuples), so compare() must reach it only via the
    compare_tree_shapes() fallback."""
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")
    inner_b = _obs("inner_b", "OP", "Q", "Y", "_ib")
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")

    pattern = compare(a, b)
    assert pattern is not None
    assert pattern.kind == SHAPE_PATTERN

    # via compare_tree_shapes() directly too -- same result, compare() just
    # reaches it through its own fallback rather than a separate call site.
    assert compare_tree_shapes(a, b) == pattern


def test_applies_the_discovered_regrouping_to_unseen_data():
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")
    inner_b = _obs("inner_b", "OP", "Q", "Y", "_ib")
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")
    pattern = compare(a, b)

    fresh_inner = _obs("fresh_inner", "OP", "P1", "P2", "_f")
    fresh = _obs("fresh", "OP", fresh_inner, "P3", "OUT2")
    predicted = apply(pattern, fresh)
    assert predicted is not None
    assert predicted.children[0] == "OP"
    assert predicted.children[1] == "P1"
    inner_predicted = predicted.children[2]
    assert isinstance(inner_predicted, Node)
    assert inner_predicted.children == ("OP", "P2", "P3", "_intermediate")
    assert predicted.children[-1] == "OUT2"
    # apply_tree_shape() directly gives the identical result -- apply() just dispatches to it.
    assert apply_tree_shape(pattern, fresh) == predicted


def test_regroup_combined_with_permuted_leaf_order_is_correctly_refused():
    """_same_shape_signature requires the flattened leaf sequences to be
    EXACTLY equal, not merely a permutation of each other -- a regrouping
    combined with a genuine argument-order change must be refused, not
    force-fit. This is narrower than "associativity" might suggest, and is
    documented as such rather than silently overclaimed."""
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")  # flattens to [X, Q, Y]

    inner_c = _obs("inner_c", "OP", "Y", "Q", "_ic")  # flattens to [Y, Q]
    c = _obs("disc_c", "OP", inner_c, "X", "OUT")  # flattens to [Y, Q, X] -- a permutation, not equal

    assert compare_tree_shapes(a, c) is None
    assert compare(a, c) is None  # the flat search also finds nothing here (different arity/shape)


def test_repeated_leaf_value_does_not_corrupt_fresh_data_predictions():
    """THE confirmed bug fixed before this port: the original value-keyed
    leaf binding silently merged two leaves that happened to share a value
    at discovery time into one variable. Applied to fresh data with three
    genuinely distinct values, that bug duplicated one value and dropped
    another entirely (P1 appeared twice, P3 zero times). This test locks in
    the fix: every fresh value must appear exactly once, at the correct
    position, regardless of what coincidentally repeated during discovery."""
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")  # flattens to [X, Q]
    a = _obs("disc_a", "OP", inner_a, "X", "OUT")  # flattens to [X, Q, X] -- "X" repeats

    inner_b = _obs("inner_b", "OP", "Q", "X", "_ib")  # flattens to [Q, X]
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")  # flattens to [X, Q, X] -- same flat list, different grouping

    pattern = compare_tree_shapes(a, b)
    assert pattern is not None

    fresh_inner = _obs("fresh_inner", "OP", "P1", "P2", "_f")
    fresh = _obs("fresh", "OP", fresh_inner, "P3", "OUT2")
    predicted = apply_tree_shape(pattern, fresh)
    assert predicted is not None

    def collect_leaves(node):
        leaves = []
        for c in node.children[1:-1]:
            if isinstance(c, Node):
                leaves.extend(collect_leaves(c))
            else:
                leaves.append(c)
        return leaves

    leaves = collect_leaves(predicted)
    assert sorted(leaves) == ["P1", "P2", "P3"]  # each exactly once -- no duplication, no loss


def test_two_identical_observations_yield_no_pattern_not_a_trivial_rewrite():
    """Found by this port's own regression suite: two literally identical
    observations were producing a no-op SHAPE_PATTERN (src == dst) instead
    of None, breaking parity with compare()'s "identical: nothing to reify"
    contract for the flat case. compare_tree_shapes() now checks src == dst
    explicitly and refuses to reify a rewrite that changes nothing."""
    same = _obs("s", "OP", "A", "B", "C")
    identical_copy = _obs("s2", "OP", "A", "B", "C")
    assert compare(same, identical_copy) is None
    assert compare_tree_shapes(same, identical_copy) is None


def test_shape_pattern_is_applicable_matches_apply_tree_shapes_own_arity_check():
    inner_a = _obs("inner_a", "OP", "X", "Q", "_ia")
    a = _obs("disc_a", "OP", inner_a, "Y", "OUT")
    inner_b = _obs("inner_b", "OP", "Q", "Y", "_ib")
    b = _obs("disc_b", "OP", "X", inner_b, "OUT")
    pattern = compare(a, b)

    fresh_ok_inner = _obs("f1i", "OP", "P1", "P2", "_f")
    fresh_ok = _obs("f1", "OP", fresh_ok_inner, "P3", "OUT2")
    fresh_bad = _obs("f2", "OP", "P1", "P2", "OUT2")  # wrong flattened arity (2, not 3)

    assert shape_pattern_is_applicable(pattern, fresh_ok) is True
    assert apply_tree_shape(pattern, fresh_ok) is not None
    assert shape_pattern_is_applicable(pattern, fresh_bad) is False
    assert apply_tree_shape(pattern, fresh_bad) is None

    # is_applicable()/apply() (the unified entry points) agree exactly.
    assert is_applicable(pattern, fresh_ok) is True
    assert is_applicable(pattern, fresh_bad) is False


def test_flat_non_recurrent_observations_never_trigger_the_fallback_incorrectly():
    """A non-commutative flat pair (no nested/recurrent structure at all)
    must still yield no pattern -- the E18 fallback must not "rescue" a case
    the E13-A.2 flat search correctly refused."""
    sub1 = _obs("sub1", "SUB", "M", "N", "D1")
    sub2 = _obs("sub2", "SUB", "N", "M", "D2")
    assert compare(sub1, sub2) is None
    assert compare_tree_shapes(sub1, sub2) is None
