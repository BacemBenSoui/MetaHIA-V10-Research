"""Permanent invariant tests for M7 -- JEV/Kev P8.3a LABELED
criteria-order ablation (`m7_jev_label_order_ablation_v0_1.py`).

Uses injected fake `JevDecideClient`s throughout -- no network call.
Same discipline as `tests/test_m7_jev_order_ablation_v0_1.py`: verify
order generation, verify the order actually reaches the client, verify
the aggregation reuse (`summarize_order_ablation` from the STRICT
ablation module, deliberately reused rather than reimplemented) is
correct against hand-computed values -- all before any real network
run is trusted.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Optional

import pytest

from m7_jev_benchmark_v0_2 import load_corpus
from m7_jev_label_order_ablation_v0_1 import (
    LabelOrderedCondition,
    build_aucune_first_label_order,
    build_label_seed_orders,
    build_separated_label_order,
    run_label_order_ablation,
)
from m7_jev_order_ablation_v0_1 import summarize_order_ablation, summary_to_dict


# ---------------------------------------------------------------------------
# 1. Order generation.
# ---------------------------------------------------------------------------


def test_original_corpus_order_has_epoux_and_epouse_adjacent():
    """The fact motivating this whole module -- verified directly
    against the real corpus, not assumed from the docstring."""
    vocabulary, _, _ = load_corpus()
    assert list(vocabulary) == ["EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE", "AUCUNE"]


def test_separated_label_order_is_a_permutation_with_no_confusable_pair_adjacent():
    vocabulary, _, _ = load_corpus()
    order = build_separated_label_order(vocabulary)
    assert set(order) == set(vocabulary)
    assert len(order) == len(vocabulary)
    for a, b in zip(order, order[1:]):
        assert {a, b} != {"EPOUX_DE", "EPOUSE_DE"}
        assert {a, b} != {"MERE_DE", "PERE_DE"}
    assert order[-1] == "AUCUNE"  # same position as the original corpus order


def test_aucune_first_label_order_isolates_the_position_variable():
    vocabulary, _, _ = load_corpus()
    order = build_aucune_first_label_order(vocabulary)
    assert set(order) == set(vocabulary)
    assert order[0] == "AUCUNE"
    # EPOUX_DE/EPOUSE_DE keep their original relative adjacency and order
    epoux_index = order.index("EPOUX_DE")
    epouse_index = order.index("EPOUSE_DE")
    assert epouse_index == epoux_index + 1


def test_designed_orders_reject_a_mismatched_vocabulary():
    with pytest.raises(ValueError):
        build_separated_label_order(["EPOUX_DE", "EPOUSE_DE"])  # missing MERE_DE/PERE_DE/AUCUNE


def test_build_label_seed_orders_produces_permutations_deterministic_per_seed():
    vocabulary, _, _ = load_corpus()
    conditions_a = build_label_seed_orders(vocabulary, seeds=(1, 2, 3))
    conditions_b = build_label_seed_orders(vocabulary, seeds=(1, 2, 3))
    assert len(conditions_a) == 3
    assert len({c.label for c in conditions_a}) == 3
    for c in conditions_a:
        assert set(c.relations) == set(vocabulary)
    # same seeds -> same permutations, required for reproducibility
    assert [c.relations for c in conditions_a] == [c.relations for c in conditions_b]


def test_seed_orders_differ_from_each_other():
    vocabulary, _, _ = load_corpus()
    (cond1,) = build_label_seed_orders(vocabulary, seeds=(1,))
    (cond2,) = build_label_seed_orders(vocabulary, seeds=(2,))
    assert cond1.relations != cond2.relations


# ---------------------------------------------------------------------------
# 2. run_label_order_ablation reaches the client with the supplied order.
# ---------------------------------------------------------------------------


class _RecordingLabeledClient:
    """Always answers correctly by matching case text, but records the
    exact `criteria` key order it was given for every call -- proves
    the supplied label order actually reaches the wire, and that no
    description (gloss) ever leaks into a LABELED call."""

    def __init__(self, expected_by_text: Mapping[str, str]):
        self.expected_by_text = expected_by_text
        self.seen_criteria_orders = []

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        self.seen_criteria_orders.append(tuple(criteria.keys()))
        assert all(v is None for v in criteria.values()), "LABELED must never send a description"
        for text, expected in self.expected_by_text.items():
            if text in state:
                others = [r for r in criteria if r != expected]
                remainder = 0.0 if not others else 0.1
                dist = {expected: 1.0 - remainder * len(others), **{o: remainder for o in others}}
                return expected, dist[expected], dist
        raise AssertionError(f"no known case text found in state: {state!r}")


def test_run_label_order_ablation_sends_criteria_in_the_supplied_order():
    vocabulary, _, cases = load_corpus()
    expected_by_text = {c.text: c.expected_relation for c in cases}
    client = _RecordingLabeledClient(expected_by_text)

    order = LabelOrderedCondition(label="LABELED_test", relations=("AUCUNE", "PERE_DE", "MERE_DE", "EPOUSE_DE", "EPOUX_DE"))
    (report,) = run_label_order_ablation(client, (order,))

    assert report.semantic_condition == "LABELED_test"
    assert report.overall_accuracy == 1.0
    for seen_order in client.seen_criteria_orders:
        assert seen_order == order.relations


def test_run_label_order_ablation_never_sends_a_description():
    """Redundant with the assertion inside `_RecordingLabeledClient`,
    kept explicit so a future refactor that removed that assertion
    would still be caught by a named test."""
    vocabulary, _, cases = load_corpus()
    expected_by_text = {c.text: c.expected_relation for c in cases}
    client = _RecordingLabeledClient(expected_by_text)
    order = LabelOrderedCondition(label="LABELED_test", relations=tuple(vocabulary))
    run_label_order_ablation(client, (order,))  # would raise inside the client if violated


# ---------------------------------------------------------------------------
# 3. Aggregation reuse: `summarize_order_ablation` is generic over
#    WHAT varied between reports (STRICT demonstrations, LABELED
#    criteria order) -- must work unmodified on this module's reports.
# ---------------------------------------------------------------------------


def test_summarize_order_ablation_reused_unmodified_on_labeled_reports():
    vocabulary, _, cases = load_corpus()
    expected_by_text = {c.text: c.expected_relation for c in cases}
    seed_orders = build_label_seed_orders(vocabulary, seeds=(1, 2))
    client = _RecordingLabeledClient(expected_by_text)
    reports = run_label_order_ablation(client, seed_orders)

    summary = summarize_order_ablation(reports)
    assert summary.n_reports == 2
    assert summary.overall_accuracy_stats["mean"] == pytest.approx(1.0)

    payload = summary_to_dict(summary)
    json.dumps(payload)  # must not raise
