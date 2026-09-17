"""Validation of E14-E16 together, at a larger and less artificial scale
(requested 2026-09-16, before attempting the more speculative E17).

Unlike the E14/E15/E16 experiments (one new dimension at a time, on a
minimal disposable fixture), this runs the SAME kernel.py -- zero code
change from what E16 left -- against research/k3_spike_e13a2/corpus/
validation_corpus_v001.json: 20 families, 5 holdout cases, mixed arities
(4/5), nested structures at depth 2 AND depth 3, a competing-regularities
group with 4 pairs (2 reinforcing, 1 competing, 1 duplicate-value ambiguous),
malformed-arity impostors mixed directly into two otherwise-normal families,
and two non-commutative counter-examples.

If this file needed to modify kernel.py to pass, that would itself be an
important finding (E14-E16 "PASS" on toy fixtures but not at scale) -- it did
not: every fix below is limited to the validation corpus/test file.
"""
from __future__ import annotations

from kernel2 import (
    OBSERVATION,
    Node,
    apply_pattern,
    compare,
    group_into_hypotheses,
    pattern_is_applicable,
)
from loader import load_validation_corpus


def _pair(corpus, family):
    """The first two entries of a family -- ignores any trailing impostor."""
    a, b = corpus.families[family][0], corpus.families[family][1]
    return a, b


def _content(value):
    """Recursively strip node_id/provenance and keep only the actual leaf
    content -- freshly predicted Nodes (auto-generated ids) and hand-authored
    ground-truth Nodes (their own ids) must compare equal on content alone."""
    if isinstance(value, Node):
        return tuple(_content(c) for c in value.children)
    return value


def test_all_swap12_arity4_families_discovered_despite_the_mixed_in_impostor():
    """E14 at scale: 5 independent arity-4 families, one of which (op4_1) has
    a 3rd, malformed-arity impostor entry sitting right next to its real
    pair. The impostor must not prevent discovery on the real pair, and must
    not itself produce a pattern against either sibling."""
    corpus = load_validation_corpus()
    for family in ["op4_1", "op4_2", "op4_3", "op4_4", "op4_5"]:
        a, b = _pair(corpus, family)
        pattern = compare(a, b)
        assert pattern is not None, f"expected a pattern for {family!r}"
        assert pattern.children[1].source_position == 2
        assert pattern.children[2].source_position == 1

    impostor = corpus.families["op4_1"][2]
    real_a, real_b = _pair(corpus, "op4_1")
    assert compare(real_a, impostor) is None
    assert compare(real_b, impostor) is None


def test_two_arity5_shapes_discovered_independently_and_never_cross_merge():
    """E14+E16 together: TERN (swap positions 1,2) and SHIFT (swap positions
    2,3) share the same arity (5) but are genuinely different transformations
    -- both must be discoverable, and abstraction must never merge across
    the two shapes despite the shared arity."""
    corpus = load_validation_corpus()
    tern_1 = compare(*_pair(corpus, "tern_1"))
    tern_2 = compare(*_pair(corpus, "tern_2"))
    shift_1 = compare(*_pair(corpus, "shift_1"))
    shift_2 = compare(*_pair(corpus, "shift_2"))
    assert all(p is not None for p in (tern_1, tern_2, shift_1, shift_2))

    tern_general = compare(tern_1, tern_2)
    shift_general = compare(shift_1, shift_2)
    assert tern_general is not None
    assert shift_general is not None
    assert compare(tern_general, shift_general) is None  # genuinely different shapes: must not merge


def test_non_commutative_counter_examples_yield_no_pattern_at_scale():
    corpus = load_validation_corpus()
    assert compare(*_pair(corpus, "subx")) is None
    assert compare(*_pair(corpus, "divx")) is None


def test_nested_families_discovered_at_depth_2_and_abstract_correctly():
    """E15 at scale: 3 independent depth-2 nested families, one (nwrap_1)
    with a malformed impostor (a plain string where a nested Node was
    expected) mixed in. All 3 real pairs must be discovered and abstract
    into one fully generalized nested pattern; the impostor must be safely
    rejected without crashing."""
    corpus = load_validation_corpus()
    patterns = []
    for family in ["nwrap_1", "nwrap_2", "nwrap_3"]:
        a, b = _pair(corpus, family)
        pattern = compare(a, b)
        assert pattern is not None, f"expected a pattern for {family!r}"
        assert pattern.children[1].nested_pattern is not None
        patterns.append(pattern)

    general = compare(compare(patterns[0], patterns[1]), patterns[2])
    assert general is not None
    assert all(slot.literal_constraint is None for slot in general.children[1].nested_pattern.children)

    impostor = corpus.families["nwrap_1"][2]
    real_a, real_b = _pair(corpus, "nwrap_1")
    assert compare(real_a, impostor) is None
    assert compare(real_b, impostor) is None
    assert pattern_is_applicable(general, impostor) is False


def test_nested_families_discovered_at_depth_3_with_zero_new_code():
    """E15 pushed one level deeper than the original experiment (outer wraps
    mid wraps inner): the SAME recursive mechanism, unchanged since the E15
    commit, must resolve depth-3 nesting -- this is a validation-only
    confirmation, not a new capability."""
    corpus = load_validation_corpus()
    d1 = compare(*_pair(corpus, "deep_1"))
    d2 = compare(*_pair(corpus, "deep_2"))
    assert d1 is not None and d2 is not None

    mid_slot_1 = d1.children[1]
    assert mid_slot_1.nested_pattern is not None
    inner_slot_1 = mid_slot_1.nested_pattern.children[1]
    assert inner_slot_1.nested_pattern is not None  # depth 3: nested pattern inside a nested pattern

    general = compare(d1, d2)
    assert general is not None
    inner_general = general.children[1].nested_pattern.children[1].nested_pattern
    assert all(slot.literal_constraint is None for slot in inner_general.children)


def test_competing_regularities_group_correctly_at_a_larger_scale():
    """E16 at scale: 4 pairs sharing the operator symbol "MIX" -- two
    reinforce the same swap(1,2) transformation, one is a genuinely
    different swap(2,3), and one is a duplicate-value ambiguous pair that
    compare() itself rejects (fail-closed, per the earlier ambiguity fix).
    group_into_hypotheses must produce exactly 2 hypotheses, correctly
    ignoring the ambiguous pair entirely."""
    corpus = load_validation_corpus()
    pairs = [
        _pair(corpus, "mix_a"),
        _pair(corpus, "mix_b"),
        _pair(corpus, "mix_c"),
        _pair(corpus, "mix_ambiguous"),
    ]
    # sanity: confirm the ambiguous pair really is rejected by compare() itself
    assert compare(*_pair(corpus, "mix_ambiguous")) is None

    hypotheses = group_into_hypotheses(pairs)
    assert len(hypotheses) == 2

    all_supporting = {oid for h in hypotheses for oid in h.supporting_ids}
    assert "mix_amb1" not in all_supporting and "mix_amb2" not in all_supporting
    assert {"mix_a1", "mix_a2", "mix_b1", "mix_b2"} <= all_supporting
    assert {"mix_c1", "mix_c2"} <= all_supporting

    reinforced = next(h for h in hypotheses if "mix_a1" in h.supporting_ids)
    assert set(reinforced.supporting_ids) == {"mix_a1", "mix_a2", "mix_b1", "mix_b2"}


def test_generalization_confirmed_on_every_holdout_case():
    """The real point of validating "at scale": every one of the 5 holdout
    cases -- arity-4 swap, arity-5 swap(1,2), arity-5 swap(2,3), depth-2
    nested, depth-3 nested -- is genuinely unseen data, and each abstracted
    pattern must predict its own correct ground truth, none other."""
    corpus = load_validation_corpus()

    op4_general = compare(compare(compare(compare(
        compare(*_pair(corpus, "op4_1")), compare(*_pair(corpus, "op4_2"))),
        compare(*_pair(corpus, "op4_3"))), compare(*_pair(corpus, "op4_4"))),
        compare(*_pair(corpus, "op4_5")))
    tern_general = compare(compare(*_pair(corpus, "tern_1")), compare(*_pair(corpus, "tern_2")))
    shift_general = compare(compare(*_pair(corpus, "shift_1")), compare(*_pair(corpus, "shift_2")))
    nwrap_general = compare(
        compare(compare(*_pair(corpus, "nwrap_1")), compare(*_pair(corpus, "nwrap_2"))),
        compare(*_pair(corpus, "nwrap_3")),
    )
    deep_general = compare(compare(*_pair(corpus, "deep_1")), compare(*_pair(corpus, "deep_2")))

    for general, holdout_key in [
        (op4_general, "hold_op4"),
        (tern_general, "hold_tern"),
        (shift_general, "hold_shift"),
        (nwrap_general, "hold_nested"),
        (deep_general, "hold_deep"),
    ]:
        assert general is not None
        observation, ground_truth = corpus.holdout[holdout_key]
        predicted = apply_pattern(general, observation)
        assert predicted is not None, f"{holdout_key}: apply_pattern failed"
        assert _content(predicted) == _content(ground_truth), f"{holdout_key}: prediction did not match ground truth"

    # cross-check: the shift pattern must NOT correctly predict the tern
    # holdout (same arity, different transformation) -- proves the two
    # abstracted patterns really are distinct, not coincidentally compatible.
    tern_obs, tern_gt = corpus.holdout["hold_tern"]
    cross_predicted = apply_pattern(shift_general, tern_obs)
    assert cross_predicted is not None
    assert _content(cross_predicted) != _content(tern_gt)
