"""Permanent invariant tests for M7 -- JEV/Kev multi-case benchmark v0.1.

Uses an injected fake `JevDecideClient` throughout -- no network call.
Verifies the corpus itself (shape, entity disjointness from
WORKED_EXAMPLES) and the aggregation/scoring logic (accuracy, mean
confidence, honest "no answer" accounting) deterministically, before any
real network run is trusted. The real run against the live Kev server is
captured separately as a saved result artifact
(`validation/jev_benchmark_v0_1_results_2026-09-22.json`), never pinned
here as an expected value -- a real external model's answers are not
deterministic across checkpoints/hardware.
"""
from __future__ import annotations

from typing import Mapping, Optional, Tuple

from m7_jev_benchmark_v0_1 import (
    ALL_CONDITIONS,
    AUCUNE,
    GLOSSES,
    WORKED_EXAMPLES,
    load_corpus,
    report_to_dict,
    run_benchmark,
)
from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_GLOSSED,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_STRICT,
)


class _AlwaysCorrectClient:
    """For LABELED/GLOSSED only (criteria keys are real relation names) --
    takes an expected-relation lookup keyed by case text, built from the
    corpus itself in the tests below, never from the module under test."""

    def __init__(self, expected_by_text: Mapping[str, str], answer_prob: float = 0.9):
        self.expected_by_text = expected_by_text
        self.answer_prob = answer_prob
        self.calls = []

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        self.calls.append({"state": state, "instructions": instructions, "criteria": dict(criteria)})
        for text, expected_real in self.expected_by_text.items():
            if text in state:
                return expected_real, self.answer_prob
        raise AssertionError(f"no known case text found in state: {state!r}")


class _AlwaysCorrectStrictClient:
    """STRICT-aware version: resolves the correct opaque symbol by
    matching criteria's keys against the worked-examples-derived mapping
    implied by build_strict_symbol_map (alphabetical order of the real
    vocabulary) -- reconstructed independently here, not imported from
    the module under test, so this is a genuine cross-check."""

    def __init__(self, expected_by_text: Mapping[str, str], vocabulary, answer_prob: float = 0.7):
        self.expected_by_text = expected_by_text
        self.symbol_map = {real: f"R{i + 1}" for i, real in enumerate(sorted(vocabulary))}
        self.answer_prob = answer_prob
        self.calls = []

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        self.calls.append({"state": state, "instructions": instructions, "criteria": dict(criteria)})
        for text, expected_real in self.expected_by_text.items():
            if text in state:
                return self.symbol_map[expected_real], self.answer_prob
        raise AssertionError(f"no known case text found in state: {state!r}")


class _AlwaysNoAnswerClient:
    def decide(self, *, state, instructions, criteria):
        return None


def test_corpus_has_the_expected_shape():
    vocabulary, cases = load_corpus()
    assert set(vocabulary) == {"EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE", AUCUNE}
    assert len(cases) == 22
    positive = [c for c in cases if c.category == "positive"]
    adversarial = [c for c in cases if c.category != "positive"]
    assert len(positive) == 16
    assert len(adversarial) == 6
    assert all(c.expected_relation == AUCUNE for c in adversarial)
    assert {c.expected_relation for c in positive} == {"EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE"}


def test_worked_examples_never_reuse_a_corpus_entity():
    """The property the module docstring claims but does not itself
    verify -- checked here directly, the same discipline already applied
    to P4-T.2 v0.2's own non-reuse regression test."""
    _, cases = load_corpus()
    corpus_entities = set()
    for c in cases:
        corpus_entities.add(c.subject)
        corpus_entities.add(c.object)
    worked_example_entities = set()
    for ex in WORKED_EXAMPLES:
        for word in ex.text.replace(".", "").replace("'", " ").split():
            worked_example_entities.add(word)
    overlap = corpus_entities & worked_example_entities
    assert not overlap, overlap


def test_glosses_cover_every_relation_including_aucune():
    vocabulary, _ = load_corpus()
    assert set(GLOSSES.keys()) == set(vocabulary)


def test_worked_examples_cover_every_relation_including_aucune():
    vocabulary, _ = load_corpus()
    covered = {ex.relation for ex in WORKED_EXAMPLES}
    assert covered == set(vocabulary)


def _expected_by_text():
    _, cases = load_corpus()
    return {c.text: c.expected_relation for c in cases}


def test_run_benchmark_scores_a_perfectly_correct_client_at_full_accuracy():
    vocabulary, _ = load_corpus()
    expected = _expected_by_text()
    reports = {}
    for condition in ALL_CONDITIONS:
        client = (
            _AlwaysCorrectStrictClient(expected, vocabulary)
            if condition == RELATION_VOCABULARY_MODE_STRICT
            else _AlwaysCorrectClient(expected)
        )
        (report,) = run_benchmark(client, conditions=(condition,))
        reports[condition] = report

    for condition, report in reports.items():
        assert report.overall_accuracy == 1.0, condition
        assert report.positive_accuracy == 1.0, condition
        assert report.adversarial_accuracy == 1.0, condition
        assert report.no_answer_count == 0, condition


def test_run_benchmark_scores_a_client_that_never_gives_a_usable_answer():
    (report,) = run_benchmark(_AlwaysNoAnswerClient(), conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.no_answer_count == 22
    assert report.overall_accuracy is None
    assert report.mean_confidence is None


def test_strict_mode_passes_worked_examples_labeled_and_glossed_do_not():
    vocabulary, _ = load_corpus()
    expected = _expected_by_text()

    strict_client = _AlwaysCorrectStrictClient(expected, vocabulary)
    run_benchmark(strict_client, conditions=(RELATION_VOCABULARY_MODE_STRICT,))
    assert all("Examples:" in call["state"] for call in strict_client.calls)

    labeled_client = _AlwaysCorrectClient(expected)
    run_benchmark(labeled_client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert all("Examples:" not in call["state"] for call in labeled_client.calls)
    assert all(all(v is None for v in call["criteria"].values()) for call in labeled_client.calls)

    glossed_client = _AlwaysCorrectClient(expected)
    run_benchmark(glossed_client, conditions=(RELATION_VOCABULARY_MODE_GLOSSED,))
    assert all(
        all(v is not None for v in call["criteria"].values()) for call in glossed_client.calls
    )


def test_report_to_dict_is_json_serializable_and_shaped_correctly():
    import json

    vocabulary, _ = load_corpus()
    expected = _expected_by_text()
    client = _AlwaysCorrectClient(expected)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    payload = report_to_dict(report)
    json.dumps(payload)  # must not raise
    assert payload["n_cases"] == 22
    assert len(payload["cases"]) == 22
    assert payload["overall_accuracy"] == 1.0
