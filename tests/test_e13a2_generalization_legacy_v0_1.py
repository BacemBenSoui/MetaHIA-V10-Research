"""E13-A.2 as an actual, falsifiable software experiment.

Each test below corresponds to one criterion the source discussion's E13-A.2
step was defined against, but never executed in code (every result in the
discussion export was labeled "PASS CONCEPTUAL"). These assertions are the
first real execution: they pass or fail against actual output, not narrative.
"""
from __future__ import annotations

from kernel2 import apply_pattern, compare, pattern_is_applicable
from loader import load_micro_corpus


def test_local_pattern_discovered_independently_per_operator_family():
    """Reproduces the discussion's own K3-02 worked example (O-family) and
    shows the same mechanism, with zero code change, also fires for AND and
    NOR -- i.e. it is genuinely operator-agnostic, not special-cased to 'O'."""
    corpus = load_micro_corpus()
    for family, (a, b) in corpus.families.items():
        pattern = compare(a, b)
        assert pattern is not None, f"expected a local pattern for family {family!r}"
        # every family here is a swap of the two argument positions (1,2),
        # with the operator (0) and output (3) frozen to that family's own values.
        assert pattern.children[0].literal_constraint == a.children[0]
        assert pattern.children[1].source_position == 2
        assert pattern.children[2].source_position == 1
        assert pattern.children[3].literal_constraint == a.children[3]


def test_non_commutative_operator_does_not_yield_a_false_pattern():
    """Negative control: SUB(M,N)=D1, SUB(N,M)=D2 with D1 != D2. The engine
    must NOT force-fit a swap pattern just because the shape matches."""
    corpus = load_micro_corpus()
    a, b = corpus.non_commutative_pair
    assert compare(a, b) is None


def test_single_local_pattern_is_not_sufficient_evidence_for_generalization():
    """Anti-overfit guard: a pattern discovered from exactly one operator
    family must not, by itself, be treated as a cross-operator regularity.
    Abstraction requires comparing at least two independent local patterns —
    this pins down why: a lone pattern still carries the concrete "O"/"C"
    literals, so it is not even applicable to a different operator's data
    (run_spike.py enforces the >=2-independent-families rule explicitly)."""
    corpus = load_micro_corpus()
    a, b = corpus.families["O"]
    single_pattern = compare(a, b)
    unseen_from_other_operator = corpus.holdout_observation  # operator "ADD3", not "O"
    assert pattern_is_applicable(single_pattern, unseen_from_other_operator) is False


def test_pattern_abstracted_from_two_families_generalizes_to_a_third():
    """The actual generalization claim: abstract across O and AND (two
    independent local patterns), then apply the result to NOR's raw
    observation without ever having compared NOR during discovery."""
    corpus = load_micro_corpus()
    o_pattern = compare(*corpus.families["O"])
    and_pattern = compare(*corpus.families["AND"])
    general_pattern = compare(o_pattern, and_pattern)
    assert general_pattern is not None

    nor_a, _nor_b = corpus.families["NOR"]
    predicted = apply_pattern(general_pattern, nor_a)
    assert predicted is not None
    assert predicted.children == corpus.families["NOR"][1].children


def test_generalization_confirmed_on_genuinely_unseen_holdout_operator():
    """The real E13-A.2 claim, on data reserved specifically for this: a
    pattern abstracted from O/AND/NOR is applied to a fourth operator (ADD3)
    that was never part of pattern discovery at all, and the prediction is
    checked against a ground truth the corpus never let the engine see."""
    corpus = load_micro_corpus()
    o_pattern = compare(*corpus.families["O"])
    and_pattern = compare(*corpus.families["AND"])
    nor_pattern = compare(*corpus.families["NOR"])
    general_pattern = compare(compare(o_pattern, and_pattern), nor_pattern)
    assert general_pattern is not None
    # fully generalized: no literal constraints should remain anywhere.
    assert all(slot.literal_constraint is None for slot in general_pattern.children)

    predicted = apply_pattern(general_pattern, corpus.holdout_observation)
    assert predicted is not None
    assert predicted.children == corpus.holdout_ground_truth.children


def test_contradiction_is_recorded_without_erasing_prior_support():
    """E4 (contradictory emergence): a third O-family observation that
    contradicts the S1/S2 pattern must flip the hypothesis to CONTRADICTED
    while the original supporting observations remain on record."""
    from kernel2 import Hypothesis

    corpus = load_micro_corpus()
    s1, s2 = corpus.families["O"]
    pattern = compare(s1, s2)
    hyp = Hypothesis(hypothesis_id="H_O_swap", pattern=pattern).with_support(s1.node_id).with_support(s2.node_id)
    assert hyp.status == "SUPPORTED"

    # What the pattern predicts from S1 alone (same mechanism that discovered
    # S2 in the first place -- applying it to S1 must reproduce S2 exactly).
    predicted_from_s1 = apply_pattern(pattern, s1)
    assert predicted_from_s1.children == s2.children

    # The probe reports the SAME (operator, swapped-args) shape as that
    # prediction, but a genuinely different, independently observed output --
    # this is the contradiction, not a mere replay of S2.
    assert predicted_from_s1.children[:3] == tuple(corpus.contradiction_probe.children[:3])
    assert predicted_from_s1.children[3] != corpus.contradiction_probe.children[3]

    hyp = hyp.with_contradiction(corpus.contradiction_probe.node_id)
    assert hyp.status == "CONTRADICTED"
    assert hyp.supporting_ids == (s1.node_id, s2.node_id)  # conserved, not deleted
