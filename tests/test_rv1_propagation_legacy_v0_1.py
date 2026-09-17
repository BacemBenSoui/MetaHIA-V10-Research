"""R-V-1 propagation fix -- ported 2026-09-16/17 from an external variant
(kernel2.py, in the k3_spike_e13a2_preprod_2026-09-16.zip package), after
independent adversarial verification by execution.

Background: R-V-1 (reference/value separation) was wired into every PUBLIC
entry point via resolve_structure() in an earlier port, but six INTERNAL
primitives that decide whether two stored values are "the same" still used a
raw `==`/`!=`: compare_candidates()'s and _compare_observations()'s
varying-position scans, _all_reconciling_permutations(), _compare_patterns()'s
literal_constraint check, pattern_is_applicable()'s literal_constraint and
requires_source_equal checks, and aggregate_observations()'s constant-column
and cross-position dependency checks. A raw `==` is reference-aware for a
bare NodeRef (its only field IS the reference id) but NOT for a RefObject/
PatternRef, whose default equality requires both the reference and the
denoted structure to match -- confirmed by execution to silently treat a
same-reference/different-structure pair as merely unequal, rather than the
object inconsistency it actually is.

`_reference_consistency()`/`_kernel_values_equal()` close this gap at all
six sites with a three-way verdict: same reference + same (or coincidentally
equal) structure -> EQUAL; different reference -> DIFFERENT regardless of
structure; same reference + different structure -> ValueError (object
inconsistency), never silently resolved either way.

IMPORTANT CAVEAT FROM THE PORT AUDIT: the external package's own kernel2.py
was built on top of an OUTDATED, unfixed base copy (missing three bugs this
repo had already found and fixed in earlier rounds -- the pattern_is_applicable
kind guard, the NodeRef-coreference indexing fix, and compare_tree_shapes'
no-op guard). Their own regression suite ("24/24 pass") did not catch this
because its own coreference test used three MUTUALLY DISTINCT NodeRefs with
no repeated reference inside any single observation, so the distinct-variable-
count never fell below the raw-position count -- the exact condition the
indexing bug requires to manifest. Confirmed by an independent adversarial
probe using a GENUINELY repeated reference (mirroring test_noderef_refobject.py's
own fixture) before concluding the R-V-1 fix itself was sound and safe to
port on top of THIS repo's already-fixed kernel.py. This module tests only
the R-V-1 propagation fix; the three-bugs-still-fixed-here fact is covered by
test_noderef_refobject.py and test_patternref_structural_signature.py, which
this port re-ran unchanged (zero regression, 107/107) before this file was
added.
"""
from __future__ import annotations

import pytest

from kernel2 import (
    OBSERVATION,
    PATTERN,
    Node,
    NodeRef,
    PatternSlot,
    RefObject,
    aggregate_observations,
    compare,
    compare_candidates,
    is_applicable,
    node_ref,
    pattern_is_applicable,
    ref_object,
    reference_equal,
)
from kernel2 import _kernel_values_equal, _reference_consistency


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def _leaf(marker):
    return _obs(f"leaf_{marker}", "VAL", marker)


# ---------------------------------------------------------------------------
# Direct unit checks: _reference_consistency() / _kernel_values_equal()
# ---------------------------------------------------------------------------

def test_same_ref_same_structure_is_equal():
    a = ref_object("Z1", _leaf("m1"))
    b = RefObject(NodeRef("Z1"), _leaf("m1"))  # same ref_id, structurally-equal but distinct object
    assert _reference_consistency(a, b) == "EQUAL"
    assert _kernel_values_equal(a, b) is True


def test_different_ref_same_structure_is_different():
    a = ref_object("E1", _leaf("m1"))
    b = ref_object("E2", _leaf("m1"))
    assert _reference_consistency(a, b) == "DIFFERENT"
    assert _kernel_values_equal(a, b) is False


def test_same_ref_different_structure_raises_object_inconsistency():
    a = ref_object("D", _leaf("m1"))
    b = ref_object("D", _leaf("m2"))
    with pytest.raises(ValueError):
        _reference_consistency(a, b)
    with pytest.raises(ValueError):
        _kernel_values_equal(a, b)  # the ValueError must propagate, not be swallowed


def test_bare_noderef_pair_uses_ref_id_only():
    assert _reference_consistency(node_ref("P"), node_ref("P")) == "EQUAL"
    assert _reference_consistency(node_ref("P"), node_ref("Q")) == "DIFFERENT"


def test_reference_vs_plain_value_is_always_different():
    assert _reference_consistency(node_ref("P"), "plain string") == "DIFFERENT"
    assert _kernel_values_equal(ref_object("X", _leaf("m1")), 42) is False


def test_kernel_values_equal_falls_back_to_plain_equality_for_non_reference_values():
    assert _kernel_values_equal("A", "A") is True
    assert _kernel_values_equal("A", "B") is False
    assert _kernel_values_equal(3, 3) is True


# ---------------------------------------------------------------------------
# End-to-end: pattern_is_applicable() / is_applicable() (requires_source_equal
# and literal_constraint), and aggregate_observations()'s own two checks.
# ---------------------------------------------------------------------------

def test_aggregate_observations_requires_source_equal_end_to_end():
    K9 = node_ref("K9")
    obs_a = _obs("oa", ref_object("A", _leaf("m1")), K9, ref_object("A", _leaf("m1")))
    obs_b = _obs("ob", ref_object("B", _leaf("m1")), K9, ref_object("B", _leaf("m1")))
    obs_c = _obs("oc", ref_object("C", _leaf("m1")), K9, ref_object("C", _leaf("m1")))
    pattern = aggregate_observations([obs_a, obs_b, obs_c])
    assert pattern is not None

    # same reference, same structure at both dependent positions: applicable.
    fresh_ok = _obs("f_ok", ref_object("D2", _leaf("m1")), K9, ref_object("D2", _leaf("m1")))
    assert pattern_is_applicable(pattern, fresh_ok) is True
    assert is_applicable(pattern, fresh_ok) is True

    # different references at the two dependent positions: correctly rejected.
    fresh_diff_ref = _obs("f_diff", ref_object("E1", _leaf("m1")), K9, ref_object("E2", _leaf("m1")))
    assert pattern_is_applicable(pattern, fresh_diff_ref) is False

    # same reference reused with a DIFFERENT denoted structure: object
    # inconsistency, must raise -- not silently return False.
    fresh_inconsistent = _obs("f_inc", ref_object("D", _leaf("m1")), K9, ref_object("D", _leaf("m2")))
    with pytest.raises(ValueError):
        pattern_is_applicable(pattern, fresh_inconsistent)
    with pytest.raises(ValueError):
        is_applicable(pattern, fresh_inconsistent)

    # raw-string fallback path (no RefObject at all) must be completely
    # unaffected -- the original E19 violation case.
    violating_raw = _obs("violating_raw", "FOO", K9, "BAR")
    assert pattern_is_applicable(pattern, violating_raw) is False


def test_aggregate_observations_constant_column_end_to_end():
    const_value = ref_object("CONST", _leaf("m1"))
    observations = [_obs(f"kc{i}", f"v{i}", const_value, f"v{i}") for i in range(3)]
    pattern = aggregate_observations(observations)
    assert pattern is not None
    const_slot = pattern.children[1]
    assert const_slot.literal_constraint is not None
    assert reference_equal(const_slot.literal_constraint, const_value)

    # same reference, different structure at the constant position: object
    # inconsistency, must raise via the literal_constraint check.
    fresh_inconsistent = _obs("f_const_inc", "v9", ref_object("CONST", _leaf("OTHER")), "v9")
    with pytest.raises(ValueError):
        pattern_is_applicable(pattern, fresh_inconsistent)


# ---------------------------------------------------------------------------
# The OTHER four sites: compare_candidates(), _all_reconciling_permutations(),
# _compare_observations() (via compare()), and _compare_patterns() -- none of
# these were exercised directly by the external package's own test suite,
# which only checked pattern_is_applicable()/aggregate_observations() end to
# end. Added here so a future regression at any of the six sites is caught
# at its own call site, not just downstream of aggregate_observations().
# ---------------------------------------------------------------------------

def test_compare_candidates_treats_same_ref_same_structure_as_non_varying():
    same_value = ref_object("SAME", _leaf("m1"))
    obs_1 = _obs("cc1", same_value, "fixed", "R")
    obs_2 = _obs("cc2", ref_object("SAME", _leaf("m1")), "fixed", "R")  # same ref+structure, different object
    candidates = compare_candidates(obs_1, obs_2)
    # identical in every position once reference-aware: nothing to reify.
    assert candidates == ()


def test_compare_raises_object_inconsistency_directly_from_the_top_level_varying_scan():
    a = _obs("a", ref_object("D", _leaf("m1")), "X", "OUT")
    b = _obs("b", ref_object("D", _leaf("m2")), "Y", "OUT")
    with pytest.raises(ValueError):
        compare(a, b)


def test_compare_candidates_raises_object_inconsistency_from_all_reconciling_permutations():
    """Exercises _all_reconciling_permutations() specifically: the
    inconsistent pair must be reached through the permutation search itself
    (candidate position differs from where the pair first appears), not just
    the top-level varying-position scan."""
    a = _obs("c", "X", ref_object("D", _leaf("m1")), "OUT")
    b = _obs("d", ref_object("D", _leaf("m2")), "X", "OUT")
    with pytest.raises(ValueError):
        compare_candidates(a, b)


def test_compare_patterns_raises_object_inconsistency_from_literal_constraint_merge():
    p1 = Node("p1", PATTERN, (PatternSlot(source_position=0, literal_constraint=ref_object("D", _leaf("m1"))),))
    p2 = Node("p2", PATTERN, (PatternSlot(source_position=0, literal_constraint=ref_object("D", _leaf("m2"))),))
    with pytest.raises(ValueError):
        compare(p1, p2)


def test_legacy_noderef_and_plain_value_paths_are_completely_unaffected():
    """Sanity check that R-V-1 propagation changed nothing for the paths
    every prior test (E13-A.2 through E19) already exercises: plain strings,
    and a bare NodeRef used exactly like a plain leaf (no RefObject wrapper)."""
    a = _obs("a", "O", "X", "Y", "OUT")
    b = _obs("b", "O", "Y", "X", "OUT")
    assert compare(a, b) is not None  # unchanged swap discovery

    P, Q = node_ref("P"), node_ref("Q")
    c = _obs("c", "O", P, Q, "OUT")
    d = _obs("d", "O", Q, P, "OUT")
    assert compare(c, d) is not None  # bare NodeRef leaves behave exactly like strings here
