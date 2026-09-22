"""MetaHIA M6 -- context-transfer diagnosis v0.1.

Follow-up to the already-documented finding (2026-09-18,
`tests/test_m6_holdout_basis_diagnosis_v0_1.py`,
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 9-11):
`StructuralLearningPolicy.predict()` has NEVER used `BASIS_EXACT_BUCKET`
or `BASIS_RULE_ONLY` on any holdout evaluation, on any of this project's
real corpora. The cause is structural, not a data-volume problem:
`split_by_rule()` guarantees a rule's records land entirely in ONE
split, so a holdout record's `rule_signature` can never be present in
the trained policy's `_bucket_counts`/`_rule_counts` -- `predict()` can
only ever fall through to `BASIS_GLOBAL_PRIOR`. No amount of additional
data under the SAME split policy changes this; it is a logical
consequence of the split, not an emergent property of corpus size (see
`documentation/M6_CONTEXT_TRANSFER_DIAGNOSIS_V0_1.md` for the full
argument).

This module asks the one question that finding leaves open, without
touching `m6_structural_learning_v0_1.py` at all (same "parallel
adapter, never modify the validated mechanism" discipline already used
by `p4t_emergent_structure_v0_1.py` and the P4-T.6 ROI adapter): **does
CONTEXT alone (novelty band, redundancy band, depth, provenance --
deliberately dropping `rule_signature`, the one dimension guaranteed
never to match between train and holdout) carry any predictive signal
that transfers to an unseen rule, or does removing that always-
unreachable dimension leave nothing beyond the flat global prior
either?**

`ContextOnlyPolicy` is deliberately signature-compatible with
`StructuralLearningPolicy` (`predict(rule, novelty, redundancy, depth,
provenance) -> object with .distribution`) so the EXISTING, already-
validated `brier_score_multiclass()`/`expected_calibration_error_top_label()`
functions can score it completely unchanged -- no parallel
reimplementation of Brier/ECE, unlike some of this project's other
standalone-metric cases (e.g. the P8 benchmark modules), because here
there is no data-model incompatibility to work around, only a
different (simpler) key.

If context-bucket Brier/ECE genuinely beats global-prior Brier/ECE on
real holdout data, that is evidence of a form of structural transfer
this project has never previously measured. If it does not, that
confirms -- on real data, not by construction alone -- that this
project's current corpora carry no exploitable structure beyond raw
class frequency once rule identity is removed, a stronger and more
informative negative result than "the split makes EXACT_BUCKET/RULE_ONLY
unreachable" by itself.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from m6_structural_learning_v0_1 import (
    OUTCOME_CLASSES,
    StructuralLearningPolicy,
    StructuralOutcomeRecord,
    _band,
    brier_score_multiclass,
    expected_calibration_error_top_label,
    split_by_rule,
)

BASIS_CONTEXT_BUCKET = "CONTEXT_BUCKET"
BASIS_CONTEXT_GLOBAL_FALLBACK = "CONTEXT_GLOBAL_FALLBACK"


@dataclass(frozen=True)
class ContextOnlyPrediction:
    distribution: Mapping[str, float]
    basis: str
    support: int


def context_key(record: StructuralOutcomeRecord) -> Tuple[str, str, int, str]:
    """(novelty_band, redundancy_band, depth, provenance) -- exactly
    `record.bucket_key()[1:]`, i.e. the SAME public bucket key with
    `rule_signature` (element 0) dropped. Exposed as its own function,
    not inlined, so a test can assert this equivalence directly rather
    than trusting the two independently-written key constructions to
    stay in sync by coincidence."""
    return record.bucket_key()[1:]


class ContextOnlyPolicy:
    """Predicts SUPPORTED/CONTRADICTED/UNKNOWN from context ALONE,
    ignoring `rule_signature` entirely -- a diagnostic twin of
    `StructuralLearningPolicy`, never a replacement for it.
    `StructuralLearningPolicy` itself is not imported or modified beyond
    reusing its module-level `_band` helper directly (the identical
    LOW/MED/HIGH banding, not a re-derived one, to remove any risk of a
    subtly different banding producing a spurious result).
    """

    def __init__(self) -> None:
        self._context_counts: Dict[tuple, Counter] = {}
        self._global_counts: Counter = Counter()

    def fit(self, train_records: Sequence[StructuralOutcomeRecord]) -> "ContextOnlyPolicy":
        new = ContextOnlyPolicy()
        context_counts: Dict[tuple, Counter] = defaultdict(Counter)
        global_counts: Counter = Counter()
        for r in train_records:
            context_counts[context_key(r)][r.outcome] += 1
            global_counts[r.outcome] += 1
        new._context_counts = dict(context_counts)
        new._global_counts = global_counts
        return new

    def predict(self, rule: object, novelty: float, redundancy: float, depth: int, provenance: str) -> ContextOnlyPrediction:
        # `rule` is accepted only for signature compatibility with
        # StructuralLearningPolicy.predict() (so brier_score_multiclass/
        # expected_calibration_error_top_label can call this unchanged)
        # -- deliberately never read, since ignoring rule identity is
        # the entire point of this diagnostic.
        key = (_band(novelty), _band(redundancy), int(depth), provenance)
        bucket = self._context_counts.get(key)
        if bucket:
            return self._to_prediction(bucket, BASIS_CONTEXT_BUCKET)
        return self._to_prediction(self._global_counts, BASIS_CONTEXT_GLOBAL_FALLBACK)

    @staticmethod
    def _to_prediction(counter: Counter, basis: str) -> ContextOnlyPrediction:
        total = sum(counter.values())
        dist = {c: counter.get(c, 0) / total for c in OUTCOME_CLASSES}
        return ContextOnlyPrediction(distribution=dist, basis=basis, support=total)


@dataclass(frozen=True)
class ContextTransferResult:
    domain: str
    seed: int
    n_train: int
    n_holdout: int
    global_prior_brier: float
    global_prior_ece: float
    context_bucket_brier: float
    context_bucket_ece: float
    n_holdout_hitting_context_bucket: int
    n_distinct_context_keys_shared: int

    @property
    def brier_delta(self) -> float:
        """context_bucket - global_prior: negative means context genuinely
        helps (lower Brier is better); positive means it hurts; never
        rounded or clamped."""
        return self.context_bucket_brier - self.global_prior_brier


def run_context_transfer_diagnosis(
    records: Sequence[StructuralOutcomeRecord],
    *,
    domain: str,
    val_fraction: float = 0.2,
    holdout_fraction: float = 0.2,
    seed: int = 0,
) -> Optional[ContextTransferResult]:
    """Fits BOTH policies on the identical `split_by_rule()` train split
    and scores both on the identical holdout split -- the only thing
    that differs between the two Brier/ECE numbers is whether
    `rule_signature` was part of the key. Returns `None` when the split
    yields an empty train or holdout (same fail-closed discipline as
    `evaluate_promotion`'s own `EMPTY_HOLDOUT` case) rather than
    fabricating a comparison from no data."""
    train, _val, holdout = split_by_rule(records, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed)
    if not train or not holdout:
        return None

    global_policy = StructuralLearningPolicy().fit(train)
    context_policy = ContextOnlyPolicy().fit(train)

    train_context_keys = {context_key(r) for r in train}
    holdout_context_keys = {context_key(r) for r in holdout}
    hitting = sum(1 for r in holdout if context_key(r) in train_context_keys)

    return ContextTransferResult(
        domain=domain,
        seed=seed,
        n_train=len(train),
        n_holdout=len(holdout),
        global_prior_brier=brier_score_multiclass(global_policy, holdout),
        global_prior_ece=expected_calibration_error_top_label(global_policy, holdout),
        context_bucket_brier=brier_score_multiclass(context_policy, holdout),
        context_bucket_ece=expected_calibration_error_top_label(context_policy, holdout),
        n_holdout_hitting_context_bucket=hitting,
        n_distinct_context_keys_shared=len(train_context_keys & holdout_context_keys),
    )


def run_context_transfer_diagnosis_multi_seed(
    records: Sequence[StructuralOutcomeRecord],
    *,
    domain: str,
    seeds: Sequence[int] = tuple(range(10)),
    val_fraction: float = 0.2,
    holdout_fraction: float = 0.2,
) -> Tuple[ContextTransferResult, ...]:
    """The single-seed=0 comparison already reported for this project's
    other holdout numbers is one point in a distribution -- P8.2/P8.3a
    already showed, on a different mechanism, that a single split/order
    can misrepresent a real effect's robustness. Runs the identical
    comparison across multiple seeds and returns every non-empty result,
    never averaging away a seed where the two policies disagree."""
    results = []
    for seed in seeds:
        result = run_context_transfer_diagnosis(
            records, domain=domain, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed
        )
        if result is not None:
            results.append(result)
    return tuple(results)


def result_to_dict(result: ContextTransferResult) -> dict:
    return {
        "domain": result.domain,
        "seed": result.seed,
        "n_train": result.n_train,
        "n_holdout": result.n_holdout,
        "global_prior_brier": result.global_prior_brier,
        "global_prior_ece": result.global_prior_ece,
        "context_bucket_brier": result.context_bucket_brier,
        "context_bucket_ece": result.context_bucket_ece,
        "brier_delta": result.brier_delta,
        "n_holdout_hitting_context_bucket": result.n_holdout_hitting_context_bucket,
        "n_distinct_context_keys_shared": result.n_distinct_context_keys_shared,
    }


__all__ = [
    "BASIS_CONTEXT_BUCKET",
    "BASIS_CONTEXT_GLOBAL_FALLBACK",
    "ContextOnlyPrediction",
    "ContextOnlyPolicy",
    "ContextTransferResult",
    "context_key",
    "run_context_transfer_diagnosis",
    "run_context_transfer_diagnosis_multi_seed",
    "result_to_dict",
]
