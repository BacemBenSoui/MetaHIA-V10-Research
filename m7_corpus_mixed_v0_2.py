"""MetaHIA M7 -- mixed-corpus promotion integration v0.2.

Extends v0.1 (`m7_corpus_mixed_v0_1.py`, frozen -- its hash is pinned in
`MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md`, not touched here) to a
THIRD independent evidence source: the free-text claim parser
(`m7_corpus_from_text_claims_v0_1.py`). Chosen explicitly over the two other
candidate next steps (improving parsing fidelity, extending either LLM
mechanism to length>1 patterns) because its real result (2026-09-18) showed
genuine outcome diversity -- 5 `SUPPORTED`, 2 `CONTRADICTED` out of 7 records
-- unlike the closed-question witness's degenerate all-`CONTRADICTED`
result, making it the single most promising untested evidence source for
this pipeline.

Four conditions are compared under the SAME split parameters, to isolate the
individual and joint effect of each LLM source on top of the
already-validated adversarial baseline:

    baseline            = adversarial only (m6_corpus_from_m4_m5_v0_2.py)
    + witness           = adversarial + closed-question LLM witness
                          (m7_corpus_from_llm_v0_1.py -- this is exactly
                          v0.1's comparison, reproduced here for a uniform
                          four-way table, not re-validated)
    + text claims       = adversarial + free-text claim parser (NEW)
    + witness + text    = all three sources combined

Fairness (same property v0.1 already established and this module reuses
unchanged): neither LLM mechanism can ever add a rule signature absent from
the adversarial corpus -- both only ever ask about patterns already
discovered from the same corpus file. `split_by_rule` therefore assigns the
IDENTICAL holdout rule set under a fixed seed in all four conditions --
verified in tests/test_m7_mixed_corpus_v0_2_promotion_v0_1.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_structural_learning_v0_1 import (
    PromotionDecision,
    StructuralLearningPolicy,
    StructuralOutcomeRecord,
    brier_score_multiclass,
    evaluate_promotion,
    expected_calibration_error_top_label,
    split_by_rule,
)
from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus
from m7_corpus_from_text_claims_v0_1 import build_text_claim_corpus
from m7_llm_fact_proposer_v0_1 import GenerateFn


@dataclass(frozen=True)
class MixedCorpusReportV2:
    adversarial_records: Tuple[StructuralOutcomeRecord, ...]
    llm_records: Tuple[StructuralOutcomeRecord, ...]
    text_claim_records: Tuple[StructuralOutcomeRecord, ...]

    @property
    def combined_with_witness(self) -> Tuple[StructuralOutcomeRecord, ...]:
        return self.adversarial_records + self.llm_records

    @property
    def combined_with_text_claims(self) -> Tuple[StructuralOutcomeRecord, ...]:
        return self.adversarial_records + self.text_claim_records

    @property
    def combined_all(self) -> Tuple[StructuralOutcomeRecord, ...]:
        return self.adversarial_records + self.llm_records + self.text_claim_records


def build_mixed_corpus_v2(
    *,
    llm_generate_fn: Optional[GenerateFn] = None,
    text_generate_fn: Optional[GenerateFn] = None,
    model: str = "llama3.2:latest",
) -> MixedCorpusReportV2:
    adversarial_report = build_real_corpus_v2()
    llm_report = build_llm_witnessed_corpus(generate_fn=llm_generate_fn, model=model)
    text_report = build_text_claim_corpus(generate_fn=text_generate_fn, model=model)
    return MixedCorpusReportV2(
        adversarial_records=adversarial_report.records,
        llm_records=llm_report.records,
        text_claim_records=text_report.records,
    )


@dataclass(frozen=True)
class ConditionResult:
    label: str
    train_size: int
    holdout_size: int
    holdout_brier: float
    holdout_ece: float
    promotion: PromotionDecision


@dataclass(frozen=True)
class CalibrationComparisonV2:
    baseline: ConditionResult
    with_witness: ConditionResult
    with_text_claims: ConditionResult
    with_both: ConditionResult


def _evaluate_condition(
    label: str,
    records: Tuple[StructuralOutcomeRecord, ...],
    *,
    val_fraction: float,
    holdout_fraction: float,
    seed: int,
    brier_threshold: float,
    ece_bins: int,
) -> ConditionResult:
    train, _val, holdout = split_by_rule(records, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed)
    policy = StructuralLearningPolicy().fit(train)
    brier = brier_score_multiclass(policy, holdout) if holdout else float("nan")
    ece = expected_calibration_error_top_label(policy, holdout, n_bins=ece_bins) if holdout else float("nan")
    decision = evaluate_promotion(policy, None, holdout, brier_threshold=brier_threshold)
    return ConditionResult(
        label=label, train_size=len(train), holdout_size=len(holdout),
        holdout_brier=brier, holdout_ece=ece, promotion=decision,
    )


def compare_calibration_across_sources(
    report: MixedCorpusReportV2,
    *,
    val_fraction: float = 0.2,
    holdout_fraction: float = 0.2,
    seed: int = 0,
    brier_threshold: float = 0.5,
    ece_bins: int = 5,
) -> CalibrationComparisonV2:
    """Evaluates all four conditions with the SAME split parameters -- real
    computations through the unchanged M6 machinery, no new metric, no new
    threshold logic."""
    kwargs = dict(val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed, brier_threshold=brier_threshold, ece_bins=ece_bins)
    return CalibrationComparisonV2(
        baseline=_evaluate_condition("baseline", report.adversarial_records, **kwargs),
        with_witness=_evaluate_condition("with_witness", report.combined_with_witness, **kwargs),
        with_text_claims=_evaluate_condition("with_text_claims", report.combined_with_text_claims, **kwargs),
        with_both=_evaluate_condition("with_both", report.combined_all, **kwargs),
    )


__all__ = [
    "MixedCorpusReportV2",
    "build_mixed_corpus_v2",
    "ConditionResult",
    "CalibrationComparisonV2",
    "compare_calibration_across_sources",
]
