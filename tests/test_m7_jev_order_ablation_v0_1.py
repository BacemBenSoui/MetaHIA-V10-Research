"""Permanent invariant tests for M7 -- JEV/Kev P8.2 order ablation
(`m7_jev_order_ablation_v0_1.py`).

Uses injected fake `JevDecideClient`s throughout -- no network call.
Verifies order-generation (interleaving actually separates MERE_DE/
PERE_DE, random orders are permutations, deterministic per seed),
that `run_order_ablation` is STRICT-only by construction (never sends a
real relation name as a criteria key), and the aggregation math
(mean/stdev/min/max, per-pair confusion rate, near-synonym resistance
rate) against hand-computed expected values, before any real network run
is trusted -- the same discipline already applied in
`tests/test_m7_jev_benchmark_v0_2.py`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Optional

import pytest

from m7_jev_benchmark_v0_2 import CaseOutcome, ConditionReport, NEAR_SYNONYM_CATEGORY, load_corpus
from m7_jev_order_ablation_v0_1 import (
    TRACKED_CONFUSION_PAIRS,
    OrderedCondition,
    build_interleaved_order,
    build_random_order,
    build_seed_orders,
    run_order_ablation,
    summarize_order_ablation,
    summary_to_dict,
)
from m7_jev_relation_choice_v0_1 import JevProposal, build_strict_symbol_map


# ---------------------------------------------------------------------------
# 1. Order generation.
# ---------------------------------------------------------------------------


def test_interleaved_order_is_a_permutation_of_the_original_demonstration_set():
    _, demonstration_set, _ = load_corpus()
    interleaved = build_interleaved_order(demonstration_set)
    assert len(interleaved) == len(demonstration_set)
    assert {(e.text, e.relation) for e in interleaved} == {(e.text, e.relation) for e in demonstration_set}


def test_interleaved_order_separates_mere_de_from_pere_de():
    """The specific, minimal property this ablation is designed to test:
    the original corpus has all 3 MERE_DE demonstrations immediately
    followed by all 3 PERE_DE ones (verified directly against the real
    file, not assumed) -- interleaving must break every such adjacency."""
    _, demonstration_set, _ = load_corpus()
    original_relations = [e.relation for e in demonstration_set]
    assert original_relations[2] == "MERE_DE" and original_relations[3] == "PERE_DE"

    interleaved = build_interleaved_order(demonstration_set)
    relations = [e.relation for e in interleaved]
    for a, b in zip(relations, relations[1:]):
        assert not (a == "MERE_DE" and b == "PERE_DE")
        assert not (a == "PERE_DE" and b == "MERE_DE")


def test_random_order_is_deterministic_per_seed_and_a_true_permutation():
    _, demonstration_set, _ = load_corpus()
    order_a = build_random_order(demonstration_set, seed=7)
    order_b = build_random_order(demonstration_set, seed=7)
    assert order_a == order_b  # same seed -> same order, required for reproducibility
    assert {(e.text, e.relation) for e in order_a} == {(e.text, e.relation) for e in demonstration_set}


def test_random_order_differs_across_seeds():
    _, demonstration_set, _ = load_corpus()
    order_1 = build_random_order(demonstration_set, seed=1)
    order_2 = build_random_order(demonstration_set, seed=2)
    assert order_1 != order_2


def test_build_seed_orders_produces_one_uniquely_labeled_condition_per_seed():
    _, demonstration_set, _ = load_corpus()
    conditions = build_seed_orders(demonstration_set, seeds=(1, 2, 3))
    assert len(conditions) == 3
    assert len({c.label for c in conditions}) == 3
    for c in conditions:
        assert {(e.text, e.relation) for e in c.demonstrations} == {(e.text, e.relation) for e in demonstration_set}


# ---------------------------------------------------------------------------
# 2. run_order_ablation is STRICT-only by construction.
# ---------------------------------------------------------------------------


@pytest.fixture()
def tiny_corpus(tmp_path: Path) -> Path:
    payload = {
        "relation_vocabulary": ["MERE_DE", "PERE_DE"],
        "demonstration_set": [
            {"text": "Ana est la mere de Bob.", "relation": "MERE_DE"},
            {"text": "Cid est le pere de Deb.", "relation": "PERE_DE"},
        ],
        "cases": [
            {
                "case_id": "T01",
                "category": "positive",
                "expected_relation": "MERE_DE",
                "subject": "Eve",
                "object": "Fay",
                "text": "Eve est la mere de Fay.",
            },
            {
                "case_id": "T02",
                "category": "positive",
                "expected_relation": "PERE_DE",
                "subject": "Gus",
                "object": "Hal",
                "text": "Gus est le pere de Hal.",
            },
        ],
    }
    path = tmp_path / "tiny_corpus.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class _RecordingStrictClient:
    """Always answers correctly (via the caller-visible symbol_map) but
    records every `criteria` mapping it was asked to choose among, so a
    test can assert none of them is ever a real relation name (which
    would mean LABELED/GLOSSED leaked into what should be a STRICT-only
    ablation) and that the `state` text actually varies with the
    supplied demonstration order."""

    def __init__(self, symbol_map: Mapping[str, str], expected_by_text: Mapping[str, str]):
        self.symbol_map = symbol_map
        self.expected_by_text = expected_by_text
        self.seen_criteria_keys = []
        self.seen_states = []

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        self.seen_criteria_keys.append(tuple(sorted(criteria.keys())))
        self.seen_states.append(state)
        for text, expected_real in self.expected_by_text.items():
            if text in state:
                chosen = self.symbol_map[expected_real]
                others = [s for s in criteria if s != chosen]
                remainder = 0.0 if not others else 0.05
                dist = {chosen: 1.0 - remainder * len(others), **{o: remainder for o in others}}
                return chosen, dist[chosen], dist
        raise AssertionError(f"no known case text found in state: {state!r}")


def test_run_order_ablation_never_sends_a_real_relation_name_as_a_criteria_key(tiny_corpus):
    vocabulary = ["MERE_DE", "PERE_DE"]
    symbol_map = build_strict_symbol_map(vocabulary)
    expected_by_text = {"Eve est la mere de Fay.": "MERE_DE", "Gus est le pere de Hal.": "PERE_DE"}
    demonstrations = (
        __import__("m7_jev_relation_choice_v0_1").WorkedExample("Ana est la mere de Bob.", "MERE_DE"),
        __import__("m7_jev_relation_choice_v0_1").WorkedExample("Cid est le pere de Deb.", "PERE_DE"),
    )
    order = OrderedCondition(label="STRICT_test", demonstrations=demonstrations)
    client = _RecordingStrictClient(symbol_map, expected_by_text)

    (report,) = run_order_ablation(client, (order,), corpus_path=tiny_corpus)

    assert report.semantic_condition == "STRICT_test"
    assert report.overall_accuracy == 1.0
    for keys in client.seen_criteria_keys:
        assert set(keys) == set(symbol_map.values())
        assert not (set(keys) & set(vocabulary))  # never a real relation name


def test_run_order_ablation_reflects_the_supplied_demonstration_order_in_the_prompt(tiny_corpus):
    """Two orders built from the SAME two demonstrations, reversed --
    each order's `state` text must place the demonstrations in the
    order it was given, proving the order actually reaches the client
    rather than being silently re-sorted somewhere."""
    WorkedExample = __import__("m7_jev_relation_choice_v0_1").WorkedExample
    vocabulary = ["MERE_DE", "PERE_DE"]
    symbol_map = build_strict_symbol_map(vocabulary)
    expected_by_text = {"Eve est la mere de Fay.": "MERE_DE", "Gus est le pere de Hal.": "PERE_DE"}
    demo_a = WorkedExample("Ana est la mere de Bob.", "MERE_DE")
    demo_b = WorkedExample("Cid est le pere de Deb.", "PERE_DE")

    order_forward = OrderedCondition(label="forward", demonstrations=(demo_a, demo_b))
    order_reversed = OrderedCondition(label="reversed", demonstrations=(demo_b, demo_a))

    client_forward = _RecordingStrictClient(symbol_map, expected_by_text)
    run_order_ablation(client_forward, (order_forward,), corpus_path=tiny_corpus)
    client_reversed = _RecordingStrictClient(symbol_map, expected_by_text)
    run_order_ablation(client_reversed, (order_reversed,), corpus_path=tiny_corpus)

    first_state_forward = client_forward.seen_states[0]
    first_state_reversed = client_reversed.seen_states[0]
    assert first_state_forward.index("Ana") < first_state_forward.index("Cid")
    assert first_state_reversed.index("Cid") < first_state_reversed.index("Ana")


# ---------------------------------------------------------------------------
# 3. Aggregation math, hand-computed.
# ---------------------------------------------------------------------------


def _outcome(case_id: str, category: str, expected: str, predicted: str, vocabulary) -> CaseOutcome:
    dist = {r: (1.0 if r == predicted else 0.0) for r in vocabulary}
    proposal = JevProposal(
        subject="S",
        relation=predicted,
        object="O",
        positive_prob=dist[predicted],
        model="test",
        semantic_condition="STRICT",
        raw_response="{}",
        probabilities=dist,
    )
    return CaseOutcome(case_id=case_id, category=category, expected_relation=expected, proposal=proposal)


def test_summarize_order_ablation_matches_hand_computed_stats_and_rates():
    vocabulary = ("MERE_DE", "PERE_DE", "AUCUNE")

    report_1 = ConditionReport(
        semantic_condition="STRICT_seed1",
        vocabulary=vocabulary,
        outcomes=(
            _outcome("c1", "positive", "PERE_DE", "MERE_DE", vocabulary),  # wrong: PERE->MERE
            _outcome("c2", "positive", "MERE_DE", "MERE_DE", vocabulary),  # correct
            _outcome("c3", NEAR_SYNONYM_CATEGORY, "AUCUNE", "AUCUNE", vocabulary),  # correct
            _outcome("c4", "adversarial_x", "AUCUNE", "AUCUNE", vocabulary),  # correct
        ),
    )
    report_2 = ConditionReport(
        semantic_condition="STRICT_seed2",
        vocabulary=vocabulary,
        outcomes=(
            _outcome("c1", "positive", "PERE_DE", "PERE_DE", vocabulary),  # correct
            _outcome("c2", "positive", "MERE_DE", "PERE_DE", vocabulary),  # wrong: MERE->PERE
            _outcome("c3", NEAR_SYNONYM_CATEGORY, "AUCUNE", "MERE_DE", vocabulary),  # wrong
            _outcome("c4", "adversarial_x", "AUCUNE", "AUCUNE", vocabulary),  # correct
        ),
    )

    summary = summarize_order_ablation((report_1, report_2))

    assert summary.n_reports == 2
    assert summary.labels == ("STRICT_seed1", "STRICT_seed2")

    assert summary.overall_accuracy_values == (0.75, 0.5)
    stats = summary.overall_accuracy_stats
    assert stats["mean"] == pytest.approx(0.625)
    assert stats["min"] == 0.5
    assert stats["max"] == 0.75

    assert summary.positive_accuracy_values == (0.5, 0.5)
    assert summary.positive_accuracy_stats["stdev"] == pytest.approx(0.0)

    assert summary.adversarial_accuracy_values == (1.0, 0.5)

    pere_to_mere = summary.confusion_rate_stats("PERE_DE", "MERE_DE")
    assert pere_to_mere["mean"] == pytest.approx(0.5)
    assert pere_to_mere["min"] == 0.0
    assert pere_to_mere["max"] == 1.0

    mere_to_pere = summary.confusion_rate_stats("MERE_DE", "PERE_DE")
    assert mere_to_pere["mean"] == pytest.approx(0.5)

    assert summary.near_synonym_resistance_count == 1
    assert summary.near_synonym_resistance_rate == pytest.approx(0.5)

    payload = summary_to_dict(summary)
    json.dumps(payload)  # must not raise
    for pair in TRACKED_CONFUSION_PAIRS:
        assert f"{pair[0]}_to_{pair[1]}" in payload["confusion_rate_stats"]


def test_summarize_order_ablation_handles_a_missing_row_without_crashing():
    """A report where a tracked-pair's expected relation never appears
    (0 usable cases for that row) must report None for that pair's rate,
    not divide by zero."""
    vocabulary = ("MERE_DE", "PERE_DE", "AUCUNE")
    report = ConditionReport(
        semantic_condition="STRICT_seed1",
        vocabulary=vocabulary,
        outcomes=(_outcome("c1", "positive", "MERE_DE", "MERE_DE", vocabulary),),
    )
    summary = summarize_order_ablation((report,))
    assert summary.confusion_rate_stats("PERE_DE", "MERE_DE") is None
