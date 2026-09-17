"""E19 — multi-observation aggregate discovery (ported 2026-09-16, see
documentation/CORPUS_V2_0_RAPPORT_TESTS_ET_CORRECTIONS_2026-09-16.md).

compare()'s pairwise permutation search is structurally incapable of
discovering a genuine multi-observation invariant like "this column is
always constant" or "these two columns always agree": two observations can
never distinguish a real invariant from a coincidence. aggregate_observations()
takes >=3 observations and, for each position, infers either a constant
value or a unique positional dependency that holds across all of them --
producing an ordinary PATTERN node, reusing apply_pattern()/
pattern_is_applicable() rather than a bespoke application mechanism.

Every test either reproduces a real bug found and fixed BEFORE this port
(pattern_is_applicable() silently ignoring a violated column dependency), or
exercises the method's own honestly-disclosed limits.
"""
from __future__ import annotations

import random

from kernel2 import (
    OBSERVATION,
    Node,
    aggregate_observations,
    apply,
    apply_pattern,
    discover_hypothesis,
    is_applicable,
    pattern_is_applicable,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def _sig(pattern):
    return [(s.source_position, s.literal_constraint, s.requires_source_equal) for s in pattern.children]


def test_discovers_a_constant_column_and_a_mutual_positional_dependency():
    """The reported worked example: Z(A,K9)->A / Z(B,K9)->B / Z(C,K9)->C.
    Column 2 ("K9") is constant; columns 1 and 3 mutually depend on each
    other (a positional identity, not expressible from only 2 examples)."""
    base = [_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B"), _obs("z3", "Z", "C", "K9", "C")]
    pattern = aggregate_observations(base)
    assert pattern is not None
    assert _sig(pattern) == [(0, "Z", False), (3, None, True), (2, "K9", False), (1, None, True)]


def test_fewer_than_three_observations_yields_nothing():
    """compare() itself cannot discover this kind of invariant at all (only
    2 examples can never rule out coincidence) -- aggregate_observations()
    enforces the same floor explicitly rather than guessing from 2."""
    two = [_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B")]
    assert aggregate_observations(two) is None


def test_ambiguous_multi_column_match_is_correctly_refused():
    """Three positions that are all identical to each other across every
    observation: the target/source mapping is genuinely ambiguous (more than
    one column could equally explain the dependency) -- refused, not guessed,
    consistent with compare()'s own active-ambiguity-refusal stance."""
    amb = [_obs("m1", "Z", "A", "A", "A"), _obs("m2", "Z", "B", "B", "B"), _obs("m3", "Z", "C", "C", "C")]
    assert aggregate_observations(amb) is None


def test_discovered_pattern_is_order_independent():
    base = [_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B"), _obs("z3", "Z", "C", "K9", "C")]
    p1 = aggregate_observations(base)
    shuffled = base[:]
    random.Random(42).shuffle(shuffled)
    p2 = aggregate_observations(shuffled)
    assert _sig(p1) == _sig(p2)


def test_width_mismatched_observations_are_rejected_not_force_aligned():
    mismatched = [
        _obs("w1", "Z", "A", "K9", "A"),
        _obs("w2", "Z", "B", "K9", "B"),
        _obs("w3", "Z", "C", "K9"),  # one field short
    ]
    assert aggregate_observations(mismatched) is None


def test_discovered_pattern_integrates_with_apply_pattern_on_unseen_data():
    """No separate application mechanism needed for this discovery method --
    the discovered Node is an ordinary PATTERN, usable through the same
    apply_pattern()/apply() already validated for compare()-discovered
    patterns since E13-A.2."""
    base = [_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B"), _obs("z3", "Z", "C", "K9", "C")]
    pattern = aggregate_observations(base)
    fresh = _obs("z4", "Z", "D", "K9", "D")
    predicted = apply_pattern(pattern, fresh)
    assert predicted is not None and predicted.children == ("Z", "D", "K9", "D")
    assert apply(pattern, fresh) == predicted


def test_pattern_is_applicable_checks_the_column_dependency_not_just_literals():
    """THE confirmed bug fixed before this port: pattern_is_applicable() only
    checked literal_constraint slots, so an observation that violated the
    discovered Z(x,K9)=x dependency (arg != output) was silently reported as
    applicable, and apply_pattern() produced a nonsensical, unflagged
    prediction. Fixed via PatternSlot.requires_source_equal."""
    base = [_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B"), _obs("z3", "Z", "C", "K9", "C")]
    pattern = aggregate_observations(base)

    matching = _obs("ok", "Z", "D", "K9", "D")
    assert pattern_is_applicable(pattern, matching) is True
    assert is_applicable(pattern, matching) is True

    violating = _obs("bad", "Z", "FOO", "K9", "BAR")  # FOO != BAR: violates the discovered dependency
    assert pattern_is_applicable(pattern, violating) is False
    assert is_applicable(pattern, violating) is False
    # apply_pattern still computes something (by design, same "Apply never
    # refuses, Applicable is separate" contract as everywhere else in this
    # kernel) -- it's on the caller to check applicability first if the
    # distinction matters to them.
    assert apply_pattern(pattern, violating) is not None


def test_a_coincidental_three_observation_match_is_an_honest_limit_not_a_bug():
    """With only 3 observations, a purely coincidental column match (no
    underlying relationship at all) is indistinguishable from a genuine
    dependency -- demonstrated concretely rather than asserted. This is
    consistent with the function's own documented contract ("holds across
    every SUPPLIED observation"), not a defect: the important correctness
    property is that pattern_is_applicable() correctly flags a later
    observation that breaks the coincidence, which it now does."""
    coincidence = [_obs("c1", "Z", "SAME1", "SAME1"), _obs("c2", "Z", "SAME2", "SAME2"), _obs("c3", "Z", "SAME3", "SAME3")]
    pattern = aggregate_observations(coincidence)
    assert pattern is not None  # the method cannot know this was a coincidence from 3 examples alone

    held_out = _obs("c4", "Z", "LEFT", "RIGHT")  # the coincidence does not hold here
    assert pattern_is_applicable(pattern, held_out) is False
    predicted = apply_pattern(pattern, held_out)
    assert predicted is not None  # Apply still computes; Applicable already warned the caller


def test_discover_hypothesis_wraps_with_correct_lineage_and_status():
    base = [_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B"), _obs("z3", "Z", "C", "K9", "C")]
    hyp = discover_hypothesis(base)
    assert hyp is not None
    assert set(hyp.supporting_ids) == {"z1", "z2", "z3"}
    assert hyp.status == "SUPPORTED"


def test_discover_hypothesis_returns_none_when_aggregation_fails():
    assert discover_hypothesis([_obs("z1", "Z", "A", "K9", "A"), _obs("z2", "Z", "B", "K9", "B")]) is None
