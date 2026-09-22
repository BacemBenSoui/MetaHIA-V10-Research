"""MetaHIA M7 -- JEV/Kev multi-case benchmark v0.2 (P8.1: STRICT enriched few-shot).

Follow-up to `m7_jev_benchmark_v0_1.py`'s real result
(`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 6ter), done
by explicit request: STRICT failed on nearly every nuanced adversarial
case with only 5 worked examples (1 per outcome class); this module
tests whether that was a few-shot deficit (Case A: enriching examples
fixes it) or a real limit of the mechanism (Case B: positive accuracy
improves but adversarial stays weak) or neither (Case C: no change) --
the three-way framework the review itself proposed.

Three concrete changes over v0.1, none touching
`m7_jev_relation_choice_v0_1.py`'s own logic:

1. A real, separate `demonstration_set` (24 entries: 3 per positive
   relation + 2 per adversarial subtype, `corpus/jev_benchmark_cases_v0_2.json`)
   replaces v0.1's 5 minimal `WORKED_EXAMPLES` -- every entity in it is
   verified disjoint from every evaluation-case entity by a dedicated
   test, not just by inspection.
2. Adversarial cases expand from 6 (1 per category) to 19 (3-4 paraphrases
   per category, same subject/object held constant per category so
   phrasing is the only varying factor) -- directly answers the review's
   request for a permanent "does 'conjoint' stay AUCUNE under paraphrase"
   regression check (`near_synonym_all_paraphrases_correct` below).
3. A new `positive_paraphrase` category (4 cases) tests genuine
   structural generalization: every demonstration uses "X est la
   RELATION de Y"; these evaluation cases use a different syntactic
   structure ("La RELATION de Y s'appelle X") never shown in any
   demonstration -- distinguishes H1 (memorized surface pattern) from H2
   (genuine relation abstraction), exactly the H1/H2 split the review
   asked for.

Also adds, requested explicitly: a real confusion matrix (which wrong
relation an error actually produces, not just "wrong") and real
multiclass calibration (Brier score + top-label ECE) computed from the
FULL probability distribution now captured by
`m7_jev_relation_choice_v0_1.JevProposal.probabilities` (P8.1's other
change to that module). Both formulas mirror
`m6_structural_learning_v0_1.py`'s own `brier_score_multiclass()` /
`expected_calibration_error_top_label()` exactly (same math, standalone
reimplementation here since that module's own functions are tightly
coupled to `StructuralLearningPolicy`/`StructuralOutcomeRecord`, the
wrong data model for a JEV proposal -- forcing that reuse would be
exactly the kind of forced comparison this project already refuses
elsewhere, e.g. P4-T.6's own refusal to fabricate a fake `PathRecord`).
LogLoss is explicitly NOT computed here -- not used anywhere else in
this project, and Brier + ECE alone already answer the calibration
question this benchmark needs; deferred, not silently dropped.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_GLOSSED,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_STRICT,
    JevDecideClient,
    JevProposal,
    WorkedExample,
    propose_relation_jev,
)

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "jev_benchmark_cases_v0_2.json"

AUCUNE = "AUCUNE"

GLOSSES: Mapping[str, str] = {
    "EPOUX_DE": "X est l'époux (le mari) de Y",
    "EPOUSE_DE": "X est l'épouse (la femme) de Y",
    "MERE_DE": "X est la mère de Y",
    "PERE_DE": "X est le père de Y",
    AUCUNE: "Aucune des relations familiales ci-dessus n'est affirmée par la phrase",
}

ALL_CONDITIONS = (
    RELATION_VOCABULARY_MODE_STRICT,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_GLOSSED,
)

NEAR_SYNONYM_CATEGORY = "adversarial_near_synonym_coercion_risk"


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    category: str
    expected_relation: str
    subject: str
    object: str
    text: str


def load_corpus(path: Path = CORPUS_PATH) -> Tuple[Tuple[str, ...], Tuple[WorkedExample, ...], Tuple[BenchmarkCase, ...]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    vocabulary = tuple(data["relation_vocabulary"])
    demonstration_set = tuple(WorkedExample(d["text"], d["relation"]) for d in data["demonstration_set"])
    cases = tuple(
        BenchmarkCase(
            case_id=c["case_id"],
            category=c["category"],
            expected_relation=c["expected_relation"],
            subject=c["subject"],
            object=c["object"],
            text=c["text"],
        )
        for c in data["cases"]
    )
    return vocabulary, demonstration_set, cases


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    category: str
    expected_relation: str
    proposal: Optional[JevProposal]

    @property
    def correct(self) -> Optional[bool]:
        if self.proposal is None:
            return None
        return self.proposal.relation == self.expected_relation


@dataclass(frozen=True)
class ConditionReport:
    semantic_condition: str
    vocabulary: Tuple[str, ...]
    outcomes: Tuple[CaseOutcome, ...]

    @property
    def no_answer_count(self) -> int:
        return sum(1 for o in self.outcomes if o.proposal is None)

    def _accuracy_where(self, predicate) -> Optional[float]:
        """`predicate(category: str) -> bool` selects which cases count --
        always an exact category-membership test, never a prefix match:
        `"positive_paraphrase".startswith("positive")` is True, which
        silently pooled paraphrase cases into ordinary positive accuracy
        the first time this was written (found and fixed by
        tests/test_m7_jev_benchmark_v0_2.py before any real network run
        was trusted)."""
        relevant = [o for o in self.outcomes if o.proposal is not None and predicate(o.category)]
        if not relevant:
            return None
        return sum(1 for o in relevant if o.correct) / len(relevant)

    @property
    def overall_accuracy(self) -> Optional[float]:
        return self._accuracy_where(lambda c: True)

    @property
    def positive_accuracy(self) -> Optional[float]:
        return self._accuracy_where(lambda c: c == "positive")

    @property
    def adversarial_accuracy(self) -> Optional[float]:
        return self._accuracy_where(lambda c: c.startswith("adversarial"))

    @property
    def structural_paraphrase_accuracy(self) -> Optional[float]:
        """H1 vs H2: accuracy on cases whose phrasing was never shown in
        any demonstration. High accuracy here is evidence for H2 (genuine
        relation abstraction); accuracy collapsing relative to the
        ordinary positive cases is evidence the model relies on surface
        pattern matching (H1)."""
        return self._accuracy_where(lambda c: c == "positive_paraphrase")

    @property
    def near_synonym_all_paraphrases_correct(self) -> bool:
        """The permanent regression check requested explicitly: does
        "conjoint" (and its paraphrases) stay AUCUNE across every
        formulation tested, in THIS condition? False means at least one
        paraphrase was coerced into a real relation -- exactly the A05
        failure mode already measured on official Jev and on v0.1's
        GLOSSED condition."""
        relevant = [o for o in self.outcomes if o.category == NEAR_SYNONYM_CATEGORY]
        return bool(relevant) and all(o.correct is True for o in relevant)

    @property
    def mean_confidence(self) -> Optional[float]:
        confidences = [o.proposal.positive_prob for o in self.outcomes if o.proposal is not None]
        if not confidences:
            return None
        return statistics.fmean(confidences)

    @property
    def confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        """confusion[expected][predicted] = count. Only over cases with a
        usable answer -- a `None` proposal is already reported separately
        via `no_answer_count`, never silently folded into "wrong"."""
        matrix: Dict[str, Dict[str, int]] = {r: {r2: 0 for r2 in self.vocabulary} for r in self.vocabulary}
        for o in self.outcomes:
            if o.proposal is None:
                continue
            matrix[o.expected_relation][o.proposal.relation] = matrix[o.expected_relation].get(
                o.proposal.relation, 0
            ) + 1
        return matrix

    @property
    def brier_score_multiclass(self) -> Optional[float]:
        """Mean squared error between the predicted distribution and the
        one-hot true outcome -- same formula as
        m6_structural_learning_v0_1.brier_score_multiclass(), standalone
        reimplementation here since that function is coupled to a
        different data model (StructuralLearningPolicy). 0 is perfect;
        never rewards overconfidence (a proper scoring rule)."""
        usable = [o for o in self.outcomes if o.proposal is not None]
        if not usable:
            return None
        total = 0.0
        for o in usable:
            dist = o.proposal.probabilities
            total += sum((dist.get(r, 0.0) - (1.0 if r == o.expected_relation else 0.0)) ** 2 for r in self.vocabulary)
        return total / len(usable)

    def expected_calibration_error_top_label(self, *, n_bins: int = 10) -> Optional[float]:
        """Standard top-label multi-class ECE -- same formula as
        m6_structural_learning_v0_1.expected_calibration_error_top_label(),
        standalone reimplementation for the same reason as
        `brier_score_multiclass` above."""
        usable = [o for o in self.outcomes if o.proposal is not None]
        if not usable:
            return None
        bins: list = [[] for _ in range(n_bins)]
        for o in usable:
            dist = o.proposal.probabilities
            top_class = max(dist, key=dist.get)
            confidence = dist[top_class]
            correct = top_class == o.expected_relation
            idx = min(int(confidence * n_bins), n_bins - 1)
            bins[idx].append((confidence, correct))
        total_error = 0.0
        for bucket in bins:
            if not bucket:
                continue
            mean_conf = statistics.fmean(c for c, _ in bucket)
            accuracy = sum(1 for _, correct in bucket if correct) / len(bucket)
            total_error += (len(bucket) / len(usable)) * abs(mean_conf - accuracy)
        return total_error


def run_benchmark(
    client: JevDecideClient,
    *,
    corpus_path: Path = CORPUS_PATH,
    conditions: Sequence[str] = ALL_CONDITIONS,
) -> Tuple[ConditionReport, ...]:
    """Runs every case in the corpus through `propose_relation_jev()` for
    each requested semantic condition. Never pins an expected accuracy --
    see `tests/test_m7_jev_benchmark_v0_2.py` for the deterministic
    aggregation/scoring tests against a fake client.
    """
    vocabulary, demonstration_set, cases = load_corpus(corpus_path)
    reports = []
    for condition in conditions:
        outcomes = []
        for case in cases:
            proposal = propose_relation_jev(
                text=case.text,
                subject=case.subject,
                obj=case.object,
                all_relations=vocabulary,
                semantic_condition=condition,
                client=client,
                worked_examples=demonstration_set if condition == RELATION_VOCABULARY_MODE_STRICT else (),
                glosses=GLOSSES if condition == RELATION_VOCABULARY_MODE_GLOSSED else {},
            )
            outcomes.append(
                CaseOutcome(
                    case_id=case.case_id,
                    category=case.category,
                    expected_relation=case.expected_relation,
                    proposal=proposal,
                )
            )
        reports.append(ConditionReport(semantic_condition=condition, vocabulary=vocabulary, outcomes=tuple(outcomes)))
    return tuple(reports)


def report_to_dict(report: ConditionReport) -> dict:
    return {
        "semantic_condition": report.semantic_condition,
        "n_cases": len(report.outcomes),
        "no_answer_count": report.no_answer_count,
        "overall_accuracy": report.overall_accuracy,
        "positive_accuracy": report.positive_accuracy,
        "adversarial_accuracy": report.adversarial_accuracy,
        "structural_paraphrase_accuracy": report.structural_paraphrase_accuracy,
        "near_synonym_all_paraphrases_correct": report.near_synonym_all_paraphrases_correct,
        "mean_confidence": report.mean_confidence,
        "brier_score_multiclass": report.brier_score_multiclass,
        "expected_calibration_error_top_label": report.expected_calibration_error_top_label(),
        "confusion_matrix": report.confusion_matrix,
        "cases": [
            {
                "case_id": o.case_id,
                "category": o.category,
                "expected_relation": o.expected_relation,
                "predicted_relation": o.proposal.relation if o.proposal else None,
                "positive_prob": o.proposal.positive_prob if o.proposal else None,
                "correct": o.correct,
            }
            for o in report.outcomes
        ],
    }


__all__ = [
    "AUCUNE",
    "ALL_CONDITIONS",
    "CORPUS_PATH",
    "GLOSSES",
    "NEAR_SYNONYM_CATEGORY",
    "BenchmarkCase",
    "CaseOutcome",
    "ConditionReport",
    "load_corpus",
    "run_benchmark",
    "report_to_dict",
]
