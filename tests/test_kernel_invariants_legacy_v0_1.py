"""Permanent invariant tests for the K3 kernel (requested 2026-09-16, following
the detailed test/correction audit -- documentation/CORPUS_V2_0_RAPPORT_TESTS_ET_CORRECTIONS_2026-09-16.md).

The audit's four corrections map onto three stability properties that had,
until now, only ever been checked by specific, one-off examples embedded in
feature tests (E13-A.2 through E17). This module turns each into a
systematic, permanent regression guard, swept over many constructed cases
rather than the single example that originally surfaced each issue:

  1. CLOSURE       -- compare() and apply_pattern() always produce either
                       None or a well-formed Node of the expected kind/arity,
                       recursively (through nested and operator-level slots).
                       (Discussion source, E10: "Apply(Node,...) -> Node",
                       "Compare(...) -> Node".)
  2. MONOTONICITY   -- generalization only ever removes information (a
                       literal_constraint becoming free), never reintroduces
                       it; supporting/contradicting evidence only accumulates,
                       never shrinks; a contradicted Hypothesis never reverts
                       to SUPPORTED. (_compare_patterns' own stated invariant,
                       Correction 1's root cause.)
  3. ACTIVE AMBIGUITY REFUSAL -- compare() returns None whenever more than
                       one permutation reconciles a pair, across many
                       differently-shaped ambiguous cases, not just the one
                       that originally surfaced the bug (Correction 3) --
                       plus the cross-consistency invariant tying compare()
                       to compare_candidates() that makes silent regressions
                       to "pick one arbitrarily" detectable automatically.

If a future change to kernel.py breaks any of these, it should fail here
first, independently of whatever feature test happens to exercise that code
path.
"""
from __future__ import annotations

from itertools import combinations

from kernel2 import (
    OBSERVATION,
    PATTERN,
    SHAPE_PATTERN,
    Hypothesis,
    Node,
    PatternSlot,
    ShapeRewrite,
    ShapeTerm,
    apply,
    apply_pattern,
    compare,
    compare_candidates,
    group_into_hypotheses,
)


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


def _swap12(node_id_a, node_id_b, op, a1, a2, out, *extra_frozen):
    """A same-shape pair whose only regularity is swapping positions 1,2."""
    a = _obs(node_id_a, op, a1, a2, *extra_frozen, out)
    b = _obs(node_id_b, op, a2, a1, *extra_frozen, out)
    return a, b


def _is_well_formed_pattern(node) -> bool:
    """Recursively validates closure across BOTH pattern kinds: for PATTERN,
    a Node whose children are all PatternSlot with an in-range
    source_position and any nested_pattern itself well-formed (recursively);
    for SHAPE_PATTERN (E18), a Node with exactly one well-formed
    ShapeRewrite child."""
    if not isinstance(node, Node):
        return False
    if node.kind == PATTERN:
        n = len(node.children)
        for slot in node.children:
            if not isinstance(slot, PatternSlot):
                return False
            if not (0 <= slot.source_position < n):
                return False
            if slot.nested_pattern is not None and not _is_well_formed_pattern(slot.nested_pattern):
                return False
        return True
    if node.kind == SHAPE_PATTERN:
        if len(node.children) != 1 or not isinstance(node.children[0], ShapeRewrite):
            return False
        rw = node.children[0]
        return isinstance(rw.source, ShapeTerm) and isinstance(rw.target, ShapeTerm) and isinstance(rw.arity, int) and rw.arity > 0
    return False


def _is_well_formed_observation(node) -> bool:
    if not isinstance(node, Node) or node.kind != OBSERVATION:
        return False
    return all(
        (not isinstance(child, Node)) or child.kind in (OBSERVATION, PATTERN)
        for child in node.children
    )


def _ambiguous_pair(block_sizes, node_id_a="amb_a", node_id_b="amb_b"):
    """Generalizes the audit's X,X,Y,Y example to arbitrary block sizes: N
    blocks of values V0..V(N-1), each repeated block_sizes[i] times, laid out
    in `a` in order and reversed-block-order in `b`. Every block of size
    m>=2 contributes m! internally-free permutations on each side it maps
    to/from, guaranteeing genuine, non-trivial ambiguity (verified by the
    assertions in the tests below, not just assumed)."""
    values = [f"V{i}" for i in range(len(block_sizes))]
    a_children = [v for v, size in zip(values, block_sizes) for _ in range(size)]
    b_children = [v for v, size in zip(reversed(values), reversed(block_sizes)) for _ in range(size)]
    return _obs(node_id_a, *a_children), _obs(node_id_b, *b_children)


# ---------------------------------------------------------------------------
# 1. CLOSURE -- compare()/apply_pattern() always yield None or a well-formed
#    Node of the right kind/arity, however the inputs are shaped.
# ---------------------------------------------------------------------------

def _closure_observation_battery():
    """A deliberately varied sweep: several arities, a non-commutative
    counter-example, an ambiguous pair, and depth-2/depth-3 nested pairs --
    every case compare() is meant to handle, comparable or not."""
    cases = [
        _swap12("a1", "b1", "O", "A", "B", "C"),
        _swap12("a2", "b2", "TERN", "A", "B", "C", "K"),
        _swap12("a3", "b3", "HEX", "A", "B", "C", "K1", "K2"),
        (_obs("nc_a", "SUB", "M", "N", "D1"), _obs("nc_b", "SUB", "N", "M", "D2")),  # no pattern
        _ambiguous_pair([2, 2]),   # ambiguous, arity 4
        _ambiguous_pair([3, 3]),   # ambiguous, arity 6
        _ambiguous_pair([2, 3]),   # ambiguous, arity 5, uneven blocks
        (_obs("id_a", "O", "A", "B", "C"), _obs("id_b", "O", "A", "B", "C")),  # identical: no difference
        (_obs("shape_a", "O", "A", "B", "C"), _obs("shape_b", "O", "A", "B")),  # different arity
    ]
    # depth-2 and depth-3 nested pairs
    inner_a, inner_b = _swap12("in_a", "in_b", "IN", "A", "B", "C")
    cases.append((_obs("nest2_a", "WRAP", inner_a), _obs("nest2_b", "WRAP", inner_b)))
    mid_a = _obs("mid_a", "MID", inner_a)
    mid_b = _obs("mid_b", "MID", inner_b)
    cases.append((_obs("nest3_a", "OUTER", mid_a), _obs("nest3_b", "OUTER", mid_b)))
    # E18: a genuine recurrent-shape pair -- the flat search finds nothing at
    # all here (different top-level arity as flat tuples), so compare() can
    # only produce a result via the compare_tree_shapes() fallback. Included
    # so the closure tests actually exercise a SHAPE_PATTERN result, not just
    # avoid crashing on ones that never occur.
    shape_inner_a = _obs("shape_inner_a", "OP", "X", "Q", "_ia")
    shape_a = _obs("shape_disc_a", "OP", shape_inner_a, "Y", "OUT")
    shape_inner_b = _obs("shape_inner_b", "OP", "Q", "Y", "_ib")
    shape_b = _obs("shape_disc_b", "OP", "X", shape_inner_b, "OUT")
    cases.append((shape_a, shape_b))
    return cases


def test_closure_compare_on_observations_is_none_or_a_well_formed_pattern_of_matching_arity():
    for a, b in _closure_observation_battery():
        result = compare(a, b)
        if result is None:
            continue
        assert _is_well_formed_pattern(result)
        if result.kind == PATTERN:  # arity parity only applies to fixed-arity PATTERN results
            assert len(result.children) == len(a.children)


def test_closure_compare_candidates_on_observations_is_always_a_tuple_of_well_formed_patterns():
    for a, b in _closure_observation_battery():
        results = compare_candidates(a, b)
        assert isinstance(results, tuple)
        for r in results:
            assert _is_well_formed_pattern(r)
            if r.kind == PATTERN:
                assert len(r.children) == len(a.children)


def test_closure_compare_on_patterns_abstraction_is_none_or_a_well_formed_pattern():
    patterns = [compare(a, b) for a, b in _closure_observation_battery()]
    patterns = [p for p in patterns if p is not None]
    for p1, p2 in combinations(patterns, 2):
        if p1.kind != p2.kind:
            continue  # compare() raises for mismatched kinds -- not a "None or well-formed" case, a fail-loud one
        if len(p1.children) != len(p2.children):
            continue
        result = compare(p1, p2)
        assert result is None or _is_well_formed_pattern(result)


def test_closure_apply_pattern_is_none_or_a_node_of_the_operand_kind_and_arity():
    """apply_pattern()'s own contract is PATTERN-only (SHAPE_PATTERN goes
    through apply_tree_shape()/apply() instead -- see the next test)."""
    battery = _closure_observation_battery()
    patterns = [compare(a, b) for a, b in battery]
    operands = [a for a, _ in battery] + [b for _, b in battery] + [p for p in patterns if p is not None and p.kind == PATTERN]
    for pattern in patterns:
        if pattern is None or pattern.kind != PATTERN:
            continue
        for operand in operands:
            if len(pattern.children) != len(operand.children):
                continue
            result = apply_pattern(pattern, operand)
            if result is None:
                continue
            assert isinstance(result, Node)
            assert result.kind == operand.kind
            assert len(result.children) == len(operand.children)
            if result.kind == OBSERVATION:
                assert _is_well_formed_observation(result)
            else:
                assert _is_well_formed_pattern(result)


def test_closure_apply_unified_entry_point_is_none_or_a_well_formed_node_for_either_pattern_kind():
    """apply() (E18/E19 unification) must preserve closure across BOTH
    pattern kinds, not just PATTERN -- exercised here specifically against a
    SHAPE_PATTERN result, which apply_pattern() itself would reject outright."""
    battery = _closure_observation_battery()
    patterns = [compare(a, b) for a, b in battery if compare(a, b) is not None]
    observations = [a for a, _ in battery] + [b for _, b in battery]
    for pattern in patterns:
        for operand in observations:
            if pattern.kind == PATTERN and len(pattern.children) != len(operand.children):
                continue
            if pattern.kind == SHAPE_PATTERN and operand.kind != OBSERVATION:
                continue
            result = apply(pattern, operand)
            if result is None:
                continue
            assert isinstance(result, Node)
            assert result.kind == operand.kind
            if result.kind == OBSERVATION:
                assert _is_well_formed_observation(result)
            else:
                assert _is_well_formed_pattern(result)


# ---------------------------------------------------------------------------
# 2. MONOTONICITY -- generalization only removes constraints, evidence only
#    accumulates, a contradiction never reverts to SUPPORTED.
# ---------------------------------------------------------------------------

def test_monotonicity_generalized_slots_never_regain_a_literal_across_a_longer_chain():
    """Six independent families (more than any single prior experiment used),
    folded one at a time. At every step, any slot already free (None) in the
    accumulated pattern must still be free after merging in the next family
    -- generalization must never run backwards."""
    families = [
        _swap12(f"s{i}a", f"s{i}b", f"OP{i}", "A", "B", f"C{i}")
        for i in range(6)
    ]
    local_patterns = [compare(a, b) for a, b in families]
    assert all(p is not None for p in local_patterns)

    accumulated = local_patterns[0]
    previously_free = {i for i, slot in enumerate(accumulated.children) if slot.literal_constraint is None}
    for next_pattern in local_patterns[1:]:
        merged = compare(accumulated, next_pattern)
        assert merged is not None
        now_free = {i for i, slot in enumerate(merged.children) if slot.literal_constraint is None}
        assert previously_free <= now_free, "a slot regained a literal constraint after being generalized"
        accumulated = merged
        previously_free = now_free

    # since every family only shares the swap(1,2) shape with different
    # literals for operator/output, both those positions must end up free.
    assert accumulated.children[0].literal_constraint is None
    assert accumulated.children[3].literal_constraint is None


def test_monotonicity_hypothesis_evidence_only_accumulates_never_shrinks():
    pattern = compare(*_swap12("m1", "m2", "O", "A", "B", "C"))
    hyp = Hypothesis(hypothesis_id="H", pattern=pattern)
    seen_support: set = set()
    seen_contradiction: set = set()
    for i in range(5):
        hyp = hyp.with_support(f"support_{i}")
        seen_support.add(f"support_{i}")
        assert set(hyp.supporting_ids) == seen_support
    for i in range(3):
        hyp = hyp.with_contradiction(f"contradiction_{i}")
        seen_contradiction.add(f"contradiction_{i}")
        assert set(hyp.contradicting_ids) == seen_contradiction
        # support already recorded must still be there -- contradiction never erases it
        assert set(hyp.supporting_ids) == seen_support


def test_monotonicity_a_contradicted_hypothesis_never_reverts_to_supported():
    pattern = compare(*_swap12("m1", "m2", "O", "A", "B", "C"))
    hyp = Hypothesis(hypothesis_id="H", pattern=pattern).with_support("s1").with_contradiction("bad1")
    assert hyp.status == "CONTRADICTED"
    # further support arriving later must not un-contradict it
    hyp = hyp.with_support("s2").with_support("s3")
    assert hyp.status == "CONTRADICTED"
    assert set(hyp.supporting_ids) == {"s1", "s2", "s3"}
    assert set(hyp.contradicting_ids) == {"bad1"}


def test_monotonicity_group_into_hypotheses_supporting_ids_only_grow_with_more_reinforcing_pairs():
    """Five independent, mutually-compatible families fed one at a time: the
    reinforced hypothesis's supporting_ids must be exactly the union of every
    pair processed so far, at every prefix of the sequence -- never fewer."""
    pairs = [_swap12(f"g{i}a", f"g{i}b", f"OP{i}", "A", "B", f"C{i}") for i in range(5)]
    expected: set = set()
    for i in range(1, len(pairs) + 1):
        hyps = group_into_hypotheses(pairs[:i])
        assert len(hyps) == 1
        expected = {oid for pair in pairs[:i] for oid in (pair[0].node_id, pair[1].node_id)}
        assert set(hyps[0].supporting_ids) == expected


# ---------------------------------------------------------------------------
# 3. ACTIVE AMBIGUITY REFUSAL -- compare() never guesses among competing
#    permutations, swept across many shapes, plus the cross-consistency
#    invariant with compare_candidates().
# ---------------------------------------------------------------------------

def test_active_refusal_across_a_systematic_sweep_of_block_shapes():
    """Not just the one X,X,Y,Y example that originally surfaced the bug --
    several different block-size combinations, arities, and symmetric/
    uneven shapes, each independently verified to be genuinely ambiguous
    (>1 valid permutation) before checking compare() refuses it."""
    for block_sizes in ([2, 2], [3, 3], [2, 3], [2, 2, 2]):
        a, b = _ambiguous_pair(block_sizes)
        candidates = compare_candidates(a, b)
        assert len(candidates) > 1, f"{block_sizes} was not actually ambiguous -- test construction is wrong"
        assert compare(a, b) is None, f"compare() guessed on a genuinely ambiguous case (blocks={block_sizes})"


def test_active_refusal_does_not_reject_genuinely_unambiguous_cases():
    """The other side of the same invariant: refusal must be triggered by
    genuine ambiguity, not by pattern-matching "looks like it might be
    ambiguous" -- every unambiguous shape in the closure battery must still
    produce exactly one candidate and a matching compare() result."""
    for a, b in _closure_observation_battery():
        candidates = compare_candidates(a, b)
        if len(candidates) == 1:
            assert compare(a, b) == candidates[0]


def test_active_refusal_compare_and_compare_candidates_are_always_consistent():
    """The permanent regression guard for Correction 3: compare(a, b) is not
    None if and only if compare_candidates(a, b) has exactly one element, and
    when both exist they are identical. If a future edit ever reintroduces
    "pick the first candidate silently" behavior, this fails immediately,
    independently of any specific example."""
    battery = _closure_observation_battery()
    battery += [_ambiguous_pair(bs) for bs in ([2, 2], [3, 3], [2, 3], [2, 2, 2])]
    for a, b in battery:
        single = compare(a, b)
        candidates = compare_candidates(a, b)
        if single is None:
            assert len(candidates) != 1, "compare() refused but exactly one unambiguous candidate existed"
        else:
            assert len(candidates) == 1
            assert single == candidates[0]


def test_active_refusal_propagates_through_nested_nesting_recursion():
    """The ambiguity-refusal invariant must also hold one level deeper (E15's
    recursion), not just at the top level: an ambiguous OBSERVATION pair
    embedded as a nested child must make the recursive compare() call inside
    _resolve_nested_positions refuse too, rather than silently accepting one
    arbitrary resolution for the nested slot. (Note: _compare_patterns itself
    has no permutation search -- it is purely positional -- so genuine
    ambiguity can only arise from an OBSERVATION-vs-OBSERVATION comparison,
    reached here through nesting rather than directly at the top level.)"""
    amb_a, amb_b = _ambiguous_pair([2, 2], "nest_amb_a", "nest_amb_b")
    meta_a = _obs("meta_amb_a", "USES", amb_a)
    meta_b = _obs("meta_amb_b", "USES", amb_b)
    assert compare(meta_a, meta_b) is None
