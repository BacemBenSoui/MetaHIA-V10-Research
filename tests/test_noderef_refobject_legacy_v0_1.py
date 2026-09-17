"""NodeRef/RefObject (reference/value separation) -- ported 2026-09-16 from
an external variant after two rounds of adversarial verification by
execution. See kernel.py's module docstring, addendum #2, and
research/k3_spike_e13a2/README.md for the dated section.

Covers: reference_equal vs structural_equal semantics, resolve_structure()
transparency through every public entry point, the NodeRef coreference
mechanism in E18 shape discovery/application (including the regression this
port fixed BEFORE merging: raw-position indexing of a deduplicated variable
list), and that the legacy plain-string path is unaffected.
"""
from __future__ import annotations

from kernel2 import (
    OBSERVATION,
    SHAPE_PATTERN,
    Node,
    NodeRef,
    RefObject,
    apply,
    apply_tree_shape,
    compare,
    compare_candidates,
    is_applicable,
    node_ref,
    pattern_is_applicable,
    ref_object,
    reference_equal,
    resolve_structure,
    structural_equal,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


# ---------------------------------------------------------------------------
# reference_equal / structural_equal
# ---------------------------------------------------------------------------

def test_reference_equal_is_identity_by_ref_id_not_by_payload():
    r1 = node_ref("P")
    r2 = node_ref("P")  # same ref_id, separately constructed
    r3 = node_ref("Q")
    assert reference_equal(r1, r2)
    assert not reference_equal(r1, r3)


def test_structural_equal_ignores_ref_object_identity_but_not_bare_noderef_identity():
    inner = _obs("z", "O", "a", "b", "c")
    ro1 = ref_object("X1", inner)
    ro2 = ref_object("X2", inner)  # different identity, same denoted structure
    assert not reference_equal(ro1, ro2)
    assert structural_equal(ro1, ro2)

    r1, r2 = node_ref("A"), node_ref("B")
    assert not structural_equal(r1, r2), "distinct NodeRefs are structurally different, never coerced by payload"


def test_structural_equal_recurses_into_nodes_and_pattern_slots():
    a = _obs("a", "O", "X", "Y", "OUT")
    b = _obs("b", "O", "X", "Y", "OUT")
    assert structural_equal(a, b)
    c = _obs("c", "O", "X", "Z", "OUT")
    assert not structural_equal(a, c)


# ---------------------------------------------------------------------------
# resolve_structure() transparency through every public entry point
# ---------------------------------------------------------------------------

def test_resolve_structure_unwraps_one_level_only():
    inner = _obs("z", "O", "a", "b", "c")
    ro = ref_object("X1", inner)
    assert resolve_structure(ro) is inner
    assert resolve_structure(inner) is inner  # a bare Node passes through unchanged
    assert resolve_structure(node_ref("R")) == node_ref("R")  # a bare NodeRef has no payload to resolve


def test_compare_and_compare_candidates_accept_refobject_wrapped_observations():
    a = _obs("a", "O", "X", "Y", "OUT")
    b = _obs("b", "O", "Y", "X", "OUT")
    direct = compare(a, b)
    assert direct is not None

    wrapped_direct = compare(ref_object("A", a), ref_object("B", b))
    assert wrapped_direct == direct

    assert compare_candidates(ref_object("A", a), ref_object("B", b)) == compare_candidates(a, b)


def test_pattern_is_applicable_apply_pattern_apply_is_applicable_accept_refobject_wrapped_pattern():
    a = _obs("a", "O", "X", "Y", "OUT")
    b = _obs("b", "O", "Y", "X", "OUT")
    pattern = compare(a, b)
    assert pattern is not None

    fresh = _obs("f", "O", "M", "N", "OUT")
    wrapped = ref_object("P1", pattern)

    assert pattern_is_applicable(wrapped, fresh) == pattern_is_applicable(pattern, fresh)
    assert apply(wrapped, fresh) == apply(pattern, fresh)
    assert is_applicable(wrapped, fresh) == is_applicable(pattern, fresh)

    from kernel2 import apply_pattern
    assert apply_pattern(wrapped, fresh) == apply_pattern(pattern, fresh)


def test_compare_raises_valueerror_not_attributeerror_for_non_node_input():
    import pytest
    with pytest.raises(ValueError):
        compare("not a node", "also not a node")


# ---------------------------------------------------------------------------
# NodeRef coreference in E18 shape discovery + application
# ---------------------------------------------------------------------------

def test_noderef_coreference_discovered_and_applied_correctly_end_to_end():
    """The regression this port fixed BEFORE merging (confirmed by execution,
    never introduced here): a repeated NodeRef gets the SAME variable number
    by design, but a naive apply used to index the RAW (non-deduplicated)
    flattened list by that number, silently dropping the distinct value and
    duplicating the coreferenced one instead. This must not happen here."""
    P, Q = node_ref("P"), node_ref("Q")
    inner_a = _obs("ia", "O", P, P, "_ia")
    a = _obs("da", "O", inner_a, Q, "OUT")   # flat(a) = [P, P, Q]
    inner_b = _obs("ib", "O", P, Q, "_ib")
    b = _obs("db", "O", P, inner_b, "OUT")   # flat(b) = [P, P, Q], different grouping

    pattern = compare(a, b)
    assert pattern is not None and pattern.kind == SHAPE_PATTERN

    R, S = node_ref("R"), node_ref("S")
    fresh_inner = _obs("fi", "O", R, R, "_fi")
    fresh = _obs("f", "O", fresh_inner, S, "OUT2")
    predicted = apply_tree_shape(pattern, fresh)
    assert predicted is not None

    def collect_refs(node):
        if isinstance(node, Node):
            out = []
            for c in node.children:
                out.extend(collect_refs(c))
            return out
        return [node] if isinstance(node, NodeRef) else []

    refs = collect_refs(predicted)
    r_count = sum(1 for r in refs if reference_equal(r, R))
    s_count = sum(1 for r in refs if reference_equal(r, S))
    assert r_count == 2 and s_count == 1, (
        f"coreference not preserved: R appeared {r_count} times, S {s_count} times "
        "(expected R twice via shared identity, S once)"
    )


def test_legacy_plain_string_path_is_unaffected_by_noderef_support():
    """Two leaves that coincidentally share a plain string value must NOT be
    treated as a coreference -- only an explicit NodeRef is. Mirrors the
    original E18 fixture that first surfaced the value-keyed bug."""
    inner_a = _obs("ia", "OP", "X", "Q", "_ia")
    a = _obs("da", "OP", inner_a, "X", "OUT")     # flat(a) = [X, Q, X] (coincidental repeat)
    inner_b = _obs("ib", "OP", "Q", "X", "_ib")
    b = _obs("db", "OP", "X", inner_b, "OUT")     # flat(b) = [X, Q, X], same flat list, different grouping

    pattern = compare(a, b)
    assert pattern is not None

    fresh_inner = _obs("fi", "OP", "P1", "P2", "_fi")
    fresh = _obs("f", "OP", fresh_inner, "P3", "OUT2")
    predicted = apply_tree_shape(pattern, fresh)
    assert predicted is not None

    def count_value(node, value):
        if isinstance(node, Node):
            return sum(count_value(c, value) for c in node.children)
        return 1 if node == value else 0

    assert count_value(predicted, "P1") == 1
    assert count_value(predicted, "P2") == 1
    assert count_value(predicted, "P3") == 1


def test_refobject_leaf_is_detected_as_coreference_via_its_own_ref_not_its_structure():
    """bind_reference() must fire for a RefObject's `.ref` too, not only a
    bare NodeRef -- a calculated object's identity, not the structure it
    denotes, drives coreference detection (a RefObject's `structure` is
    never inspected by _shape_template's rec())."""
    P = node_ref("P")
    # Deliberately DIFFERENT structures under the SAME ref P: bind_reference()
    # must key by `.ref.ref_id` alone, never by the (here, unequal) `.structure`.
    computed_1 = RefObject(P, "computed_value_A")
    computed_2 = RefObject(P, "computed_value_B")
    computed_other = RefObject(node_ref("Q"), "computed_value_A")  # different ref, matches computed_1's structure
    assert reference_equal(computed_1, computed_2), "same ref -> reference_equal, regardless of differing structure"
    assert not structural_equal(computed_1, computed_2), "different structure -> not structural_equal"
    assert not reference_equal(computed_1, computed_other)

    # compare_tree_shapes() requires the flattened sequences to be EXACTLY
    # (positionally) equal between a and b, so the SAME object (computed_1)
    # must sit at corresponding flat positions on both sides -- reusing
    # computed_2 there too would need it to equal computed_1 via `==`,
    # which the differing structure above deliberately breaks. The
    # coreference under test is "the same ref repeated inside ONE
    # observation", exactly mirroring the bare-NodeRef fixture above, now
    # with a RefObject leaf instead.
    inner_a = _obs("ia", "O", computed_1, computed_1, "_ia")  # ref P repeated: coreference
    a = _obs("da", "O", inner_a, "leaf", "OUT")                # flat(a) = [computed_1, computed_1, "leaf"]
    inner_b = _obs("ib", "O", computed_1, "leaf", "_ib")
    b = _obs("db", "O", computed_1, inner_b, "OUT")            # flat(b) = [computed_1, computed_1, "leaf"]

    pattern = compare(a, b)
    assert pattern is not None and pattern.kind == SHAPE_PATTERN
