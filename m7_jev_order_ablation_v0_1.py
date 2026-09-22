"""MetaHIA M7 -- JEV/Kev P8.2: demonstration-order ablation for STRICT.

Follow-up to P8.1 (`m7_jev_benchmark_v0_2.py`,
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 6quater),
requested explicitly after P8.1's real result showed all 4 `PERE_DE`
positive cases predicted `MERE_DE` in STRICT mode -- a change from v0.1
(no such systematic failure) correlated with, but not yet shown to be
CAUSED by, `MERE_DE`'s 3 demonstrations sitting immediately before
`PERE_DE`'s 3 in `corpus/jev_benchmark_cases_v0_2.json`'s
`demonstration_set` (indices 0-2 vs 3-5, verified directly). This module
is an ablation, not a prompt improvement: same demonstration content,
same 39 evaluation cases, same model, same vocabulary -- only the ORDER
in which the 24 demonstrations are presented to STRICT changes.

Scope note, load-bearing: only STRICT consumes `demonstration_set` at
all (`m7_jev_benchmark_v0_2.run_benchmark` passes `worked_examples=()`
to LABELED/GLOSSED -- verified by reading that function, not assumed).
Re-running LABELED/GLOSSED under different "demonstration orders" would
be a null experiment: there is nothing in their request that could
depend on demonstration order, since they never receive one. P8.2 is
therefore STRICT-only, deliberately, not a narrowed re-run of P8.1's
3-condition benchmark.

Two order-generation strategies:

  interleaved -- groups the 24 demonstrations by relation (preserving
      each group's internal order), then round-robins across groups in
      alphabetical order (AUCUNE, EPOUSE_DE, EPOUX_DE, MERE_DE, PERE_DE)
      -- deterministic, and specifically separates every `MERE_DE`
      demonstration from every `PERE_DE` one, the minimal change needed
      to test the recency-adjacency hypothesis directly.
  random(seed) -- a uniform random permutation of the same 24 entries,
      via `random.Random(seed).sample(...)` -- deterministic per seed
      (same seed always produces the same order, required for a
      reproducible, re-runnable experiment) but otherwise uncorrelated
      with the original grouping.

The original P8.1 order itself (`load_corpus()`'s own
`demonstration_set`, unpermuted) is NOT re-run here -- its STRICT result
already exists, real and saved
(`validation/jev_benchmark_v0_2_results_2026-09-22.json`), and re-running
an unchanged input against the same server would only add cost, not
evidence. `run_order_ablation` accepts it as `baseline_report` purely for
comparison/aggregation, never re-queries it.
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

from m7_jev_benchmark_v0_2 import (
    CORPUS_PATH,
    AUCUNE,
    BenchmarkCase,
    CaseOutcome,
    ConditionReport,
    load_corpus,
)
from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_STRICT,
    JevDecideClient,
    WorkedExample,
    propose_relation_jev,
)

TRACKED_CONFUSION_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("PERE_DE", "MERE_DE"),
    ("MERE_DE", "PERE_DE"),
    ("EPOUX_DE", "EPOUSE_DE"),
    ("EPOUSE_DE", "EPOUX_DE"),
)


_INTERLEAVE_GROUP_ORDER: Tuple[str, ...] = ("MERE_DE", "EPOUX_DE", "PERE_DE", "EPOUSE_DE", AUCUNE)
"""Deliberately NOT alphabetical. Round-robining in alphabetical order
(AUCUNE, EPOUSE_DE, EPOUX_DE, MERE_DE, PERE_DE) still puts every
MERE_DE demonstration immediately before the matching-index PERE_DE one
-- alphabetical adjacency reproduces exactly the adjacency this ablation
exists to break (caught by this module's own test before any real
network call was trusted). This order instead places one OTHER relation
between each member of both known-confusable pairs (`MERE_DE`/`PERE_DE`,
`EPOUX_DE`/`EPOUSE_DE`, both documented in P8.1): MERE_DE, EPOUX_DE,
PERE_DE, EPOUSE_DE never sit next to their confusable partner, in any
round or at any round boundary."""


def build_interleaved_order(demonstration_set: Sequence[WorkedExample]) -> Tuple[WorkedExample, ...]:
    """Round-robins across relation groups (`_INTERLEAVE_GROUP_ORDER`,
    original within-group order preserved) so that neither `MERE_DE`/
    `PERE_DE` nor `EPOUX_DE`/`EPOUSE_DE` -- the two confusable pairs
    P8.1 measured -- are ever adjacent in the output, unlike the
    original corpus order (`MERE_DE` immediately followed by
    `PERE_DE`)."""
    groups: Dict[str, list] = {}
    for example in demonstration_set:
        groups.setdefault(example.relation, []).append(example)
    ordered_relations = [r for r in _INTERLEAVE_GROUP_ORDER if r in groups]
    ordered_relations += [r for r in groups if r not in ordered_relations]  # fail-safe: never silently drop a group
    result: list = []
    index = 0
    while any(index < len(groups[r]) for r in ordered_relations):
        for relation in ordered_relations:
            bucket = groups[relation]
            if index < len(bucket):
                result.append(bucket[index])
        index += 1
    return tuple(result)


def build_random_order(demonstration_set: Sequence[WorkedExample], *, seed: int) -> Tuple[WorkedExample, ...]:
    """Deterministic per seed: the same seed always yields the same
    permutation, so the experiment is exactly reproducible without
    re-querying the server."""
    return tuple(random.Random(seed).sample(list(demonstration_set), k=len(demonstration_set)))


@dataclass(frozen=True)
class OrderedCondition:
    label: str
    demonstrations: Tuple[WorkedExample, ...]


def build_seed_orders(demonstration_set: Sequence[WorkedExample], seeds: Sequence[int]) -> Tuple[OrderedCondition, ...]:
    return tuple(
        OrderedCondition(label=f"STRICT_seed{seed}", demonstrations=build_random_order(demonstration_set, seed=seed))
        for seed in seeds
    )


def run_order_ablation(
    client: JevDecideClient,
    orders: Sequence[OrderedCondition],
    *,
    corpus_path: Path = CORPUS_PATH,
) -> Tuple[ConditionReport, ...]:
    """Runs the full 39-case evaluation corpus through STRICT for each
    supplied demonstration order. Always STRICT -- see module docstring
    for why LABELED/GLOSSED are out of scope for an order ablation.
    Never re-derives `orders` itself: callers build them via
    `build_interleaved_order`/`build_seed_orders` so the exact set of
    orders used is visible at the call site, not buried in this
    function.
    """
    vocabulary, _default_demonstration_set, cases = load_corpus(corpus_path)
    reports = []
    for order in orders:
        outcomes = []
        for case in cases:
            proposal = propose_relation_jev(
                text=case.text,
                subject=case.subject,
                obj=case.object,
                all_relations=vocabulary,
                semantic_condition=RELATION_VOCABULARY_MODE_STRICT,
                client=client,
                worked_examples=order.demonstrations,
            )
            outcomes.append(
                CaseOutcome(
                    case_id=case.case_id,
                    category=case.category,
                    expected_relation=case.expected_relation,
                    proposal=proposal,
                )
            )
        reports.append(ConditionReport(semantic_condition=order.label, vocabulary=vocabulary, outcomes=tuple(outcomes)))
    return tuple(reports)


def _confusion_rate(report: ConditionReport, expected: str, predicted: str) -> Optional[float]:
    matrix = report.confusion_matrix
    row = matrix.get(expected, {})
    total = sum(row.values())
    if total == 0:
        return None
    return row.get(predicted, 0) / total


@dataclass(frozen=True)
class OrderAblationSummary:
    """Aggregates a set of same-corpus, order-varying `ConditionReport`s
    (typically the seed set, never the interleaved/baseline single
    points, which have no variance of their own to report)."""

    labels: Tuple[str, ...]
    overall_accuracy_values: Tuple[Optional[float], ...]
    positive_accuracy_values: Tuple[Optional[float], ...]
    adversarial_accuracy_values: Tuple[Optional[float], ...]
    confusion_rates: Mapping[Tuple[str, str], Tuple[Optional[float], ...]]
    near_synonym_resistance_count: int
    n_reports: int

    @staticmethod
    def _stats(values: Sequence[Optional[float]]) -> Optional[Dict[str, float]]:
        usable = [v for v in values if v is not None]
        if not usable:
            return None
        return {
            "mean": statistics.fmean(usable),
            "stdev": statistics.stdev(usable) if len(usable) > 1 else 0.0,
            "min": min(usable),
            "max": max(usable),
        }

    @property
    def overall_accuracy_stats(self) -> Optional[Dict[str, float]]:
        return self._stats(self.overall_accuracy_values)

    @property
    def positive_accuracy_stats(self) -> Optional[Dict[str, float]]:
        return self._stats(self.positive_accuracy_values)

    @property
    def adversarial_accuracy_stats(self) -> Optional[Dict[str, float]]:
        return self._stats(self.adversarial_accuracy_values)

    def confusion_rate_stats(self, expected: str, predicted: str) -> Optional[Dict[str, float]]:
        return self._stats(self.confusion_rates.get((expected, predicted), ()))

    @property
    def near_synonym_resistance_rate(self) -> Optional[float]:
        if self.n_reports == 0:
            return None
        return self.near_synonym_resistance_count / self.n_reports


def summarize_order_ablation(reports: Sequence[ConditionReport]) -> OrderAblationSummary:
    confusion_rates: Dict[Tuple[str, str], Tuple[Optional[float], ...]] = {
        pair: tuple(_confusion_rate(r, *pair) for r in reports) for pair in TRACKED_CONFUSION_PAIRS
    }
    return OrderAblationSummary(
        labels=tuple(r.semantic_condition for r in reports),
        overall_accuracy_values=tuple(r.overall_accuracy for r in reports),
        positive_accuracy_values=tuple(r.positive_accuracy for r in reports),
        adversarial_accuracy_values=tuple(r.adversarial_accuracy for r in reports),
        confusion_rates=confusion_rates,
        near_synonym_resistance_count=sum(1 for r in reports if r.near_synonym_all_paraphrases_correct),
        n_reports=len(reports),
    )


def summary_to_dict(summary: OrderAblationSummary) -> dict:
    return {
        "labels": list(summary.labels),
        "n_reports": summary.n_reports,
        "overall_accuracy_stats": summary.overall_accuracy_stats,
        "positive_accuracy_stats": summary.positive_accuracy_stats,
        "adversarial_accuracy_stats": summary.adversarial_accuracy_stats,
        "confusion_rate_stats": {
            f"{expected}_to_{predicted}": summary.confusion_rate_stats(expected, predicted)
            for expected, predicted in TRACKED_CONFUSION_PAIRS
        },
        "near_synonym_resistance_rate": summary.near_synonym_resistance_rate,
    }


__all__ = [
    "TRACKED_CONFUSION_PAIRS",
    "OrderedCondition",
    "OrderAblationSummary",
    "build_interleaved_order",
    "build_random_order",
    "build_seed_orders",
    "run_order_ablation",
    "summarize_order_ablation",
    "summary_to_dict",
]
