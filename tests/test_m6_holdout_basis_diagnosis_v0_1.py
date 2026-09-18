"""M6 -- holdout prediction basis diagnosis v0.1.

Documents a structural finding made 2026-09-18 while investigating WHY
adding the M7 multi-hop witness's evidence improved holdout Brier
(MetaHIA_M7_TextClaimParser_V0_1.md Sec.14): every holdout prediction ever
computed in this project's history, including the original already-VALIDATED
M6 v0.2 baseline (holdout Brier=0.48125), uses `BASIS_GLOBAL_PRIOR` --
`BASIS_EXACT_BUCKET`/`BASIS_RULE_ONLY` have never fired on any holdout
evaluation.

This is a structural consequence of `split_by_rule()`'s own design (by
design, per its docstring: "Every record of a given rule lands in exactly
one split... holdout measures generalization to an unseen rule, not
memorization of a rule already partially seen in training"), not a bug: a
rule can never appear in both train and holdout, so a holdout record's rule
signature is NEVER present in `StructuralLearningPolicy`'s trained
`_bucket_counts`/`_rule_counts` -- `predict()` can only ever fall back to
`BASIS_GLOBAL_PRIOR` (or `BASIS_UNIFORM_NO_DATA`) for it.

Practical consequence, disclosed here and in MetaHIA_M6_Structural_Learning_V0_1.md
Sec.9 and MetaHIA_M7_TextClaimParser_V0_1.md Sec.14: every Brier/ECE number
this project has reported measures whether the GLOBAL training class-
frequency prior generalizes to a genuinely new rule -- never whether the
policy learned anything RULE-SPECIFIC (the literal Rule x Context x Depth x
Provenance mapping the module is named for). Adding more training records
of any kind can only move that number by shifting the global prior, not by
teaching the policy anything about a specific rule it will be asked to
predict on holdout.

This is NOT enforced as a permanent invariant (a larger/richer corpus
SHOULD eventually make EXACT_BUCKET/RULE_ONLY reachable in a holdout
evaluation, which would be a genuine improvement, not a regression) -- these
tests document the CURRENT state on the CURRENT corpus, so a future change
that finally exercises rule-specific holdout prediction is expected to
require updating this file, not treated as breaking it silently.
"""
from __future__ import annotations

from collections import Counter

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_structural_learning_v0_1 import (
    BASIS_GLOBAL_PRIOR,
    StructuralLearningPolicy,
    brier_score_multiclass,
    split_by_rule,
)


def _holdout_basis_counts(records, *, seed=0):
    train, _val, holdout = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=seed)
    train_rules = {r.rule_signature for r in train}
    policy = StructuralLearningPolicy().fit(train)
    counts = Counter()
    for r in holdout:
        assert r.rule_signature not in train_rules  # split_by_rule's own guarantee, verified directly
        pred = policy.predict(r.rule, r.novelty, r.redundancy, r.depth, r.provenance)
        counts[pred.basis] += 1
    return counts, len(holdout)


def test_split_by_rule_never_lets_a_holdout_rule_also_appear_in_training():
    """The structural guarantee this whole finding rests on, checked
    directly rather than assumed."""
    report = build_real_corpus_v2()
    train, _val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    train_rules = {r.rule_signature for r in train}
    holdout_rules = {r.rule_signature for r in holdout}
    assert train_rules.isdisjoint(holdout_rules)


def test_m6_v0_2_already_validated_baseline_holdout_uses_only_global_prior():
    """The very first non-degenerate M6 calibration result (holdout
    Brier=0.48125, already VALIDATED and closed by the project owner
    2026-09-17) never exercised EXACT_BUCKET/RULE_ONLY -- its holdout
    evaluation is, and always was, a pure global-class-frequency
    generalization test, not a demonstration of rule-specific learning.
    Documented here explicitly so this is never mistaken for something it
    is not."""
    report = build_real_corpus_v2()
    counts, holdout_size = _holdout_basis_counts(report.records)
    assert holdout_size > 0
    assert counts[BASIS_GLOBAL_PRIOR] == holdout_size
    assert sum(counts.values()) == holdout_size  # no other basis appears at all


def test_adding_global_prior_biased_evidence_is_not_a_causally_robust_improvement():
    """Regression/honesty guard for the M7 multi-hop witness finding
    (MetaHIA_M7_TextClaimParser_V0_1.md Sec.14): since any added evidence
    can only shift the GLOBAL prior (never teach anything rule-specific,
    per the two tests above), whether it helps or hurts a given holdout
    split depends entirely on how well that shift happens to match THAT
    split's composition -- it is not a guaranteed improvement. Checked
    directly across 10 seeds on a synthetic-but-representative corpus
    (adversarial + an all-CONTRADICTED evidence batch standing in for the
    multi-hop witness): both directions must be observed, proving this is a
    statistical tendency, not a causal guarantee."""
    from m4_cold_start_evidence_v0_1 import CONTRADICTED
    from m6_structural_learning_v0_1 import StructuralOutcomeRecord

    report = build_real_corpus_v2()
    # Stand-in for a batch of new-rule, all-CONTRADICTED evidence (like the
    # real multi-hop witness) using the SAME rules already in the corpus,
    # relabeled CONTRADICTED, purely to test the global-prior-shift dynamic
    # in isolation without a live LLM call.
    biased_batch = tuple(
        StructuralOutcomeRecord(
            record_id=f"synthetic-bias::{i}", rule=r.rule, novelty=r.novelty, redundancy=r.redundancy,
            depth=r.depth, provenance=r.provenance, outcome=CONTRADICTED,
        )
        for i, r in enumerate(report.records[:10])
    )
    combined = report.records + biased_batch

    deltas = []
    for seed in range(10):
        train_a, _va, holdout_a = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=seed)
        train_b, _vb, holdout_b = split_by_rule(combined, val_fraction=0.2, holdout_fraction=0.2, seed=seed)
        if not holdout_a or not holdout_b:
            continue
        brier_a = brier_score_multiclass(StructuralLearningPolicy().fit(train_a), holdout_a)
        brier_b = brier_score_multiclass(StructuralLearningPolicy().fit(train_b), holdout_b)
        deltas.append(brier_b - brier_a)

    assert any(d < 0 for d in deltas), "expected at least one seed where the biased batch helps"
    assert any(d > 0 for d in deltas), "expected at least one seed where the biased batch hurts -- proves it is not a robust, causal improvement"
