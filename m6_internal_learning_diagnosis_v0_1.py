"""MetaHIA M6 -- internal-learning diagnosis v0.1 ("M6-INTERNAL").

Formalizes a distinction the project owner drew explicitly (2026-09-22,
in response to `m6_context_transfer_diagnosis_v0_1.py`'s real result):
M6's holdout evaluation has always asked one specific question --
`split_by_rule()` guarantees every holdout record's rule was NEVER seen
in training, so `StructuralLearningPolicy.predict()` can only ever fall
back to `BASIS_GLOBAL_PRIOR` (Sec. 11,
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md`). That is one
capability -- call it **M6-TRANSFER**: does a genuinely unseen rule
benefit from anything learned on OTHER rules? -- but it is not the only
capability the module's own name promises
(`Rule x Context x Depth x Provenance -> distribution`). The other,
never previously measured because `split_by_rule()` structurally
prevents it, is **M6-INTERNAL**: *when multiple observations of the
SAME rule exist, does `StructuralLearningPolicy` actually exploit
`Rule x Context x Depth x Provenance` on a held-out observation of a
rule it has partially seen?*

These are two different capabilities, not two performance levels of one
test -- M6-TRANSFER's `BASIS_GLOBAL_PRIOR` fallback is a fact about the
evaluation design, not a comment on M6-INTERNAL, which this module
measures for the first time, on real data, without touching
`m6_structural_learning_v0_1.py` at all (same parallel-adapter
discipline as `m6_context_transfer_diagnosis_v0_1.py`,
`p4t_emergent_structure_v0_1.py`, and the P4-T.6 ROI adapter).

`split_within_rule()` is the exact structural INVERSE of
`split_by_rule()`: for any rule with at least `min_records_per_rule`
observations, it holds out a FRACTION of that rule's own records while
guaranteeing at least one record of the same rule remains in train --
so a holdout record's rule signature is now ALWAYS present in
`_rule_counts` (often `_bucket_counts` too), making `BASIS_EXACT_BUCKET`/
`BASIS_RULE_ONLY` reachable by construction, the opposite guarantee
from `split_by_rule()`. Rules with fewer than `min_records_per_rule`
observations cannot test this question at all (holding out their only
record would just reproduce the M6-TRANSFER case) and go entirely to
train, exactly like a rule too small to be usefully held out anywhere.

The comparison this module reports, mirroring
`m6_context_transfer_diagnosis_v0_1.py`'s structure: the REAL, unmodified
`StructuralLearningPolicy` (which should now genuinely reach
EXACT_BUCKET/RULE_ONLY) against `GlobalOnlyPolicy`, a minimal baseline
that always predicts the flat training-class-frequency regardless of
rule/context -- exactly what M6-TRANSFER's holdout has always measured.
If the real policy beats this baseline on M6-INTERNAL's holdout, that is
the first real evidence that `Rule x Context x Depth x Provenance`
carries information the flat prior does not, on a rule the policy has
partially seen -- the capability the module's own design has always
claimed, never previously exercised.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from m6_structural_learning_v0_1 import (
    BASIS_EXACT_BUCKET,
    BASIS_RULE_ONLY,
    OUTCOME_CLASSES,
    StructuralLearningPolicy,
    StructuralOutcomeRecord,
    brier_score_multiclass,
    expected_calibration_error_top_label,
)

BASIS_GLOBAL_ONLY_BASELINE = "GLOBAL_ONLY_BASELINE"


@dataclass(frozen=True)
class GlobalOnlyPrediction:
    distribution: Mapping[str, float]
    basis: str
    support: int


class GlobalOnlyPolicy:
    """Signature-compatible with `StructuralLearningPolicy.predict()`
    (duck-typed for `brier_score_multiclass()`/
    `expected_calibration_error_top_label()`, reused unchanged): always
    returns the flat training-class-frequency, ignoring rule and context
    entirely -- exactly what M6-TRANSFER's holdout has always measured
    via `BASIS_GLOBAL_PRIOR`. The baseline this module's real comparison
    is against, not a competing production mechanism.
    """

    def __init__(self) -> None:
        self._global_counts: Counter = Counter()

    def fit(self, train_records: Sequence[StructuralOutcomeRecord]) -> "GlobalOnlyPolicy":
        new = GlobalOnlyPolicy()
        counts: Counter = Counter()
        for r in train_records:
            counts[r.outcome] += 1
        new._global_counts = counts
        return new

    def predict(self, rule: object, novelty: float, redundancy: float, depth: int, provenance: str) -> GlobalOnlyPrediction:
        total = sum(self._global_counts.values())
        if total == 0:
            uniform = {c: 1.0 / len(OUTCOME_CLASSES) for c in OUTCOME_CLASSES}
            return GlobalOnlyPrediction(distribution=uniform, basis=BASIS_GLOBAL_ONLY_BASELINE, support=0)
        dist = {c: self._global_counts.get(c, 0) / total for c in OUTCOME_CLASSES}
        return GlobalOnlyPrediction(distribution=dist, basis=BASIS_GLOBAL_ONLY_BASELINE, support=total)


def split_within_rule(
    records: Sequence[StructuralOutcomeRecord],
    *,
    val_fraction: float = 0.0,
    holdout_fraction: float = 0.2,
    seed: int = 0,
    min_records_per_rule: int = 2,
) -> Tuple[Tuple[StructuralOutcomeRecord, ...], Tuple[StructuralOutcomeRecord, ...], Tuple[StructuralOutcomeRecord, ...]]:
    """Splits records into (train, validation, holdout) by INDIVIDUAL
    RECORD within each rule -- the structural inverse of
    `split_by_rule()`. A rule with at least `min_records_per_rule`
    observations contributes some of its own records to val/holdout
    while ALWAYS keeping at least one record of that same rule in
    train; a rule with fewer observations goes entirely to train
    (nothing to hold out that would test "already partially seen"
    rather than reproducing `split_by_rule()`'s own unseen-rule case).
    """
    if not (0.0 <= val_fraction and 0.0 <= holdout_fraction and val_fraction + holdout_fraction < 1.0):
        raise ValueError("val_fraction and holdout_fraction must be >= 0 and sum to < 1")
    if min_records_per_rule < 2:
        raise ValueError("min_records_per_rule must be >= 2 -- holding out a rule's only record tests the unseen-rule case, not this one")

    by_rule: Dict[object, list] = defaultdict(list)
    for r in records:
        by_rule[r.rule_signature].append(r)

    rng = random.Random(seed)
    train, val, holdout = [], [], []
    for sig in sorted(by_rule, key=repr):
        group = list(by_rule[sig])
        if len(group) < min_records_per_rule:
            train.extend(group)
            continue
        shuffled = list(group)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_holdout = min(n - 1, int(round(n * holdout_fraction)))
        n_val = min(n - 1 - n_holdout, int(round(n * val_fraction)))
        holdout.extend(shuffled[:n_holdout])
        val.extend(shuffled[n_holdout:n_holdout + n_val])
        train.extend(shuffled[n_holdout + n_val:])
    return tuple(train), tuple(val), tuple(holdout)


@dataclass(frozen=True)
class InternalLearningResult:
    domain: str
    seed: int
    n_train: int
    n_holdout: int
    n_rules_eligible: int
    basis_counts: Mapping[str, int]
    exact_or_rule_only_rate: float
    real_policy_brier: float
    real_policy_ece: float
    global_only_brier: float
    global_only_ece: float

    @property
    def brier_delta(self) -> float:
        """real_policy - global_only: negative means the real policy,
        genuinely exploiting Rule x Context x Depth x Provenance, beats
        the flat baseline; positive means it does worse."""
        return self.real_policy_brier - self.global_only_brier


def run_internal_learning_diagnosis(
    records: Sequence[StructuralOutcomeRecord],
    *,
    domain: str,
    val_fraction: float = 0.0,
    holdout_fraction: float = 0.2,
    seed: int = 0,
    min_records_per_rule: int = 2,
) -> Optional[InternalLearningResult]:
    """Fits the REAL, unmodified `StructuralLearningPolicy` and the
    `GlobalOnlyPolicy` baseline on the identical `split_within_rule()`
    train split, scores both on the identical holdout. Returns `None`
    when no rule has enough observations to produce a non-empty holdout
    (fail-closed, same discipline as
    `run_context_transfer_diagnosis()`/`evaluate_promotion()`)."""
    train, _val, holdout = split_within_rule(
        records, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed, min_records_per_rule=min_records_per_rule
    )
    if not train or not holdout:
        return None

    real_policy = StructuralLearningPolicy().fit(train)
    baseline_policy = GlobalOnlyPolicy().fit(train)

    basis_counts: Counter = Counter()
    for r in holdout:
        pred = real_policy.predict(r.rule, r.novelty, r.redundancy, r.depth, r.provenance)
        basis_counts[pred.basis] += 1
    exact_or_rule = basis_counts.get(BASIS_EXACT_BUCKET, 0) + basis_counts.get(BASIS_RULE_ONLY, 0)

    n_rules_eligible = sum(
        1
        for _sig, group in _group_by_rule(records).items()
        if len(group) >= min_records_per_rule
    )

    return InternalLearningResult(
        domain=domain,
        seed=seed,
        n_train=len(train),
        n_holdout=len(holdout),
        n_rules_eligible=n_rules_eligible,
        basis_counts=dict(basis_counts),
        exact_or_rule_only_rate=exact_or_rule / len(holdout),
        real_policy_brier=brier_score_multiclass(real_policy, holdout),
        real_policy_ece=expected_calibration_error_top_label(real_policy, holdout),
        global_only_brier=brier_score_multiclass(baseline_policy, holdout),
        global_only_ece=expected_calibration_error_top_label(baseline_policy, holdout),
    )


def _group_by_rule(records: Sequence[StructuralOutcomeRecord]) -> Dict[object, list]:
    groups: Dict[object, list] = defaultdict(list)
    for r in records:
        groups[r.rule_signature].append(r)
    return groups


def run_internal_learning_diagnosis_multi_seed(
    records: Sequence[StructuralOutcomeRecord],
    *,
    domain: str,
    seeds: Sequence[int] = tuple(range(10)),
    val_fraction: float = 0.0,
    holdout_fraction: float = 0.2,
    min_records_per_rule: int = 2,
) -> Tuple[InternalLearningResult, ...]:
    results = []
    for seed in seeds:
        result = run_internal_learning_diagnosis(
            records,
            domain=domain,
            val_fraction=val_fraction,
            holdout_fraction=holdout_fraction,
            seed=seed,
            min_records_per_rule=min_records_per_rule,
        )
        if result is not None:
            results.append(result)
    return tuple(results)


def result_to_dict(result: InternalLearningResult) -> dict:
    return {
        "domain": result.domain,
        "seed": result.seed,
        "n_train": result.n_train,
        "n_holdout": result.n_holdout,
        "n_rules_eligible": result.n_rules_eligible,
        "basis_counts": dict(result.basis_counts),
        "exact_or_rule_only_rate": result.exact_or_rule_only_rate,
        "real_policy_brier": result.real_policy_brier,
        "real_policy_ece": result.real_policy_ece,
        "global_only_brier": result.global_only_brier,
        "global_only_ece": result.global_only_ece,
        "brier_delta": result.brier_delta,
    }


__all__ = [
    "BASIS_GLOBAL_ONLY_BASELINE",
    "GlobalOnlyPrediction",
    "GlobalOnlyPolicy",
    "InternalLearningResult",
    "split_within_rule",
    "run_internal_learning_diagnosis",
    "run_internal_learning_diagnosis_multi_seed",
    "result_to_dict",
]
