"""E14 — variable arity (Corpus V2.0 roadmap, documentation/CORPUS_V2_0_ROADMAP_2026-09-16.md).

Dimension tested, alone (per the roadmap's "one dimension at a time" rule):
observations of a given family are not all the same arity, and a genuinely
different-arity family (ternary, not binary) coexists in the same run.

PASS criterion (from the roadmap): compare() generalizes correctly across
differently-shaped observations, with no crash and no false pattern forced
between incompatible shapes.
FAIL criterion: the engine forces an invalid position-by-position alignment
across different arities, or crashes.

Disposable, self-contained fixture data (inline, no new corpus file needed
for a single-dimension probe) -- consistent with how the ambiguity probe
(E13-A.2 follow-up) was done.
"""
from __future__ import annotations

from kernel2 import OBSERVATION, Node, apply_pattern, compare, compare_candidates


def _obs(node_id, *children):
    return Node(node_id=node_id, kind=OBSERVATION, children=tuple(children))


# The already-validated binary (arity-4) O-family pattern, reused as-is from
# E13-A.2 to prove E14 does not disturb it.
def _o_family_pattern():
    return compare(_obs("s1", "O", "A", "B", "C"), _obs("s2", "O", "B", "A", "C"))


def test_compare_finds_a_local_pattern_at_a_different_arity_than_the_existing_corpus():
    """A genuinely new, ternary (arity-5: operator + 3 args + output) family,
    never seen anywhere in the E13-A.2 micro-corpus. The exact same compare()
    that discovered the binary swap pattern must also discover this one, with
    zero code change -- the mechanism must be arity-agnostic, not hardcoded
    to 4-tuples."""
    t1 = _obs("t1", "TERN", "A", "B", "C", "D")
    t2 = _obs("t2", "TERN", "B", "A", "C", "D")  # swap arg1/arg2, arg3 and output fixed
    pattern = compare(t1, t2)
    assert pattern is not None
    assert len(pattern.children) == 5
    assert pattern.children[0].literal_constraint == "TERN"
    assert pattern.children[1].source_position == 2
    assert pattern.children[2].source_position == 1
    assert pattern.children[3].literal_constraint == "C"
    assert pattern.children[4].literal_constraint == "D"

    unseen_ternary = _obs("h", "TERN", "P", "Q", "C", "D")
    predicted = apply_pattern(pattern, unseen_ternary)
    assert predicted is not None
    assert predicted.children == ("TERN", "Q", "P", "C", "D")


def test_compare_refuses_to_abstract_across_incompatible_arities():
    """The binary O-family pattern (arity 4) and the ternary TERN-family
    pattern (arity 5) must NOT merge -- forcing them into one "general"
    pattern would be exactly the invalid position-by-position alignment the
    E14 FAIL criterion warns against. compare() must reject cleanly, not
    truncate/pad one of them to fake a matching shape."""
    o_pattern = _o_family_pattern()
    tern_pattern = compare(_obs("t1", "TERN", "A", "B", "C", "D"), _obs("t2", "TERN", "B", "A", "C", "D"))
    assert o_pattern is not None and tern_pattern is not None
    assert len(o_pattern.children) != len(tern_pattern.children)

    assert compare(o_pattern, tern_pattern) is None
    assert compare_candidates(o_pattern, tern_pattern) == ()


def test_compare_refuses_to_compare_two_raw_observations_of_different_arity():
    """The other direction of the same rule, at the OBSERVATION level: a
    3-argument fact can never be silently compared to a 2-argument one."""
    binary_obs = _obs("s1", "O", "A", "B", "C")
    ternary_obs = _obs("t1", "TERN", "A", "B", "C", "D")
    assert compare(binary_obs, ternary_obs) is None
    assert compare_candidates(binary_obs, ternary_obs) == ()


def test_a_malformed_impostor_observation_inside_a_family_does_not_corrupt_discovery():
    """Literally the roadmap's own wording: 'les observations d'une même
    famille n'ont pas toutes la même arité'. An accidental/malformed
    ternary-shaped record sitting alongside the real binary O-family pair
    must not crash the pairwise comparison, must not be force-matched
    against the binary pair, and must not prevent the correctly-shaped pair
    from still yielding its pattern."""
    s1 = _obs("s1", "O", "A", "B", "C")
    s2 = _obs("s2", "O", "B", "A", "C")
    impostor = _obs("s1_bad", "O", "A", "B", "C", "EXTRA")  # same content, one extra field

    # the real pair is unaffected
    assert compare(s1, s2) is not None

    # the impostor is safely rejected against either sibling, not force-aligned
    assert compare(s1, impostor) is None
    assert compare(s2, impostor) is None
    assert compare_candidates(s1, impostor) == ()


def test_existing_e13a2_binary_families_are_unaffected_by_e14():
    """Regression guard: introducing a different-arity family anywhere in the
    module/tests must not change compare()'s behavior on the arity-4 corpus
    that E13-A.2's result depends on."""
    from loader import load_micro_corpus

    corpus = load_micro_corpus()
    for family, (a, b) in corpus.families.items():
        assert compare(a, b) is not None, f"E14 regressed family {family!r}"
