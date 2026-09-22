"""MetaHIA M7 -- JEV/Kev multi-case benchmark v0.1 (P8).

Runs `corpus/jev_benchmark_cases_v0_1.json` (22 cases: 16 positive across
the four family relations, 6 adversarial -- negation, question,
conditional, out-of-vocabulary relation, near-synonym coercion risk,
no-claim-at-all) through `propose_relation_jev()` for all three semantic
conditions (STRICT/LABELED/GLOSSED, `SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md`
Sec. 3), against a real injected `JevDecideClient`.

NOT a re-run of the original 22-case Jev benchmark
(`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 2) -- that
benchmark's raw cases were never committed to this repo, confirmed absent
by direct search before writing this module, not assumed. This is a new
corpus of the same scale and adversarial-category design, so results are
comparable in shape, never claimed as a literal replication.

The relation vocabulary here is extended with a fifth option, `AUCUNE`
("none of the above applies"), absent from every other M7 mechanism in
this repo. Without it, `propose_relation_jev()`'s `choice` question would
force Kev to pick one of the four real relations even for a sentence that
expresses none of them (negation, a question, an out-of-vocabulary
relation, ...) -- exactly the coercion failure mode the original
benchmark's A04/A05 adversarial cases measured (`documentation/
P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 2: "travaille avec" scored
0.97 positive despite being out of vocabulary; "conjoint" was coerced
into EPOUX_DE at 0.98). `AUCUNE` is passed as an ordinary member of
`all_relations` -- no change to `propose_relation_jev()` itself was
needed.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple

from m7_jev_relation_choice_v0_1 import (
    RELATION_VOCABULARY_MODE_GLOSSED,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_STRICT,
    JevDecideClient,
    JevProposal,
    WorkedExample,
    propose_relation_jev,
)

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "jev_benchmark_cases_v0_1.json"

AUCUNE = "AUCUNE"

# Fixed across every STRICT-mode call in this benchmark. Every name here
# is disjoint from every subject/object in the corpus (verified by a
# dedicated test) -- the whole point of STRICT mode is that Kev never
# sees a real relation name, and reusing a test entity in a worked
# example would let the answer leak through entity identity instead of
# through the structural pattern the mode is meant to test.
WORKED_EXAMPLES: Tuple[WorkedExample, ...] = (
    WorkedExample("Zoe est la mère de Yanis.", "MERE_DE"),
    WorkedExample("Xavier est le père de Zoe.", "PERE_DE"),
    WorkedExample("Victor est l'époux de Wanda.", "EPOUX_DE"),
    WorkedExample("Wanda est l'épouse de Victor.", "EPOUSE_DE"),
    WorkedExample("Le ciel était nuageux ce jour-là.", AUCUNE),
)

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


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    category: str
    expected_relation: str
    subject: str
    object: str
    text: str


def load_corpus(path: Path = CORPUS_PATH) -> Tuple[Tuple[str, ...], Tuple[BenchmarkCase, ...]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    vocabulary = tuple(data["relation_vocabulary"])
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
    return vocabulary, cases


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    category: str
    expected_relation: str
    proposal: Optional[JevProposal]

    @property
    def correct(self) -> Optional[bool]:
        """None means Kev/the client gave no usable answer at all (a
        distinct, honestly-reported outcome from being wrong)."""
        if self.proposal is None:
            return None
        return self.proposal.relation == self.expected_relation


@dataclass(frozen=True)
class ConditionReport:
    semantic_condition: str
    outcomes: Tuple[CaseOutcome, ...]

    @property
    def no_answer_count(self) -> int:
        return sum(1 for o in self.outcomes if o.proposal is None)

    def _accuracy(self, category_prefix: Optional[str]) -> Optional[float]:
        relevant = [
            o
            for o in self.outcomes
            if o.proposal is not None
            and (category_prefix is None or o.category.startswith(category_prefix))
        ]
        if not relevant:
            return None
        return sum(1 for o in relevant if o.correct) / len(relevant)

    @property
    def overall_accuracy(self) -> Optional[float]:
        return self._accuracy(None)

    @property
    def positive_accuracy(self) -> Optional[float]:
        return self._accuracy("positive")

    @property
    def adversarial_accuracy(self) -> Optional[float]:
        return self._accuracy("adversarial")

    @property
    def mean_confidence(self) -> Optional[float]:
        confidences = [o.proposal.positive_prob for o in self.outcomes if o.proposal is not None]
        if not confidences:
            return None
        return statistics.fmean(confidences)


def run_benchmark(
    client: JevDecideClient,
    *,
    corpus_path: Path = CORPUS_PATH,
    conditions: Sequence[str] = ALL_CONDITIONS,
) -> Tuple[ConditionReport, ...]:
    """Runs every case in the corpus through `propose_relation_jev()` for
    each requested semantic condition, against the real injected client.
    Never pins an expected accuracy -- a real external model's answers are
    not deterministic across checkpoints/hardware, only the reporting
    machinery itself is (see `tests/test_m7_jev_benchmark_v0_1.py`, which
    exercises this same aggregation logic against a fake, fully
    deterministic client).
    """
    vocabulary, cases = load_corpus(corpus_path)
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
                worked_examples=WORKED_EXAMPLES if condition == RELATION_VOCABULARY_MODE_STRICT else (),
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
        reports.append(ConditionReport(semantic_condition=condition, outcomes=tuple(outcomes)))
    return tuple(reports)


def report_to_dict(report: ConditionReport) -> dict:
    """JSON-serializable summary, for saving real run results to disk --
    mirrors this project's established `scripts/print_*_comparison_v0_1.py`
    convention of a real, timestamped result artifact, not just console
    output."""
    return {
        "semantic_condition": report.semantic_condition,
        "n_cases": len(report.outcomes),
        "no_answer_count": report.no_answer_count,
        "overall_accuracy": report.overall_accuracy,
        "positive_accuracy": report.positive_accuracy,
        "adversarial_accuracy": report.adversarial_accuracy,
        "mean_confidence": report.mean_confidence,
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
    "WORKED_EXAMPLES",
    "BenchmarkCase",
    "CaseOutcome",
    "ConditionReport",
    "load_corpus",
    "run_benchmark",
    "report_to_dict",
]
