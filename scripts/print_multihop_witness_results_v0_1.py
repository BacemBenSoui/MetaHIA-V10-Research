"""One-off script (not a test): prints the real multi-hop witness corpus
results, and the calibration effect of adding this evidence to the existing
adversarial + witness + parser union. Makes real Ollama calls.
"""
from __future__ import annotations

import json

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    brier_score_multiclass,
    evaluate_promotion,
    expected_calibration_error_top_label,
    split_by_rule,
)
from m7_corpus_from_llm_multihop_v0_1 import build_llm_witnessed_multihop_corpus
from m7_corpus_mixed_v0_2 import build_mixed_corpus_v2

multihop_report = build_llm_witnessed_multihop_corpus()

print(json.dumps({
    "candidate_patterns_considered": multihop_report.candidate_patterns_considered,
    "records": len(multihop_report.records),
    "excluded_no_llm_proposal": len(multihop_report.excluded_no_llm_proposal),
    "outcomes": {o: sum(1 for r in multihop_report.records if r.outcome == o) for o in {r.outcome for r in multihop_report.records}},
}, indent=2, default=str))

# Calibration effect: adversarial + retained union (witness + parser, length-1) + this new
# length>=2 witness extension, vs. the retained union alone.
mixed_v2 = build_mixed_corpus_v2()
retained_union = mixed_v2.combined_all  # adversarial + witness(len1) + parser(len1)
with_multihop = retained_union + multihop_report.records


def _eval(records, label):
    train, _val, holdout = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)
    brier = brier_score_multiclass(policy, holdout) if holdout else None
    ece = expected_calibration_error_top_label(policy, holdout, n_bins=5) if holdout else None
    decision = evaluate_promotion(policy, None, holdout, brier_threshold=0.5)
    return {
        "label": label, "train_size": len(train), "holdout_size": len(holdout),
        "holdout_brier": brier, "holdout_ece": ece, "promote": decision.promote, "reasons": decision.reasons,
    }


print(json.dumps({
    "retained_union_alone": _eval(retained_union, "retained_union_alone"),
    "retained_union_plus_multihop_witness": _eval(with_multihop, "retained_union_plus_multihop_witness"),
}, indent=2, default=str))
