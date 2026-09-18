"""One-off script (not a test): prints the real four-way calibration
comparison (baseline / +witness / +text claims / +both) for documentation
purposes. Makes real Ollama calls (both LLM mechanisms).
"""
from __future__ import annotations

import json

from m7_corpus_mixed_v0_2 import build_mixed_corpus_v2, compare_calibration_across_sources

report = build_mixed_corpus_v2()
comparison = compare_calibration_across_sources(report, seed=0, brier_threshold=0.5)


def _row(c):
    return {
        "label": c.label,
        "train_size": c.train_size,
        "holdout_size": c.holdout_size,
        "holdout_brier": c.holdout_brier,
        "holdout_ece": c.holdout_ece,
        "promote": c.promotion.promote,
        "reasons": c.promotion.reasons,
    }


print(json.dumps({
    "adversarial_records": len(report.adversarial_records),
    "llm_records": len(report.llm_records),
    "text_claim_records": len(report.text_claim_records),
    "llm_outcomes": {o: sum(1 for r in report.llm_records if r.outcome == o) for o in {r.outcome for r in report.llm_records}},
    "text_claim_outcomes": {o: sum(1 for r in report.text_claim_records if r.outcome == o) for o in {r.outcome for r in report.text_claim_records}},
    "baseline": _row(comparison.baseline),
    "with_witness": _row(comparison.with_witness),
    "with_text_claims": _row(comparison.with_text_claims),
    "with_both": _row(comparison.with_both),
}, indent=2, default=str))
