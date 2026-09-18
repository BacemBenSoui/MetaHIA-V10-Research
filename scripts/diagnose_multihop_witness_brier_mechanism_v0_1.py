"""One-off diagnostic (not a test, no network calls): verifies WHY adding
the multi-hop witness's evidence improved holdout Brier in the real run
(2026-09-18), by inspecting StructuralLearningPolicy.predict()'s `basis`
for every holdout record, rather than guessing.

Uses fully deterministic fakes reproducing the REAL run's exact outcome
SHAPE (witness: 16/16 CONTRADICTED; multihop witness: 20/20 CONTRADICTED;
parser: the known 10 SUPPORTED / 6 CONTRADICTED perfect-parser diversity)
combined with the real, non-LLM adversarial corpus -- this reproduces the
structural situation exactly without needing new live Ollama calls, since
the mechanism-level question (which basis drives predictions) does not
depend on which specific run's exact record counts were observed.

Key structural fact checked directly, not assumed: split_by_rule() puts
every record of a given rule into exactly ONE split. So a holdout record
belonging to a rule with ANY training representation is predicted via
EXACT_BUCKET/RULE_ONLY; a holdout record whose rule has ZERO training
representation (true for any brand-new multihop rule that lands in
holdout) can ONLY be predicted via BASIS_GLOBAL_PRIOR (the class
distribution pooled across ALL training records, regardless of rule) or
BASIS_UNIFORM_NO_DATA. If adding 20 new CONTRADICTED training records
shifts predictions for OTHER (unrelated-rule) holdout records, it must be
happening through this global-prior channel, not through any
per-rule "same bias in train and holdout" mechanism (which is structurally
impossible here).
"""
from __future__ import annotations

import json
from collections import Counter

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    brier_score_multiclass,
    split_by_rule,
)
from m7_corpus_from_llm_multihop_v0_1 import build_llm_witnessed_multihop_corpus
from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus
from m7_corpus_from_text_claims_v0_1 import TEXT_CLAIMS_PATH, build_text_claim_corpus


def _perfect_parser(prompt):
    claims = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    for claim in claims:
        if claim["text"] in prompt:
            return {"subject": claim["subject"], "relation": claim["relation"], "object": claim["asserted_object"]}
    return None


adversarial = build_real_corpus_v2()
witness = build_llm_witnessed_corpus(generate_fn=lambda p: {"object": "AlwaysWrong_Witness"})
parser = build_text_claim_corpus(generate_fn=_perfect_parser)
multihop = build_llm_witnessed_multihop_corpus(generate_fn=lambda p: {"object": "AlwaysWrong_Multihop"})

print(json.dumps({
    "adversarial": len(adversarial.records),
    "witness": len(witness.records),
    "parser": len(parser.records),
    "multihop": len(multihop.records),
}, indent=2))

retained_union = adversarial.records + witness.records + parser.records
with_multihop = retained_union + multihop.records


def _diagnose(records, label):
    train, _val, holdout = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    train_rule_signatures = {r.rule_signature for r in train}
    policy = StructuralLearningPolicy().fit(train)
    brier = brier_score_multiclass(policy, holdout)

    basis_counts = Counter()
    cross_split_violation = False
    for r in holdout:
        if r.rule_signature in train_rule_signatures:
            cross_split_violation = True
        pred = policy.predict(r.rule, r.novelty, r.redundancy, r.depth, r.provenance)
        basis_counts[pred.basis] += 1

    return {
        "label": label,
        "train_size": len(train),
        "holdout_size": len(holdout),
        "holdout_brier": brier,
        "basis_distribution_over_holdout": dict(basis_counts),
        "any_holdout_rule_also_in_train": cross_split_violation,  # structural check: must be False
    }


print(json.dumps(_diagnose(retained_union, "retained_union"), indent=2))
print(json.dumps(_diagnose(with_multihop, "retained_union_plus_multihop"), indent=2))

# Direct comparison of the GLOBAL PRIOR distribution before/after adding multihop evidence,
# since that is the only channel through which the new records could affect predictions for
# holdout records belonging to OTHER, pre-existing rules.
train_before, _v, _h = split_by_rule(retained_union, val_fraction=0.2, holdout_fraction=0.2, seed=0)
train_after, _v2, _h2 = split_by_rule(with_multihop, val_fraction=0.2, holdout_fraction=0.2, seed=0)
print(json.dumps({
    "global_prior_before": dict(Counter(r.outcome for r in train_before)),
    "global_prior_after": dict(Counter(r.outcome for r in train_after)),
}, indent=2))
