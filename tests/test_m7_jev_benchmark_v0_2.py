"""Permanent invariant tests for M7 -- JEV/Kev multi-case benchmark v0.2
(P8.1: STRICT enriched few-shot).

Uses an injected fake `JevDecideClient` throughout -- no network call.
Verifies the corpus (shape, demonstration/evaluation entity disjointness
-- checked programmatically, not just asserted in the corpus's own
docstring) and the new aggregation logic (confusion matrix, multiclass
Brier score, top-label ECE, the near-synonym-paraphrase regression check,
structural-paraphrase accuracy) deterministically, against hand-computed
expected values where practical, before any real network run is trusted.
The real run against the live Kev server is captured separately as a
saved result artifact, never pinned here.
"""
from __future__ import annotations

import re
from typing import Mapping, Optional

from m7_jev_benchmark_v0_2 import (
    ALL_CONDITIONS,
    AUCUNE,
    GLOSSES,
    NEAR_SYNONYM_CATEGORY,
    load_corpus,
    report_to_dict,
    run_benchmark,
)
from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_GLOSSED,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_STRICT,
)


def _dist(chosen: str, chosen_prob: float, options) -> dict:
    others = [o for o in options if o != chosen]
    remainder = (1.0 - chosen_prob) / len(others) if others else 0.0
    return {chosen: chosen_prob, **{o: remainder for o in others}}


class _ScriptedClient:
    """Returns whatever `answers_by_text` maps the matched case text to --
    a plain relation name (LABELED/GLOSSED) or an opaque symbol (STRICT,
    resolved by the caller via `symbol_map`). `answers_by_text` values are
    (predicted_relation, confidence) pairs; a missing text raises, so a
    test can never silently pass by feeding the wrong case."""

    def __init__(self, answers_by_text: Mapping[str, tuple], vocabulary, symbol_map: Optional[dict] = None):
        self.answers_by_text = answers_by_text
        self.vocabulary = vocabulary
        self.symbol_map = symbol_map  # None for LABELED/GLOSSED

    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]):
        for text, (predicted_real, confidence) in self.answers_by_text.items():
            if text in state:
                if self.symbol_map is not None:
                    chosen = self.symbol_map[predicted_real]
                else:
                    chosen = predicted_real
                return chosen, confidence, _dist(chosen, confidence, criteria.keys())
        raise AssertionError(f"no known case text found in state: {state!r}")


def _symbol_map(vocabulary):
    return {real: f"R{i + 1}" for i, real in enumerate(sorted(vocabulary))}


# ---------------------------------------------------------------------------
# 1. Corpus shape and the disjointness property, verified programmatically.
# ---------------------------------------------------------------------------


def test_corpus_has_the_expected_shape():
    vocabulary, demonstration_set, cases = load_corpus()
    assert set(vocabulary) == {"EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE", AUCUNE}
    assert len(demonstration_set) == 24
    assert len(cases) == 39
    positive = [c for c in cases if c.category == "positive"]
    adversarial = [c for c in cases if c.category.startswith("adversarial")]
    paraphrase = [c for c in cases if c.category == "positive_paraphrase"]
    assert len(positive) == 16
    assert len(adversarial) == 19
    assert len(paraphrase) == 4
    assert len(positive) + len(adversarial) + len(paraphrase) == len(cases)


def test_demonstration_set_covers_every_relation_including_aucune():
    vocabulary, demonstration_set, _ = load_corpus()
    covered = {ex.relation for ex in demonstration_set}
    assert covered == set(vocabulary)
    # 3 per positive relation, 2 per adversarial subtype (6 subtypes) = 12 AUCUNE
    aucune_count = sum(1 for ex in demonstration_set if ex.relation == AUCUNE)
    assert aucune_count == 12
    for real_relation in ("EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE"):
        assert sum(1 for ex in demonstration_set if ex.relation == real_relation) == 3


def test_demonstration_set_never_reuses_an_evaluation_entity():
    """The property the module docstring and corpus 'purpose' field both
    claim but do not themselves verify -- checked directly, the same
    discipline already applied to P4-T.2 v0.2's own non-reuse test."""
    _, demonstration_set, cases = load_corpus()
    eval_entities = set()
    for c in cases:
        eval_entities.add(c.subject)
        eval_entities.add(c.object)
    demo_entities = set()
    for ex in demonstration_set:
        # crude but sufficient tokenizer: capitalized words are names in
        # this corpus's own French sentences (never a capitalized common
        # noun in any of these hand-authored sentences).
        for word in re.findall(r"[A-ZÀ-Ý][a-zà-ÿ]+", ex.text):
            demo_entities.add(word)
    overlap = eval_entities & demo_entities
    assert not overlap, overlap


def test_near_synonym_category_holds_subject_object_constant_across_paraphrases():
    """The experimental control the review asked for: within one
    adversarial category, only the phrasing should vary, never the
    entities -- otherwise a coercion failure or success can't be
    attributed to the phrasing itself."""
    _, _, cases = load_corpus()
    near_synonym_cases = [c for c in cases if c.category == NEAR_SYNONYM_CATEGORY]
    assert len(near_synonym_cases) == 4
    assert len({(c.subject, c.object) for c in near_synonym_cases}) == 1


def test_positive_paraphrase_cases_use_a_structure_absent_from_every_demonstration():
    """H1 vs H2: every demonstration is 'X est la RELATION de Y' or an
    AUCUNE variant -- none is 'La RELATION de Y s'appelle X', the
    structure the positive_paraphrase cases use."""
    _, demonstration_set, cases = load_corpus()
    paraphrase_cases = [c for c in cases if c.category == "positive_paraphrase"]
    assert len(paraphrase_cases) == 4
    for c in paraphrase_cases:
        assert "s'appelle" in c.text
    assert not any("s'appelle" in ex.text for ex in demonstration_set)


# ---------------------------------------------------------------------------
# 2. Aggregation logic, hand-computed expected values.
# ---------------------------------------------------------------------------


def test_confusion_matrix_counts_a_deliberate_misclassification():
    """Scripts a client that gets exactly ONE case wrong, in a known way
    (MERE_DE case predicted as PERE_DE), and checks the confusion matrix
    entry directly -- not just overall accuracy, which would not
    distinguish this from any other kind of error."""
    vocabulary, _, cases = load_corpus()
    answers = {c.text: (c.expected_relation, 0.8) for c in cases}
    # Force exactly one MERE_DE positive case to be misclassified as PERE_DE.
    mere_case = next(c for c in cases if c.expected_relation == "MERE_DE" and c.category == "positive")
    answers[mere_case.text] = ("PERE_DE", 0.6)

    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.confusion_matrix["MERE_DE"]["PERE_DE"] == 1
    # The confusion matrix is corpus-wide, not category-filtered: 4
    # "positive" MERE_DE cases (1 misrouted, 3 correct) + 1
    # "positive_paraphrase" MERE_DE case (P01, untouched, correct) = 4.
    assert report.confusion_matrix["MERE_DE"]["MERE_DE"] == 4


def test_near_synonym_all_paraphrases_correct_is_false_on_a_single_coercion():
    """Mirrors the real GLOSSED failure already measured on v0.1: 3 of 4
    near-synonym paraphrases correctly AUCUNE, 1 coerced -- must report
    False, not "mostly true"."""
    vocabulary, _, cases = load_corpus()
    answers = {c.text: (c.expected_relation, 0.7) for c in cases}
    near_synonym_cases = [c for c in cases if c.category == NEAR_SYNONYM_CATEGORY]
    coerced_case = near_synonym_cases[0]
    answers[coerced_case.text] = ("EPOUX_DE", 0.9)  # exactly the measured A05 failure mode

    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.near_synonym_all_paraphrases_correct is False


def test_near_synonym_all_paraphrases_correct_is_true_when_every_paraphrase_resists_coercion():
    vocabulary, _, cases = load_corpus()
    answers = {c.text: (c.expected_relation, 0.7) for c in cases}
    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.near_synonym_all_paraphrases_correct is True


def test_structural_paraphrase_accuracy_is_isolated_from_ordinary_positive_accuracy():
    """H1 vs H2: a client that gets every ordinary positive case right
    but every structural-paraphrase case wrong must show full positive
    accuracy alongside zero paraphrase accuracy -- the two must never be
    conflated into one number."""
    vocabulary, _, cases = load_corpus()
    answers = {}
    for c in cases:
        if c.category == "positive_paraphrase":
            # deliberately wrong: always answer with a different relation
            wrong = next(r for r in ("EPOUX_DE", "EPOUSE_DE", "MERE_DE", "PERE_DE") if r != c.expected_relation)
            answers[c.text] = (wrong, 0.5)
        else:
            answers[c.text] = (c.expected_relation, 0.8)

    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.positive_accuracy == 1.0
    assert report.structural_paraphrase_accuracy == 0.0


def test_brier_score_is_zero_for_a_perfectly_confident_correct_client():
    vocabulary, _, cases = load_corpus()
    answers = {c.text: (c.expected_relation, 1.0) for c in cases}
    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.brier_score_multiclass == 0.0


def test_brier_score_is_positive_for_a_confidently_wrong_client():
    vocabulary, _, cases = load_corpus()
    wrong_relation = "PERE_DE"
    answers = {
        c.text: (wrong_relation if c.expected_relation != wrong_relation else "MERE_DE", 0.95) for c in cases
    }
    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert report.brier_score_multiclass > 0.5


def test_ece_is_near_zero_when_confidence_matches_accuracy_for_a_mixed_client():
    """A client correct exactly 70% of the time, always reporting 0.7
    confidence, should have ECE close to 0 -- confidence matches observed
    accuracy by construction."""
    vocabulary, _, cases = load_corpus()
    answers = {}
    for i, c in enumerate(cases):
        # deterministic 70/30 split by case index
        correct = (i % 10) < 7
        predicted = c.expected_relation if correct else next(
            r for r in vocabulary if r != c.expected_relation
        )
        answers[c.text] = (predicted, 0.7)
    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    ece = report.expected_calibration_error_top_label()
    assert ece is not None
    assert ece < 0.15


def test_strict_mode_uses_the_demonstration_set_labeled_and_glossed_do_not():
    vocabulary, demonstration_set, cases = load_corpus()
    symbol_map = _symbol_map(vocabulary)
    answers = {c.text: (c.expected_relation, 0.7) for c in cases}

    strict_client = _ScriptedClient(answers, vocabulary, symbol_map=symbol_map)
    (strict_report,) = run_benchmark(strict_client, conditions=(RELATION_VOCABULARY_MODE_STRICT,))
    assert strict_report.overall_accuracy == 1.0

    labeled_client = _ScriptedClient(answers, vocabulary)
    (labeled_report,) = run_benchmark(labeled_client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    assert labeled_report.overall_accuracy == 1.0


def test_report_to_dict_includes_the_new_p8_1_fields():
    import json

    vocabulary, _, cases = load_corpus()
    answers = {c.text: (c.expected_relation, 0.8) for c in cases}
    client = _ScriptedClient(answers, vocabulary)
    (report,) = run_benchmark(client, conditions=(RELATION_VOCABULARY_MODE_LABELED,))
    payload = report_to_dict(report)
    json.dumps(payload)  # must not raise
    for field in (
        "structural_paraphrase_accuracy",
        "near_synonym_all_paraphrases_correct",
        "brier_score_multiclass",
        "expected_calibration_error_top_label",
        "confusion_matrix",
    ):
        assert field in payload


def test_glosses_cover_every_relation_including_aucune():
    vocabulary, _, _ = load_corpus()
    assert set(GLOSSES.keys()) == set(vocabulary)
