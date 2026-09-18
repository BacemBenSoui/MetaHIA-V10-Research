"""One-off script (not a test): prints the real consensus text-claim corpus
results for documentation purposes. Makes real Ollama calls to BOTH the
local and LAN sandbox servers (both voters, always contacted).
"""
from __future__ import annotations

import json

from m7_corpus_from_text_claims_consensus_v0_1 import build_consensus_text_claim_corpus
from m7_corpus_mixed_v0_2 import build_mixed_corpus_v2, compare_calibration_across_sources
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2

report = build_consensus_text_claim_corpus()

print(json.dumps({
    "candidate_patterns_considered": report.candidate_patterns_considered,
    "records": len(report.records),
    "excluded_no_matching_text_claim": len(report.excluded_no_matching_text_claim),
    "excluded_voter_failed": len(report.excluded_voter_failed),
    "excluded_voter_failed_detail": list(report.excluded_voter_failed),
    "excluded_disagreement": len(report.excluded_disagreement),
    "excluded_disagreement_detail": list(report.excluded_disagreement),
    "excluded_parsing_mismatch": len(report.excluded_parsing_mismatch),
    "outcomes": {o: sum(1 for r in report.records if r.outcome == o) for o in {r.outcome for r in report.records}},
}, indent=2, ensure_ascii=False, default=str))

# Now compute the calibration effect of consensus-filtered text-claim evidence
# vs. the adversarial baseline, mirroring the v0.2 four-way comparison but
# substituting the consensus-filtered records for the raw single-model ones.
adversarial = build_real_corpus_v2()
from m6_structural_learning_v0_1 import StructuralLearningPolicy, brier_score_multiclass, evaluate_promotion, expected_calibration_error_top_label, split_by_rule

combined = adversarial.records + report.records
train, _val, holdout = split_by_rule(combined, val_fraction=0.2, holdout_fraction=0.2, seed=0)
policy = StructuralLearningPolicy().fit(train)
brier = brier_score_multiclass(policy, holdout) if holdout else None
ece = expected_calibration_error_top_label(policy, holdout, n_bins=5) if holdout else None
decision = evaluate_promotion(policy, None, holdout, brier_threshold=0.5)

print(json.dumps({
    "adversarial_plus_consensus_text_claims": {
        "train_size": len(train),
        "holdout_size": len(holdout),
        "holdout_brier": brier,
        "holdout_ece": ece,
        "promote": decision.promote,
        "reasons": decision.reasons,
    }
}, indent=2, default=str))
