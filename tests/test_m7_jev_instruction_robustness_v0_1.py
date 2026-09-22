"""Permanent invariant tests for M7 -- JEV/Kev P8.3b LABELED
`instructions`-wording robustness (`m7_jev_instruction_robustness_v0_1.py`).

Uses an injected fake `JevDecideClient` -- no network call. Same
discipline as P8.2/P8.3a: verify the variant set is genuinely distinct
from the original wording, verify each variant actually reaches the
client (and criteria order stays fixed/unconfounded), verify the
generic `summarize_order_ablation`/`summary_to_dict` reuse still works
on these reports -- before any real network run is trusted.
"""
from __future__ import annotations

import json
from typing import Mapping, Optional

import pytest

from m7_jev_benchmark_v0_2 import load_corpus
from m7_jev_instruction_robustness_v0_1 import INSTRUCTION_VARIANTS, run_instruction_robustness
from m7_jev_order_ablation_v0_1 import summarize_order_ablation, summary_to_dict
from m7_jev_relation_choice_v0_1 import DEFAULT_LABELED_GLOSSED_INSTRUCTIONS


def test_instruction_variants_are_genuinely_distinct_from_each_other_and_the_original():
    assert len(INSTRUCTION_VARIANTS) == 5
    texts = list(INSTRUCTION_VARIANTS.values())
    assert len(set(texts)) == 5  # no accidental duplicate wording
    assert DEFAULT_LABELED_GLOSSED_INSTRUCTIONS not in texts
    assert len(set(INSTRUCTION_VARIANTS.keys())) == 5  # unique labels


class _RecordingLabeledClient:
    """Always answers correctly by matching case text, and records the
    exact `instructions` string and `criteria` key order for every
    call -- proves each variant's wording reaches the wire and that
    criteria order stays fixed (unconfounded with P8.3a's axis)."""

    def __init__(self, expected_by_text: Mapping[str, str]):
        self.expected_by_text = expected_by_text
        self.seen_instructions = []
        self.seen_criteria_orders = []

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        self.seen_instructions.append(instructions)
        self.seen_criteria_orders.append(tuple(criteria.keys()))
        for text, expected in self.expected_by_text.items():
            if text in state:
                others = [r for r in criteria if r != expected]
                remainder = 0.0 if not others else 0.1
                dist = {expected: 1.0 - remainder * len(others), **{o: remainder for o in others}}
                return expected, dist[expected], dist
        raise AssertionError(f"no known case text found in state: {state!r}")


def test_run_instruction_robustness_sends_each_variants_exact_wording():
    _, _, cases = load_corpus()
    expected_by_text = {c.text: c.expected_relation for c in cases}
    client = _RecordingLabeledClient(expected_by_text)

    reports = run_instruction_robustness(client)

    assert len(reports) == 5
    assert {r.semantic_condition for r in reports} == {f"LABELED_instructions_{k}" for k in INSTRUCTION_VARIANTS}
    for r in reports:
        assert r.overall_accuracy == 1.0

    # Every call within one report's run used that report's exact wording.
    n_cases = len(cases)
    for i, (label, text) in enumerate(INSTRUCTION_VARIANTS.items()):
        call_slice = client.seen_instructions[i * n_cases : (i + 1) * n_cases]
        assert all(seen == text for seen in call_slice)


def test_run_instruction_robustness_keeps_criteria_order_fixed_across_variants():
    """The axis this module varies is wording alone -- criteria order
    must be identical (the corpus's own vocabulary order) for every
    variant, never confounded with P8.3a's own axis."""
    vocabulary, _, cases = load_corpus()
    expected_by_text = {c.text: c.expected_relation for c in cases}
    client = _RecordingLabeledClient(expected_by_text)

    run_instruction_robustness(client)

    assert all(order == tuple(vocabulary) for order in client.seen_criteria_orders)


def test_summarize_order_ablation_reused_unmodified_on_instruction_variant_reports():
    _, _, cases = load_corpus()
    expected_by_text = {c.text: c.expected_relation for c in cases}
    client = _RecordingLabeledClient(expected_by_text)
    reports = run_instruction_robustness(client)

    summary = summarize_order_ablation(reports)
    assert summary.n_reports == 5
    assert summary.overall_accuracy_stats["mean"] == pytest.approx(1.0)

    payload = summary_to_dict(summary)
    json.dumps(payload)  # must not raise
