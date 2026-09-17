"""Unit tests for the generic K3 spike mechanics (kernel.py) in isolation from
the micro-corpus / experiment narrative — edge cases of compare()/apply_pattern()."""
from __future__ import annotations

import pytest

from kernel2 import (
    OBSERVATION,
    Hypothesis,
    Node,
    PatternSlot,
    apply_pattern,
    compare,
    pattern_is_applicable,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def test_compare_finds_a_two_slot_swap():
    a = _obs("a", "O", "A", "B", "C")
    b = _obs("b", "O", "B", "A", "C")
    pattern = compare(a, b)
    assert pattern is not None
    assert [(s.source_position, s.literal_constraint) for s in pattern.children] == [
        (0, "O"), (2, None), (1, None), (3, "C"),
    ]
    assert pattern.provenance == ("a", "b")


def test_compare_returns_none_for_identical_observations():
    a = _obs("a", "O", "A", "B", "C")
    b = _obs("b", "O", "A", "B", "C")
    assert compare(a, b) is None


def test_compare_returns_none_for_different_shapes():
    a = _obs("a", "O", "A", "B", "C")
    b = _obs("b", "O", "A", "B")
    assert compare(a, b) is None


def test_compare_returns_none_when_no_permutation_reconciles():
    # Non-commutative: output changes too, no permutation can hold it frozen.
    a = _obs("a", "SUB", "M", "N", "D1")
    b = _obs("b", "SUB", "N", "M", "D2")
    assert compare(a, b) is None


def test_compare_rejects_mismatched_kinds():
    obs = _obs("a", "O", "A", "B", "C")
    pattern = Node(node_id="p", kind="PATTERN", children=(PatternSlot(0, "O"),))
    with pytest.raises(ValueError):
        compare(obs, pattern)


def test_abstraction_merges_two_compatible_local_patterns():
    p1 = compare(_obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C"))
    p2 = compare(_obs("s3", "AND", "P", "Q", "R"), _obs("s4", "AND", "Q", "P", "R"))
    merged = compare(p1, p2)
    assert merged is not None
    # positions 0 and 3 were frozen-but-different literals across instances: generalized away.
    assert [(s.source_position, s.literal_constraint) for s in merged.children] == [
        (0, None), (2, None), (1, None), (3, None),
    ]


def test_abstraction_rejects_incompatible_patterns():
    swap = compare(_obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C"))
    identity_like = Node(
        node_id="p_identity",
        kind="PATTERN",
        children=(
            PatternSlot(0, "X"), PatternSlot(1, None), PatternSlot(2, None), PatternSlot(3, "Y"),
        ),
    )
    # same positions free/frozen shape but position 1 maps to itself here, not to 2:
    # different underlying transformation -> must not merge.
    assert compare(swap, identity_like) is None


def test_apply_pattern_predicts_the_mirrored_observation():
    pattern = compare(_obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C"))
    unseen = _obs("h1", "O", "R1", "R2", "C")
    predicted = apply_pattern(pattern, unseen)
    assert predicted is not None
    assert predicted.children == ("O", "R2", "R1", "C")
    assert predicted.provenance == (pattern.node_id, "h1")


def test_pattern_is_applicable_is_separate_from_apply():
    """Source discussion, section 12: 'Exploration != application automatique'
    — Applicable and Apply must be separate mechanisms. pattern_is_applicable()
    reports the mismatch; apply_pattern() still computes a (garbage-in,
    garbage-out) prediction rather than silently refusing to run — refusing
    would make it useless for contradiction detection (see test_e13a2_*)."""
    pattern = compare(_obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C"))
    wrong_operator = _obs("h2", "DIFFERENT_OP", "R1", "R2", "C")
    assert pattern_is_applicable(pattern, wrong_operator) is False
    predicted = apply_pattern(pattern, wrong_operator)
    assert predicted is not None
    assert predicted.children == ("DIFFERENT_OP", "R2", "R1", "C")


def test_hypothesis_status_transitions_and_conserves_support():
    pattern = compare(_obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C"))
    hyp = Hypothesis(hypothesis_id="h", pattern=pattern)
    assert hyp.status == "UNKNOWN"
    hyp = hyp.with_support("s1").with_support("s2")
    assert hyp.status == "SUPPORTED"
    hyp = hyp.with_contradiction("s1b")
    assert hyp.status == "CONTRADICTED"
    # the contradiction must never silently erase prior support
    assert hyp.supporting_ids == ("s1", "s2")
    assert hyp.contradicting_ids == ("s1b",)
