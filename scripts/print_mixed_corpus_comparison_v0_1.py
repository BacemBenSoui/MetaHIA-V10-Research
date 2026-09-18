"""One-off script (not a test): prints the real mixed-corpus calibration
comparison numbers for documentation purposes. Makes a real Ollama call.
"""
from __future__ import annotations

import json

from m7_corpus_mixed_v0_1 import build_mixed_corpus, compare_calibration_with_and_without_llm_evidence

report = build_mixed_corpus()
comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)

print(json.dumps({
    "adversarial_records": len(report.adversarial_records),
    "llm_records": len(report.llm_records),
    "combined_records": len(report.combined_records),
    "llm_outcomes": {o: sum(1 for r in report.llm_records if r.outcome == o) for o in {r.outcome for r in report.llm_records}},
    "baseline_train_size": comparison.baseline_train_size,
    "baseline_holdout_size": comparison.baseline_holdout_size,
    "baseline_holdout_brier": comparison.baseline_holdout_brier,
    "baseline_holdout_ece": comparison.baseline_holdout_ece,
    "baseline_promote": comparison.baseline_promotion.promote,
    "baseline_reasons": comparison.baseline_promotion.reasons,
    "mixed_train_size": comparison.mixed_train_size,
    "mixed_holdout_size": comparison.mixed_holdout_size,
    "mixed_holdout_brier": comparison.mixed_holdout_brier,
    "mixed_holdout_ece": comparison.mixed_holdout_ece,
    "mixed_promote": comparison.mixed_promotion.promote,
    "mixed_reasons": comparison.mixed_promotion.reasons,
}, indent=2, default=str))
