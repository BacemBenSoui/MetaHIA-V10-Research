"""Adversarial probe for the permutation-ambiguity finding (2026-09-16), and
regression coverage for its fix: compare() now fails closed on ambiguity
instead of silently picking a permutation, and compare_candidates() exposes
every viable candidate for callers that want to carry multiple competing
hypotheses forward (matching the project's "never silently discard a viable
alternative" stance already used for contradictions, see Hypothesis).
"""
from __future__ import annotations

from kernel2 import OBSERVATION, Node, apply_pattern, compare, compare_candidates


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def test_compare_fails_closed_on_a_genuinely_ambiguous_pair():
    """a=(X,X,Y,Y), b=(Y,Y,X,X): two distinct permutations reconcile them
    equally well ((1,2)->(3,4) & (3,4)->(1,2), or the other pairing). compare()
    must not pick one arbitrarily -- it must report None, exactly like the
    "no permutation reconciles them" case, since from compare()'s contract
    both are "not a single well-defined answer"."""
    a = _obs("a", "X", "X", "Y", "Y")
    b = _obs("b", "Y", "Y", "X", "X")
    assert compare(a, b) is None


def test_compare_candidates_exposes_every_viable_permutation():
    """The same pair, through compare_candidates(): the ambiguity is worse
    than a simple two-way tie -- with a=(X,X,Y,Y), b=(Y,Y,X,X), the {X,X}
    block can map onto {2,3} in either order, independently of how the {Y,Y}
    block maps onto {0,1}, giving 2x2 = 4 equally valid permutations, all
    present, each internally consistent, and diverging into 4 DIFFERENT
    predictions on unseen data with no repeated values -- exactly the risk a
    silent single choice would have hidden."""
    a = _obs("a", "X", "X", "Y", "Y")
    b = _obs("b", "Y", "Y", "X", "X")
    candidates = compare_candidates(a, b)
    assert len(candidates) == 4

    # every candidate reproduces b exactly when applied back to a (each is a
    # genuinely valid explanation of the training pair, not a wrong guess)
    for c in candidates:
        assert apply_pattern(c, a).children == b.children

    # on data with no repeated values, the candidates diverge into 4 distinct,
    # mutually incompatible predictions
    unseen = _obs("h", "P", "Q", "R", "S")
    predictions = {apply_pattern(c, unseen).children for c in candidates}
    assert predictions == {
        ("R", "S", "P", "Q"), ("R", "S", "Q", "P"),
        ("S", "R", "P", "Q"), ("S", "R", "Q", "P"),
    }


def test_compare_candidates_matches_compare_in_the_unambiguous_case():
    """No duplicate values -> exactly one candidate, identical to compare()'s
    result -- compare_candidates() is a strict generalization, not a
    different algorithm."""
    a = _obs("a", "O", "A", "B", "C")
    b = _obs("b", "O", "B", "A", "C")
    single = compare(a, b)
    candidates = compare_candidates(a, b)
    assert single is not None
    assert len(candidates) == 1
    assert candidates[0] == single


def test_compare_candidates_returns_empty_for_incomparable_or_identical_pairs():
    identical = compare_candidates(_obs("a", "O", "A", "B", "C"), _obs("b", "O", "A", "B", "C"))
    assert identical == ()

    non_commutative = compare_candidates(
        _obs("a", "SUB", "M", "N", "D1"), _obs("b", "SUB", "N", "M", "D2")
    )
    assert non_commutative == ()
