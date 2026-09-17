"""PatternRef and the cross-representation structural-signature layer --
ported 2026-09-16 from a further-evolved external variant
(kernel2_pre_rv_internal_fix_2026-09-16.py), on top of the already-audited
NodeRef/RefObject base. See kernel.py's module docstring, addendum #2.

Covers: PatternRef construction/typing, the ref_object()/pattern_ref()
constructor dispatch, resolve_structure() transparency through PatternRef,
same-representation structural equality, and the specific adversarial
false-positive hunt this audit performed for the flat/nested asymmetry
between a lifted PATTERN and a genuine ShapeRewrite (documented as a risk
in kernel.py, not found to be a reachable bug through the real discovery
API -- this test is the regression guard for that finding).
"""
from __future__ import annotations

import pytest

from kernel2 import (
    OBSERVATION,
    PATTERN,
    SHAPE_PATTERN,
    Node,
    PatternRef,
    RefObject,
    compare,
    compare_pattern_references,
    pattern_ref,
    pattern_structural_equal,
    ref_object,
    resolve_structure,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def _abstracted_swap_pattern(op_a, op_b):
    """Classic E13-A.2 two-step abstraction: discover a per-operator swap
    pattern for each of two operators, then abstract across them by
    comparing the two PATTERNs (the literal operator constraint generalizes
    to free since the two operator labels differ) -- yields a fully generic
    swap pattern with every slot free."""
    a1 = _obs("a1", op_a, "X", "Y", "R")
    b1 = _obs("b1", op_a, "Y", "X", "R")
    p1 = compare(a1, b1)
    assert p1 is not None and p1.kind == PATTERN

    a2 = _obs("a2", op_b, "X", "Y", "R")
    b2 = _obs("b2", op_b, "Y", "X", "R")
    p2 = compare(a2, b2)
    assert p2 is not None and p2.kind == PATTERN

    merged = compare(p1, p2)
    assert merged is not None and merged.kind == PATTERN
    return merged


# ---------------------------------------------------------------------------
# PatternRef construction and typing
# ---------------------------------------------------------------------------

def test_patternref_wraps_a_pattern_and_exposes_kind_and_pattern():
    pattern = _abstracted_swap_pattern("AND", "OR")
    pr = pattern_ref("P1", pattern)
    assert isinstance(pr, PatternRef)
    assert isinstance(pr, RefObject)
    assert pr.kind == PATTERN
    assert pr.pattern is pattern


def test_patternref_rejects_a_non_pattern_node_body():
    obs = _obs("a", "O", "X", "Y", "OUT")
    with pytest.raises(ValueError):
        pattern_ref("bad", obs)


def test_patternref_rejects_a_non_node_body():
    with pytest.raises(TypeError):
        PatternRef("bad", "not a node")


def test_ref_object_dispatches_to_patternref_for_pattern_bodies_and_refobject_otherwise():
    pattern = _abstracted_swap_pattern("NAND", "XOR")
    ro_plain = ref_object("X1", "just a payload")
    assert type(ro_plain) is RefObject
    assert not isinstance(ro_plain, PatternRef)

    ro_pattern = ref_object("X2", pattern)
    assert isinstance(ro_pattern, PatternRef)


def test_resolve_structure_unwraps_patternref_exactly_like_refobject():
    pattern = _abstracted_swap_pattern("AND", "OR")
    pr = pattern_ref("P1", pattern)
    assert resolve_structure(pr) is pattern


# ---------------------------------------------------------------------------
# Same-representation structural equality
# ---------------------------------------------------------------------------

def test_pattern_structural_equal_true_for_two_independently_discovered_equivalent_abstractions():
    pat_1 = _abstracted_swap_pattern("AND", "OR")
    pat_2 = _abstracted_swap_pattern("NAND", "XOR")
    assert pattern_structural_equal(pat_1, pat_2)
    assert compare_pattern_references(pat_1, pat_2) is True


def test_pattern_structural_equal_false_for_genuinely_different_abstractions():
    swap_pattern = _abstracted_swap_pattern("AND", "OR")

    # A non-commutative pair contributes a DIFFERENT pattern shape (nothing
    # generalizes the same way) -- build a second, non-swap family instead.
    a = _obs("a", "K", "M", "N", "P", "R")
    b = _obs("b", "K", "N", "P", "M", "R")  # a 3-cycle rotation, not a simple swap
    rotate_pattern = compare(a, b)
    assert rotate_pattern is not None
    assert not pattern_structural_equal(swap_pattern, rotate_pattern)
    assert compare_pattern_references(swap_pattern, rotate_pattern) is False


def test_pattern_structural_equal_and_compare_pattern_references_agree_on_non_pattern_input():
    obs = _obs("a", "O", "X", "Y", "OUT")
    pattern = _abstracted_swap_pattern("AND", "OR")
    assert pattern_structural_equal(obs, pattern) is False
    assert compare_pattern_references(obs, pattern) is None  # could not be lifted -- not "compared and differ"


# ---------------------------------------------------------------------------
# Cross-representation: REWRITE_TREE vs REWRITE_SLOTS never accidentally
# equal (different tags), and the flat/nested asymmetry means a lifted pure-
# permutation PATTERN cannot coincide with a genuinely regrouped
# SHAPE_PATTERN through the real discovery API -- the adversarial finding
# from this port's audit, turned into a permanent regression guard.
# ---------------------------------------------------------------------------

def test_pattern_with_literal_constraint_never_matches_a_shape_pattern():
    """A PATTERN carrying a literal_constraint or nested_pattern is lifted
    into a REWRITE_SLOTS signature, never REWRITE_TREE -- so it can never be
    mistaken for a ShapeRewrite (tagged REWRITE_TREE), by construction."""
    a = _obs("a", "FIXED_OP", "X", "Y", "OUT")
    b = _obs("b", "FIXED_OP", "Y", "X", "OUT")
    pattern_with_literal = compare(a, b)  # operator position is a literal_constraint here
    assert pattern_with_literal is not None
    assert pattern_with_literal.children[0].literal_constraint == "FIXED_OP"

    inner_e = _obs("ie", "Z", "A1", "A2", "_ie")
    e = _obs("e", "Z", inner_e, "A3", "OUT")
    inner_f = _obs("if_", "Z", "A2", "A3", "_if")
    f = _obs("f", "Z", "A1", inner_f, "OUT")
    shape_pattern = compare(e, f)
    assert shape_pattern is not None and shape_pattern.kind == SHAPE_PATTERN

    assert not pattern_structural_equal(pattern_with_literal, shape_pattern)
    assert compare_pattern_references(pattern_with_literal, shape_pattern) is False


def test_adversarial_search_finds_no_false_positive_between_a_pure_permutation_pattern_and_a_regrouped_shape_pattern():
    """The specific adversarial construction from this port's audit: a pure
    flat position-permutation PATTERN (fully generic, no literal, no
    nested) of the same arity as a genuinely-regrouped SHAPE_PATTERN,
    checked for a false-positive structural match. None was found through
    the real discovery API -- _pattern_slots_tree_signature can only ever
    produce a FLAT rewrite tree, while a genuine regroup is necessarily
    NESTED, so the two signatures cannot coincide for cases reachable this
    way (see kernel.py's honesty note on this exact asymmetry). This test
    is the regression guard: if a future change to either lifting function
    ever makes this pair compare equal, the assertion below must fail loud."""
    inner_e = _obs("ie", "Z", "A1", "A2", "_ie")
    e = _obs("e", "Z", inner_e, "A3", "OUT")          # flat(e) = [A1, A2, A3]
    inner_f = _obs("if_", "Z", "A2", "A3", "_if")
    f = _obs("f", "Z", "A1", inner_f, "OUT")          # flat(f) = [A1, A2, A3] (regroup)
    shape_pattern = compare(e, f)
    assert shape_pattern is not None and shape_pattern.kind == SHAPE_PATTERN

    g = _obs("g", "K1", "K2", "K3")   # 3-child flat observation, all distinct
    h = _obs("h", "K3", "K1", "K2")   # rotated -- a pure 3-cycle permutation, same arity (3)
    pure_perm_pattern = compare(g, h)
    assert pure_perm_pattern is not None and pure_perm_pattern.kind == PATTERN
    assert len(pure_perm_pattern.children) == shape_pattern.children[0].arity

    assert compare_pattern_references(shape_pattern, pure_perm_pattern) is False
    assert not pattern_structural_equal(shape_pattern, pure_perm_pattern)
