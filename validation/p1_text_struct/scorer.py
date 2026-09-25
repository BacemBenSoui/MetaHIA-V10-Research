"""Scorer for H-P1-TEXT-STRUCT: compares predicted and gold target structures (STRUCTURE_CONVENTION.md).

Structures are JSON trees: a leaf is a string, an application is [head, *args], abstention is None.
The scorer never produces or reads an epistemic verdict and never runs the Core or any verifier.
Measures (numbering of the owner's request, 2026-09-25):
  1 exact structure   2 argument conservation   3 negation conservation   4 role conservation
  5 morpho-syntactic normalisation (heads)   6 abstention   7 resource audit (audit_resources)
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Optional

RESERVED = {"attr", "neg", "card", "q_all", "q_some"}
ALLOWED_RESOURCE_CATEGORIES = {
    "determiners", "pronouns", "prepositions", "auxiliaries", "negators", "conjunctions",
    "quantifiers", "number_words", "suffix_rules", "irregular_forms",
}
FORBIDDEN_RESOURCE_HINTS = ("synonym", "antonym", "hypernym", "hyponym", "gazetteer", "entity", "sentiment",
                            "embedding", "wordnet", "colour", "color", "city", "profession", "idiom")


def leaves(tree) -> Counter:
    """Argument leaves (never heads)."""
    if isinstance(tree, str):
        return Counter([tree])
    out: Counter = Counter()
    for child in tree[1:]:
        out += leaves(child)
    return out


def heads(tree) -> Counter:
    if isinstance(tree, str):
        return Counter()
    out = Counter([tree[0]])
    for child in tree[1:]:
        out += heads(child)
    return out


def neg_paths(tree, path=()) -> set:
    """Position of every neg node, as the sequence of (head, child index) from the root."""
    if isinstance(tree, str):
        return set()
    here = {path} if tree[0] == "neg" else set()
    for i, child in enumerate(tree[1:], start=1):
        here |= neg_paths(child, path + ((tree[0], i),))
    return here


def _label(tree) -> str:
    return tree if isinstance(tree, str) else tree[0]


def role_triples(tree) -> Counter:
    """(head, argument position, head-or-leaf of the argument) for every application."""
    if isinstance(tree, str):
        return Counter()
    out = Counter((tree[0], i, _label(child)) for i, child in enumerate(tree[1:], start=1))
    for child in tree[1:]:
        out += role_triples(child)
    return out


def _prf(pred: Counter, gold: Counter) -> dict:
    common = sum((pred & gold).values())
    p = common / sum(pred.values()) if pred else (1.0 if not gold else 0.0)
    r = common / sum(gold.values()) if gold else (1.0 if not pred else 0.0)
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}


def score_item(pred: Optional[object], gold: Optional[object]) -> dict:
    if gold is None:  # sentence out of convention: correct behaviour is to abstain
        return {"gold_abstain": True, "pred_abstain": pred is None, "exact": pred is None}
    if pred is None:
        return {"gold_abstain": False, "pred_abstain": True, "exact": False}
    return {
        "gold_abstain": False, "pred_abstain": False,
        "exact": pred == gold,                                          # 1
        "arguments": _prf(leaves(pred), leaves(gold)),                   # 2
        "negation_count_match": len(neg_paths(pred)) == len(neg_paths(gold)),   # 3
        "negation_scope_match": neg_paths(pred) == neg_paths(gold),     # 3
        "roles": _prf(role_triples(pred), role_triples(gold)),           # 4
        "heads": _prf(heads(pred), heads(gold)),                         # 5
    }


def aggregate(scores: Iterable[dict]) -> dict:
    scores = list(scores)
    in_conv = [s for s in scores if not s["gold_abstain"]]
    answered = [s for s in in_conv if not s["pred_abstain"]]
    out_conv = [s for s in scores if s["gold_abstain"]]

    def mean(key, sub):
        return round(sum(s[key][sub] for s in answered) / len(answered), 4) if answered else None

    return {
        "items": len(scores),
        "exact_rate_all": round(sum(s["exact"] for s in scores) / len(scores), 4) if scores else None,   # 1
        "exact_rate_answered": round(sum(s["exact"] for s in answered) / len(answered), 4) if answered else None,
        "arguments_f1": mean("arguments", "f1"),                                                          # 2
        "negation_scope_match_rate": round(sum(s["negation_scope_match"] for s in answered) / len(answered), 4) if answered else None,  # 3
        "roles_f1": mean("roles", "f1"),                                                                  # 4
        "heads_f1": mean("heads", "f1"),                                                                  # 5
        "abstention_rate_in_convention": round(sum(s["pred_abstain"] for s in in_conv) / len(in_conv), 4) if in_conv else None,  # 6
        "correct_abstention_rate_out_of_convention": round(sum(s["pred_abstain"] for s in out_conv) / len(out_conv), 4) if out_conv else None,
    }


def audit_resources(resources: dict) -> list[str]:
    """Measure 7: every declared resource must be a permitted closed class; returns violations."""
    problems = []
    for name in resources:
        if name not in ALLOWED_RESOURCE_CATEGORIES:
            problems.append(f"resource {name!r} is not a permitted closed class")
        if any(hint in name.lower() for hint in FORBIDDEN_RESOURCE_HINTS):
            problems.append(f"resource {name!r} looks like semantic knowledge")
    return problems
