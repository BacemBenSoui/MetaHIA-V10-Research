"""MetaHIA M7 -- JEV/Kev P8.3a: LABELED criteria-order ablation.

Explicit follow-up requested after P8.2: P8.2 showed STRICT's
performance is highly sensitive to the ORDER of its few-shot
demonstrations. Before treating LABELED's P8.1 result (overall 74.4%,
Brier 0.377, ECE 0.137 -- the current best-justified candidate for
`m7_corpus_from_jev_v0_1.py`) as settled, the same question needs
asking of LABELED's own only order-dependent input: the ORDER of the
`criteria` mapping's keys (the real relation names), which
`propose_relation_jev`'s LABELED branch builds directly from the
caller-supplied `all_relations` sequence
(`criteria = {r: None for r in all_relations}` -- verified by reading
`m7_jev_relation_choice_v0_1.py` directly, not assumed). LABELED never
receives worked examples at all, so P8.2's demonstration-order ablation
has nothing to say about it; this is a distinct axis, needing its own
ablation.

Motivating, already-measured fact: `corpus/jev_benchmark_cases_v0_2.json`'s
`relation_vocabulary` is `["EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE",
"AUCUNE"]` -- `EPOUX_DE` and `EPOUSE_DE`, the one confusable pair P8.1
measured LABELED actually getting wrong (4/4, opposite direction from
STRICT), sit ADJACENT in this order, exactly the kind of adjacency P8.2
found causally relevant for STRICT. Whether the same holds for LABELED
is untested before this module.

Three designed orders isolate three different variables, deliberately
NOT confounded with each other:

  original    -- `load_corpus()`'s own vocabulary order (the P8.1
                 baseline itself, NOT re-run here for the same reason
                 P8.2 didn't re-run STRICT's original order: it is
                 already measured and saved).
  separated   -- EPOUX_DE and EPOUSE_DE (and, for consistency, MERE_DE
                 and PERE_DE) are never adjacent; AUCUNE stays LAST,
                 same position as `original` -- isolates the
                 "confusable-pair adjacency" variable alone.
  aucune_first -- AUCUNE moves to FIRST position; EPOUX_DE/EPOUSE_DE
                 keep their original adjacency and relative order --
                 isolates the "reject-option position" variable alone
                 (a known LLM multiple-choice position-bias hypothesis,
                 distinct from the adjacency question).

Plus 10 deterministic random-seed permutations (seeds 1-10, same
convention as `m7_jev_order_ablation_v0_1.py`'s STRICT ablation) to
measure baseline variance the same way P8.2 did.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Tuple

from m7_jev_benchmark_v0_2 import CORPUS_PATH, CaseOutcome, ConditionReport, load_corpus
from m7_jev_order_ablation_v0_1 import build_random_order  # generic permutation-by-seed, reused as-is
from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_LABELED,
    JevDecideClient,
    WorkedExample,
    propose_relation_jev,
)

_SEPARATED_LABEL_ORDER: Tuple[str, ...] = ("EPOUX_DE", "MERE_DE", "EPOUSE_DE", "PERE_DE", "AUCUNE")
_AUCUNE_FIRST_LABEL_ORDER: Tuple[str, ...] = ("AUCUNE", "EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE")


@dataclass(frozen=True)
class LabelOrderedCondition:
    label: str
    relations: Tuple[str, ...]


def _reordered(vocabulary: Sequence[str], target_order: Sequence[str]) -> Tuple[str, ...]:
    """Reorders `vocabulary` to match `target_order` -- fails loud if the
    two don't cover the same set, rather than silently dropping or
    duplicating a relation (the same discipline as GLOSSED's own
    missing-gloss check in `propose_relation_jev`)."""
    if set(vocabulary) != set(target_order):
        raise ValueError(f"vocabulary {sorted(vocabulary)} does not match the designed order's relation set {sorted(target_order)}")
    return tuple(r for r in target_order if r in vocabulary)


def build_separated_label_order(vocabulary: Sequence[str]) -> Tuple[str, ...]:
    """Neither confusable pair (`EPOUX_DE`/`EPOUSE_DE`, `MERE_DE`/
    `PERE_DE`) is adjacent; `AUCUNE` stays last, same position as the
    original corpus order -- isolates confusable-pair adjacency from
    `AUCUNE`'s position."""
    return _reordered(vocabulary, _SEPARATED_LABEL_ORDER)


def build_aucune_first_label_order(vocabulary: Sequence[str]) -> Tuple[str, ...]:
    """`AUCUNE` moves to first position; `EPOUX_DE`/`EPOUSE_DE` keep
    their original adjacency -- isolates `AUCUNE`'s position from
    confusable-pair adjacency."""
    return _reordered(vocabulary, _AUCUNE_FIRST_LABEL_ORDER)


def build_label_seed_orders(vocabulary: Sequence[str], seeds: Sequence[int]) -> Tuple[LabelOrderedCondition, ...]:
    """Deterministic per seed, same convention as
    `m7_jev_order_ablation_v0_1.build_seed_orders`. Reuses
    `build_random_order` (a plain Fisher-Yates-via-`random.sample`
    permutation, agnostic to what it's permuting) by wrapping each
    relation name in a throwaway `WorkedExample` and unwrapping the
    `.text` field back out -- avoids a second, drift-prone
    reimplementation of the same seeded-shuffle logic for a bare
    string sequence."""
    conditions = []
    for seed in seeds:
        wrapped = tuple(WorkedExample(text=r, relation=r) for r in vocabulary)
        shuffled = build_random_order(wrapped, seed=seed)
        conditions.append(LabelOrderedCondition(label=f"LABELED_seed{seed}", relations=tuple(w.text for w in shuffled)))
    return tuple(conditions)


def run_label_order_ablation(
    client: JevDecideClient,
    orders: Sequence[LabelOrderedCondition],
    *,
    corpus_path: Path = CORPUS_PATH,
) -> Tuple[ConditionReport, ...]:
    """Runs the full 39-case evaluation corpus through LABELED for each
    supplied criteria order. Always LABELED -- LABELED never receives
    worked examples or glosses, so nothing else varies between orders
    except the `all_relations` sequence that becomes `criteria`'s key
    order inside `propose_relation_jev`.
    """
    _default_vocabulary, _demonstration_set, cases = load_corpus(corpus_path)
    reports = []
    for order in orders:
        outcomes = []
        for case in cases:
            proposal = propose_relation_jev(
                text=case.text,
                subject=case.subject,
                obj=case.object,
                all_relations=order.relations,
                semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
                client=client,
            )
            outcomes.append(
                CaseOutcome(
                    case_id=case.case_id,
                    category=case.category,
                    expected_relation=case.expected_relation,
                    proposal=proposal,
                )
            )
        reports.append(ConditionReport(semantic_condition=order.label, vocabulary=order.relations, outcomes=tuple(outcomes)))
    return tuple(reports)


__all__ = [
    "LabelOrderedCondition",
    "build_separated_label_order",
    "build_aucune_first_label_order",
    "build_label_seed_orders",
    "run_label_order_ablation",
]
