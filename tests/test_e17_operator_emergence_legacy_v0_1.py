"""E17 — operator emergence (Corpus V2.0 roadmap, documentation/CORPUS_V2_0_ROADMAP_2026-09-16.md).

The most speculative experiment in the sequence -- explicitly marked OPEN,
never resolved even conceptually, in the source discussion (its own E12).

PASS criterion (from the roadmap): a Node plays the role of an operator in a
composition without having been specially provided as such upfront.
FAIL criterion: no emergence observed beyond a reapplication of already-known
patterns.

What this experiment actually establishes, precisely (no more, no less):
  1. A discovered PATTERN node (Omega) -- never labeled "operator" anywhere
     in kernel.py -- can be embedded as an ordinary child of a new
     OBSERVATION, exactly like any opaque label or nested OBSERVATION (E15).
  2. compare(), unchanged in its dispatch logic (only the nesting-detection
     kind check was relaxed from "both OBSERVATION" to "both the same
     kind"), recurses INTO that embedded operator and discovers a
     meta-regularity ACROSS two different operators -- i.e. Compare applied
     one level higher than data, onto operators themselves.
  3. apply_pattern(), similarly relaxed, projects that meta-regularity onto
     a third, previously uninvolved operator, producing a new PATTERN that
     -- once a real composition bug (found and fixed below) was corrected --
     behaves identically to independently discovering that operator's own
     regularity from scratch.

What it does NOT establish (consistent with the roadmap's own framing of
E17 as the most speculative step): a totally novel operator with no
structural precedent in any data given. Every operator that emerges here was
still discovered from at least one pair of concrete observations -- nothing
is generated from nothing. test_no_emergence_without_any_precedent below
makes this boundary explicit and checks it holds.
"""
from __future__ import annotations

from kernel2 import (
    OBSERVATION,
    PATTERN,
    Node,
    apply_pattern,
    compare,
    pattern_is_applicable,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def _discover(a_id, b_id, op, x, y, out):
    return compare(_obs(a_id, op, x, y, out), _obs(f"{b_id}", op, y, x, out))


def test_a_discovered_pattern_is_a_plain_node_playing_an_unlabeled_role():
    """Baseline, not new by itself: Omega is produced by the exact same
    compare() used throughout E13-A.2 -- nothing in kernel.py ever calls it
    "an operator". It is just a Node of kind PATTERN."""
    omega = _discover("s1", "s2", "O", "A", "B", "C")
    assert omega.kind == PATTERN
    assert isinstance(omega, Node)


def test_compare_recurses_through_the_operator_level_to_find_a_meta_regularity():
    """The actually new part: two operators (Omega_a from an "O" family,
    Omega_b from an unrelated "AND" family) are embedded as the payload of
    two new observations. compare() on those two observations must recurse
    INTO the operators themselves (both are PATTERN-kind, the relaxed nesting
    check) and discover that they share the same underlying transformation,
    generalizing away their concrete literal differences -- exactly the
    abstraction mechanism already validated at the data level, now
    demonstrated one level higher, on the operators."""
    omega_a = _discover("s1", "s2", "O", "A", "B", "C")
    omega_b = _discover("s3", "s4", "AND", "P", "Q", "R")

    meta_a = _obs("meta_a", "USES", omega_a)
    meta_b = _obs("meta_b", "USES", omega_b)

    outer = compare(meta_a, meta_b)
    assert outer is not None
    assert outer.children[0].literal_constraint == "USES"
    operator_slot = outer.children[1]
    assert operator_slot.nested_pattern is not None

    meta_pattern = operator_slot.nested_pattern
    assert [ (s.source_position, s.literal_constraint) for s in meta_pattern.children ] == [
        (0, None), (2, None), (1, None), (3, None),
    ]  # fully generalized: operator identity ("O" vs "AND") and output ("C" vs "R") both differ across the two, so both generalize


def test_apply_projects_the_meta_regularity_onto_a_third_unseen_operator():
    """The real E17 claim: Apply, extended through the operator level, takes
    the meta-regularity discovered above and projects it onto Omega_c -- an
    operator discovered from a THIRD, independent family (NOR), never
    involved in discovering the meta-pattern. The result must be a valid
    PATTERN node (an operator itself), usable exactly like any
    independently-discovered one."""
    omega_a = _discover("s1", "s2", "O", "A", "B", "C")
    omega_b = _discover("s3", "s4", "AND", "P", "Q", "R")
    omega_c = _discover("s5", "s6", "NOR", "X", "Y", "Z")

    outer = compare(_obs("meta_a", "USES", omega_a), _obs("meta_b", "USES", omega_b))
    meta_c = _obs("meta_c", "USES", omega_c)

    assert pattern_is_applicable(outer, meta_c) is True
    predicted_meta = apply_pattern(outer, meta_c)
    assert predicted_meta is not None

    predicted_omega = predicted_meta.children[1]
    assert predicted_omega.kind == PATTERN  # Apply into a PATTERN yields a PATTERN, not an OBSERVATION


def test_the_projected_operator_is_semantically_faithful_not_just_well_typed():
    """This is the bug found and fixed while building E17: naively relocating
    a PatternSlot without rebasing its own internal source_position silently
    produced a DIFFERENT, wrong operator (a swap degenerated into an
    identity). After the fix, the projected operator must be usable, and must
    behave exactly like Omega_c itself when applied to fresh data -- not just
    type-check as *some* PATTERN node."""
    omega_a = _discover("s1", "s2", "O", "A", "B", "C")
    omega_b = _discover("s3", "s4", "AND", "P", "Q", "R")
    omega_c = _discover("s5", "s6", "NOR", "X", "Y", "Z")

    outer = compare(_obs("meta_a", "USES", omega_a), _obs("meta_b", "USES", omega_b))
    predicted_meta = apply_pattern(outer, _obs("meta_c", "USES", omega_c))
    predicted_omega = predicted_meta.children[1]

    # same slot structure as independently discovering omega_c's own regularity
    assert [(s.source_position, s.literal_constraint) for s in predicted_omega.children] == \
           [(s.source_position, s.literal_constraint) for s in omega_c.children]

    fresh = _obs("fresh", "NOR", "P1", "P2", "Z")
    assert apply_pattern(predicted_omega, fresh).children == apply_pattern(omega_c, fresh).children
    assert apply_pattern(predicted_omega, fresh).children == ("NOR", "P2", "P1", "Z")


def test_incompatible_operators_correctly_fail_to_yield_a_meta_regularity():
    """Negative control: two operators with genuinely different underlying
    transformations (swap positions 1,2 vs swap positions 2,3, at arity 5)
    must NOT be forced into a fake meta-regularity when embedded and
    compared -- the same incompatibility check already validated at the
    plain pattern-abstraction level (E16) must still hold one level up."""
    swap12 = compare(
        _obs("t1", "TERN", "A", "B", "K", "C"), _obs("t2", "TERN", "B", "A", "K", "C"),
    )
    swap23 = compare(
        _obs("t3", "SHIFT", "M", "X", "Y", "D"), _obs("t4", "SHIFT", "M", "Y", "X", "D"),
    )
    meta_a = _obs("meta_a", "USES", swap12)
    meta_b = _obs("meta_b", "USES", swap23)
    assert compare(meta_a, meta_b) is None


def test_no_emergence_without_any_precedent():
    """Explicit honesty boundary (matches the roadmap's FAIL criterion and
    the source discussion's own caution that full novel-operator generation
    remains OPEN): every operator used above was discovered from at least
    one real pair of observations. Nothing here spontaneously invents a
    transformation with zero structural precedent -- confirmed by checking
    that a "meta-observation" wrapping something that is NOT a discovered
    pattern at all (compare() found no regularity, so there is no operator
    to embed) simply cannot be constructed as a nested_pattern slot: the
    only Nodes ever embedded in this experiment are ones compare() itself
    already produced from concrete data."""
    non_commutative_pattern = compare(
        _obs("s7", "SUB", "M", "N", "D1"), _obs("s8", "SUB", "N", "M", "D2"),
    )
    assert non_commutative_pattern is None  # no regularity discovered: nothing to embed as an operator
