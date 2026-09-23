"""MetaHIA M6 -- internal-learning regularization diagnosis v0.1.

Direct follow-up to `m6_internal_learning_diagnosis_v0_1.py`'s real
result (2026-09-23, `documentation/MetaHIA_M6_Structural_Learning_V0_1.md`
Sec. 13): on every real domain corpus, once `EXACT_BUCKET`/`RULE_ONLY`
are made reachable at all (via `split_within_rule()`), the REAL
`StructuralLearningPolicy` loses to a flat global-prior baseline in
50/50 seed/domain combinations, 0 wins. The identified mechanism:
`StructuralLearningPolicy._to_prediction()` applies no smoothing, so a
bucket/rule with a single training observation (`support=1`, the ONLY
support level any current real corpus ever produces once
`min_records_per_rule=2` is enforced) yields a 100%-confident one-hot
prediction -- and the held-out second observation of that same rule
frequently disagrees (real, measured within-rule outcome inconsistency,
not assumed), incurring the maximum possible Brier penalty.

The project owner's own review of that result added a load-bearing
refinement, kept here without softening: the defect is not "missing
smoothing" alone -- it is the CONJUNCTION of (A) support as low as 1 and
(B) a rule's outcome genuinely not being deterministic even at fixed
`Rule x Context x Depth x Provenance`. Even perfect smoothing cannot
manufacture confidence a single observation does not warrant; the real
question is how many observations a genuinely non-deterministic rule
needs before its outcome distribution can be estimated at all reliably
-- a statistical convergence question, not merely "Laplace or not".

This module answers BOTH questions, as two separate measures, exactly
as the review requested, never conflating them:

  Measure A -- does regularization fix the REAL-corpus deficit? Three
    regularized `StructuralLearningPolicy` twins (never modifying it;
    same parallel-adapter discipline as every other M6/P4-T diagnostic
    in this project) compared against `M6_RAW` (byte-for-byte the same
    cascade and normalization as the real policy, included here as a
    consistency check, not a new baseline) and `GlobalOnlyPolicy`
    (imported unchanged from `m6_internal_learning_diagnosis_v0_1.py`),
    on the SAME real `split_within_rule()` splits already used there.

  Measure B -- does the estimator converge to a KNOWN true distribution
    as support grows? A controlled synthetic benchmark with several
    hand-chosen true outcome distributions (90/10, 50/50, 70/30) at
    support levels 1/2/5/10/20, scored against the TRUE distribution
    directly (mean squared distance over many independent samples per
    (distribution, support) cell) rather than against one holdout draw
    -- isolates estimator behavior from any single real corpus's small
    scale or particular quirks, exactly the review's own point that
    "Laplace wins on this 2-observation corpus" would be too weak a
    claim to draw from Measure A alone.

Governance point carried over unchanged from every prior M6 diagnostic:
`m6_structural_learning_v0_1.StructuralLearningPolicy` is READ ONLY --
never imported for mutation, never modified. Every regularized variant
here rebuilds its own bucket/rule/global counts from
`StructuralOutcomeRecord`'s own PUBLIC fields (`bucket_key()`,
`rule_signature`, `outcome`), the same pattern already used by
`GlobalOnlyPolicy`/`ContextOnlyPolicy`.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

from m4_cold_start_evidence_v0_1 import CONTRADICTED, SUPPORTED
from m6_internal_learning_diagnosis_v0_1 import GlobalOnlyPolicy, split_within_rule
from m6_structural_learning_v0_1 import (
    OUTCOME_CLASSES,
    StructuralOutcomeRecord,
    brier_score_multiclass,
    expected_calibration_error_top_label,
)


def _probe(rule: object, novelty: float, redundancy: float, depth: int, provenance: str) -> StructuralOutcomeRecord:
    """A throwaway record used ONLY to derive `bucket_key()`/
    `rule_signature` via `StructuralOutcomeRecord`'s own public
    methods -- the `outcome` value is never read, so an arbitrary valid
    class is used rather than importing `m6_structural_learning_v0_1`'s
    private `_band`/`_rule_signature` helpers a second time (already
    imported once for `m6_context_transfer_diagnosis_v0_1.py`'s
    `_band` reuse; a second private import here would be needless
    duplication of the same avoidance-of-drift argument for no added
    benefit, since this module needs the FULL bucket key AND the rule
    signature, both already exposed as a public two-for-one via this
    probe pattern)."""
    return StructuralOutcomeRecord(
        record_id="__probe__", rule=rule, novelty=novelty, redundancy=redundancy,
        depth=depth, provenance=provenance, outcome=OUTCOME_CLASSES[0],
    )


SmoothingFn = Callable[[Counter, Counter], Tuple[Mapping[str, float], int]]


def raw_smoothing(local_counts: Counter, _global_counts: Counter) -> Tuple[Mapping[str, float], int]:
    """No smoothing at all -- byte-for-byte the same normalization as
    `StructuralLearningPolicy._to_prediction()`. Included as `M6_RAW`,
    a consistency check that this module's independently-rebuilt
    cascade reproduces the real policy's own numbers exactly (verified
    by a dedicated test against `m6_internal_learning_diagnosis_v0_1`'s
    real `StructuralLearningPolicy` results), not a new baseline."""
    total = sum(local_counts.values())
    dist = {c: local_counts.get(c, 0) / total for c in OUTCOME_CLASSES}
    return dist, total


def laplace_smoothing(alpha: float) -> SmoothingFn:
    def _smooth(local_counts: Counter, _global_counts: Counter) -> Tuple[Mapping[str, float], int]:
        total = sum(local_counts.values())
        denom = total + alpha * len(OUTCOME_CLASSES)
        dist = {c: (local_counts.get(c, 0) + alpha) / denom for c in OUTCOME_CLASSES}
        return dist, total
    return _smooth


def support_weighted_smoothing(k: float) -> SmoothingFn:
    """Additive shrinkage toward the GLOBAL training prior, weighted by
    how much local support exists: `weight = n / (n + k)` -- support=1
    with k=1 gives 50% weight on the local estimate and 50% on the
    global prior; weight grows toward 1 (fully local) as support grows,
    exactly the "support 1 -> moderate confidence, support N -> local
    estimate dominates" behavior requested. `k` is a single, undyed
    constant (not tuned per domain/corpus -- doing so would be exactly
    the kind of forced-verdict tuning this project's own anti-cheating
    discipline refuses elsewhere, e.g. P4-T's Gate E)."""
    def _smooth(local_counts: Counter, global_counts: Counter) -> Tuple[Mapping[str, float], int]:
        n = sum(local_counts.values())
        global_total = sum(global_counts.values())
        local_dist = (
            {c: local_counts.get(c, 0) / n for c in OUTCOME_CLASSES}
            if n > 0
            else {c: 1.0 / len(OUTCOME_CLASSES) for c in OUTCOME_CLASSES}
        )
        global_dist = (
            {c: global_counts.get(c, 0) / global_total for c in OUTCOME_CLASSES}
            if global_total > 0
            else {c: 1.0 / len(OUTCOME_CLASSES) for c in OUTCOME_CLASSES}
        )
        weight = n / (n + k) if (n + k) > 0 else 0.0
        dist = {c: weight * local_dist[c] + (1.0 - weight) * global_dist[c] for c in OUTCOME_CLASSES}
        return dist, n
    return _smooth


@dataclass(frozen=True)
class RegularizedPrediction:
    distribution: Mapping[str, float]
    basis: str
    support: int


class RegularizedPolicy:
    """Rebuilds the SAME bucket/rule/global-count cascade as
    `StructuralLearningPolicy` (EXACT_BUCKET -> RULE_ONLY ->
    GLOBAL_PRIOR -> UNIFORM_NO_DATA), from `StructuralOutcomeRecord`'s
    public fields only, applying a pluggable `SmoothingFn` at whichever
    cascade level actually returns a prediction. Never imports or
    mutates `StructuralLearningPolicy`."""

    def __init__(self, name: str, smoothing: SmoothingFn) -> None:
        self.name = name
        self._smoothing = smoothing
        self._bucket_counts: Dict[tuple, Counter] = {}
        self._rule_counts: Dict[object, Counter] = {}
        self._global_counts: Counter = Counter()

    def fit(self, train_records: Sequence[StructuralOutcomeRecord]) -> "RegularizedPolicy":
        new = RegularizedPolicy(self.name, self._smoothing)
        bucket_counts: Dict[tuple, Counter] = defaultdict(Counter)
        rule_counts: Dict[object, Counter] = defaultdict(Counter)
        global_counts: Counter = Counter()
        for r in train_records:
            bucket_counts[r.bucket_key()][r.outcome] += 1
            rule_counts[r.rule_signature][r.outcome] += 1
            global_counts[r.outcome] += 1
        new._bucket_counts = dict(bucket_counts)
        new._rule_counts = dict(rule_counts)
        new._global_counts = global_counts
        return new

    def predict(self, rule: object, novelty: float, redundancy: float, depth: int, provenance: str) -> RegularizedPrediction:
        probe = _probe(rule, novelty, redundancy, depth, provenance)
        key = probe.bucket_key()
        sig = probe.rule_signature

        bucket = self._bucket_counts.get(key)
        if bucket:
            dist, support = self._smoothing(bucket, self._global_counts)
            return RegularizedPrediction(dist, f"{self.name}_EXACT_BUCKET", support)

        rule_bucket = self._rule_counts.get(sig)
        if rule_bucket:
            dist, support = self._smoothing(rule_bucket, self._global_counts)
            return RegularizedPrediction(dist, f"{self.name}_RULE_ONLY", support)

        if self._global_counts:
            dist, support = self._smoothing(self._global_counts, self._global_counts)
            return RegularizedPrediction(dist, f"{self.name}_GLOBAL_PRIOR", support)

        # No training data at all -- a genuinely different case from
        # "some data, low confidence warranted", handled directly
        # rather than routed through `self._smoothing` (which would
        # divide by zero for `raw_smoothing`'s plain frequency count):
        # mirrors `StructuralLearningPolicy.predict()`'s own separate
        # uniform branch, never routed through `_to_prediction()` either.
        uniform = {c: 1.0 / len(OUTCOME_CLASSES) for c in OUTCOME_CLASSES}
        return RegularizedPrediction(uniform, f"{self.name}_UNIFORM_NO_DATA", 0)


def build_policy_variants() -> Dict[str, Callable[[], object]]:
    """Factory functions (not instances) so each seed/domain gets a
    fresh, independently-fitted policy of every variant. `GLOBAL_ONLY`
    is `GlobalOnlyPolicy` imported unchanged from
    `m6_internal_learning_diagnosis_v0_1.py` -- not reimplemented here."""
    return {
        "GLOBAL_ONLY": lambda: GlobalOnlyPolicy(),
        "M6_RAW": lambda: RegularizedPolicy("M6_RAW", raw_smoothing),
        "M6_LAPLACE_A1": lambda: RegularizedPolicy("M6_LAPLACE_A1", laplace_smoothing(1.0)),
        "M6_LAPLACE_A0.5": lambda: RegularizedPolicy("M6_LAPLACE_A0.5", laplace_smoothing(0.5)),
        "M6_SUPPORT_WEIGHTED_K1": lambda: RegularizedPolicy("M6_SUPPORT_WEIGHTED_K1", support_weighted_smoothing(1.0)),
    }


@dataclass(frozen=True)
class RegularizedComparisonResult:
    domain: str
    seed: int
    n_train: int
    n_holdout: int
    brier: Mapping[str, float]
    ece: Mapping[str, float]

    def brier_delta_vs_global_only(self, variant: str) -> float:
        return self.brier[variant] - self.brier["GLOBAL_ONLY"]


def run_regularized_comparison(
    records: Sequence[StructuralOutcomeRecord],
    *,
    domain: str,
    seed: int = 0,
    val_fraction: float = 0.0,
    holdout_fraction: float = 0.5,
    min_records_per_rule: int = 2,
) -> Optional[RegularizedComparisonResult]:
    """Fits every variant from `build_policy_variants()` on the IDENTICAL
    `split_within_rule()` train split (same function, same parameters,
    as `m6_internal_learning_diagnosis_v0_1.run_internal_learning_diagnosis`)
    and scores all of them on the identical holdout."""
    train, _val, holdout = split_within_rule(
        records, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed, min_records_per_rule=min_records_per_rule
    )
    if not train or not holdout:
        return None

    variants = build_policy_variants()
    brier = {}
    ece = {}
    for name, ctor in variants.items():
        policy = ctor().fit(train)
        brier[name] = brier_score_multiclass(policy, holdout)
        ece[name] = expected_calibration_error_top_label(policy, holdout)

    return RegularizedComparisonResult(domain=domain, seed=seed, n_train=len(train), n_holdout=len(holdout), brier=brier, ece=ece)


def run_regularized_comparison_multi_seed(
    records: Sequence[StructuralOutcomeRecord],
    *,
    domain: str,
    seeds: Sequence[int] = tuple(range(10)),
    val_fraction: float = 0.0,
    holdout_fraction: float = 0.5,
    min_records_per_rule: int = 2,
) -> Tuple[RegularizedComparisonResult, ...]:
    results = []
    for seed in seeds:
        result = run_regularized_comparison(
            records, domain=domain, seed=seed, val_fraction=val_fraction,
            holdout_fraction=holdout_fraction, min_records_per_rule=min_records_per_rule,
        )
        if result is not None:
            results.append(result)
    return tuple(results)


def comparison_result_to_dict(result: RegularizedComparisonResult) -> dict:
    return {
        "domain": result.domain,
        "seed": result.seed,
        "n_train": result.n_train,
        "n_holdout": result.n_holdout,
        "brier": dict(result.brier),
        "ece": dict(result.ece),
        "brier_delta_vs_global_only": {name: result.brier_delta_vs_global_only(name) for name in result.brier if name != "GLOBAL_ONLY"},
    }


# ---------------------------------------------------------------------------
# Measure B: synthetic convergence benchmark.
# ---------------------------------------------------------------------------


def _pattern(name: str) -> object:
    from kernel2 import OBSERVATION, Node, node_ref

    return Node(f"rule::{name}", OBSERVATION, (node_ref(name),))


def _default_background_records(n_rules: int = 10) -> Tuple[StructuralOutcomeRecord, ...]:
    """A small, fixed, balanced set of OTHER rules (never the rule under
    test) giving GLOBAL_PRIOR-based smoothing a genuinely different
    distribution to shrink toward. Without this, a benchmark built
    around a single tested rule makes `_rule_counts[sig]` and
    `_global_counts` IDENTICAL Counters by construction (nothing else
    was ever fit) -- `support_weighted_smoothing` then blends the local
    estimate toward itself, which is a no-op, not real shrinkage (found
    the hard way: a first version of this benchmark reported
    `M6_SUPPORT_WEIGHTED_K1` performing byte-identically to `M6_RAW` at
    every support level, before this background was added). Balanced
    50/50 SUPPORTED/CONTRADICTED across 10 distinct background rules --
    a neutral choice, not tuned toward whichever `true_distribution` is
    being tested."""
    pattern = _pattern
    return tuple(
        StructuralOutcomeRecord(
            record_id=f"background-{i}", rule=pattern(f"BACKGROUND_RULE_{i}"), novelty=0.5, redundancy=0.5,
            depth=1, provenance="GROUNDED_DIRECT", outcome=(SUPPORTED if i % 2 == 0 else CONTRADICTED),
        )
        for i in range(n_rules)
    )


def measure_convergence(
    true_distribution: Mapping[str, float],
    *,
    n: int,
    n_trials: int = 200,
    seed: int = 0,
    background_records: Sequence[StructuralOutcomeRecord] = (),
) -> Dict[str, float]:
    """For each policy variant, draws `n_trials` independent samples of
    `n` observations each from `true_distribution` (a single fixed
    rule/context throughout, so every drawn observation lands in the
    SAME bucket), fits the policy on that sample PLUS `background_records`
    (defaults to `_default_background_records()`, a fixed balanced set
    of unrelated rules -- see its docstring for why this is required,
    not optional, for `support_weighted_smoothing` to be tested
    meaningfully), and measures the mean squared distance between its
    predicted distribution and the KNOWN true distribution -- never
    against a single noisy holdout draw, the randomness a real-corpus
    Measure A comparison cannot avoid at this corpus scale. Lower is
    better; 0 is perfect."""
    if abs(sum(true_distribution.values()) - 1.0) > 1e-9:
        raise ValueError("true_distribution must sum to 1.0")
    if not background_records:
        background_records = _default_background_records()
    rng = random.Random(seed)
    classes = list(true_distribution.keys())
    weights = [true_distribution[c] for c in classes]
    rule = _pattern("SYNTH_RULE")
    variants = build_policy_variants()
    totals = {name: 0.0 for name in variants}

    for trial in range(n_trials):
        outcomes = rng.choices(classes, weights=weights, k=n)
        tested = tuple(
            StructuralOutcomeRecord(
                record_id=f"synth-{trial}-{i}", rule=rule, novelty=0.5, redundancy=0.5, depth=1,
                provenance="GROUNDED_DIRECT", outcome=outcome,
            )
            for i, outcome in enumerate(outcomes)
        )
        train = tested + tuple(background_records)
        for name, ctor in variants.items():
            policy = ctor().fit(train)
            pred = policy.predict(rule, 0.5, 0.5, 1, "GROUNDED_DIRECT")
            totals[name] += sum(
                (pred.distribution.get(c, 0.0) - true_distribution.get(c, 0.0)) ** 2 for c in OUTCOME_CLASSES
            )

    return {name: totals[name] / n_trials for name in variants}


def run_convergence_benchmark(
    true_distributions: Mapping[str, Mapping[str, float]],
    *,
    supports: Sequence[int] = (1, 2, 5, 10, 20),
    n_trials: int = 200,
    seed: int = 0,
) -> Dict[str, Dict[int, Dict[str, float]]]:
    """Runs `measure_convergence()` for every (true_distribution, support)
    cell, returning `{distribution_label: {support: {variant: mse}}}`."""
    results: Dict[str, Dict[int, Dict[str, float]]] = {}
    for label, dist in true_distributions.items():
        results[label] = {}
        for n in supports:
            results[label][n] = measure_convergence(dist, n=n, n_trials=n_trials, seed=seed)
    return results


__all__ = [
    "SmoothingFn",
    "raw_smoothing",
    "laplace_smoothing",
    "support_weighted_smoothing",
    "RegularizedPrediction",
    "RegularizedPolicy",
    "build_policy_variants",
    "RegularizedComparisonResult",
    "run_regularized_comparison",
    "run_regularized_comparison_multi_seed",
    "comparison_result_to_dict",
    "measure_convergence",
    "run_convergence_benchmark",
]
