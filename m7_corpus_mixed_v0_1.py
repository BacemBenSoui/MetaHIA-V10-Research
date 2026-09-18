"""MetaHIA M7 -- mixed-corpus promotion integration v0.1.

Answers the concrete question raised 2026-09-18: does feeding M7's LLM
evidence (GROUNDED_ANALOGY, length-1 patterns) into the SAME M6 promotion
pipeline that already runs on the adversarial verification-claims corpus
(GROUNDED_DIRECT, m6_corpus_from_m4_m5_v0_2.py) help, hurt, or leave holdout
calibration unchanged -- rather than extending scope (length>1) or preparing
third-party validation before this load-bearing question is answered.

Design (2026-09-18, chosen over the two other candidate next steps -- length>1
extension and third-party validation -- precisely because it is the cheapest
way to get the most decision-relevant number: whether this evidence source is
worth continuing to invest in at all):

    adversarial_records  = m6_corpus_from_m4_m5_v0_2.build_real_corpus_v2()
                            (all depths, GROUNDED_DIRECT)
    llm_records          = m7_corpus_from_llm_v0_1.build_llm_witnessed_corpus()
                            (depth 1 only, GROUNDED_ANALOGY)
    combined_records     = adversarial_records + llm_records

Both mechanisms already draw on the SAME corpus file
(corpus/family_tree_facts_v0_2.json) and the SAME real
acquire_cold_start()/evaluator machinery -- this module adds no new epistemic
mechanism, it only unions two already-independently-validated record streams
and reuses M6's existing split_by_rule/StructuralLearningPolicy/
evaluate_promotion unchanged.

Fairness of the comparison: split_by_rule() partitions by the SET of unique
rule signatures present in the records it is given, shuffled deterministically
by `seed`. The LLM mechanism only ever adds records for rules ALREADY present
in the adversarial corpus (it never discovers a new rule) -- so the unique
rule-signature set is identical between `adversarial_records` alone and
`combined_records`, and a fixed seed therefore assigns the SAME rules to
train/val/holdout in both cases (see
test_mixed_corpus_rule_set_is_identical_so_the_holdout_split_is_fair below,
in tests/test_m7_mixed_corpus_promotion_v0_1.py). This makes the two
calibration runs a genuine apples-to-apples comparison of "same held-out
rules, with vs without LLM evidence added to training" -- not a comparison
confounded by different holdout composition.

Live LLM results are NOT pinned to an exact value here, for the same reason
as m7_corpus_from_llm_v0_1.py: a real Ollama call is not reproducible across
runs/models/hardware. See MetaHIA_M7_LLM_Fact_Proposer_V0_1.md Sec.6 for the
real comparison numbers from an actual run, and
tests/test_m7_mixed_corpus_promotion_v0_1.py for what is asserted
deterministically (via an injected generate_fn) versus what the skippable
live demo only checks structurally.
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
from m7_llm_fact_proposer_v0_1 import GenerateFn


@dataclass(frozen=True)
class MixedCorpusReport:
    adversarial_records: Tuple[StructuralOutcomeRecord, ...]
    llm_records: Tuple[StructuralOutcomeRecord, ...]
    combined_records: Tuple[StructuralOutcomeRecord, ...]


def build_mixed_corpus(
    *,
    generate_fn: Optional[GenerateFn] = None,
    model: str = "llama3.2:latest",
) -> MixedCorpusReport:
    adversarial_report = build_real_corpus_v2()
    llm_report = build_llm_witnessed_corpus(generate_fn=generate_fn, model=model)
    return MixedCorpusReport(
        adversarial_records=adversarial_report.records,
        llm_records=llm_report.records,
        combined_records=adversarial_report.records + llm_report.records,
    )


@dataclass(frozen=True)
class CalibrationComparison:
    baseline_train_size: int
    baseline_holdout_size: int
    baseline_holdout_brier: float
    baseline_holdout_ece: float
    baseline_promotion: PromotionDecision

    mixed_train_size: int
    mixed_holdout_size: int
    mixed_holdout_brier: float
    mixed_holdout_ece: float
    mixed_promotion: PromotionDecision


def compare_calibration_with_and_without_llm_evidence(
    report: MixedCorpusReport,
    *,
    val_fraction: float = 0.2,
    holdout_fraction: float = 0.2,
    seed: int = 0,
    brier_threshold: float = 0.5,
    ece_bins: int = 5,
) -> CalibrationComparison:
    """Fits and evaluates two policies with the SAME split parameters:
    baseline (adversarial evidence only, the already-validated M6 v0.2
    mechanism) and mixed (adversarial + LLM evidence). Both are real
    computations through the unchanged M6 machinery -- no new metric, no new
    threshold logic.
    """
    baseline_train, _baseline_val, baseline_holdout = split_by_rule(
        report.adversarial_records, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed
    )
    baseline_policy = StructuralLearningPolicy().fit(baseline_train)
    baseline_brier = brier_score_multiclass(baseline_policy, baseline_holdout) if baseline_holdout else float("nan")
    baseline_ece = (
        expected_calibration_error_top_label(baseline_policy, baseline_holdout, n_bins=ece_bins)
        if baseline_holdout
        else float("nan")
    )
    baseline_decision = evaluate_promotion(baseline_policy, None, baseline_holdout, brier_threshold=brier_threshold)

    mixed_train, _mixed_val, mixed_holdout = split_by_rule(
        report.combined_records, val_fraction=val_fraction, holdout_fraction=holdout_fraction, seed=seed
    )
    mixed_policy = StructuralLearningPolicy().fit(mixed_train)
    mixed_brier = brier_score_multiclass(mixed_policy, mixed_holdout) if mixed_holdout else float("nan")
    mixed_ece = (
        expected_calibration_error_top_label(mixed_policy, mixed_holdout, n_bins=ece_bins) if mixed_holdout else float("nan")
    )
    mixed_decision = evaluate_promotion(mixed_policy, None, mixed_holdout, brier_threshold=brier_threshold)

    return CalibrationComparison(
        baseline_train_size=len(baseline_train),
        baseline_holdout_size=len(baseline_holdout),
        baseline_holdout_brier=baseline_brier,
        baseline_holdout_ece=baseline_ece,
        baseline_promotion=baseline_decision,
        mixed_train_size=len(mixed_train),
        mixed_holdout_size=len(mixed_holdout),
        mixed_holdout_brier=mixed_brier,
        mixed_holdout_ece=mixed_ece,
        mixed_promotion=mixed_decision,
    )


__all__ = [
    "MixedCorpusReport",
    "build_mixed_corpus",
    "CalibrationComparison",
    "compare_calibration_with_and_without_llm_evidence",
]
