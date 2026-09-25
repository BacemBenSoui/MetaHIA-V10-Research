"""Scorer for P1-TEXT-STRUCT v0: compares predicted and gold target structures (STRUCTURE_CONVENTION.md).

Purely functional: (predicted_structure, gold_structure) -> metrics. It never produces or reads an
epistemic verdict, never runs the Core or any verifier, and does NOT audit the gateway's resources:
that is a system-compliance check (compliance_audit.py), not observable from (prediction, reference).

Structures are JSON trees: a leaf is a string, an application is [head, *args], abstention is None.

Safety gates (hard, pre-registered = 1.00) are computed on position addresses (child indices only,
never head labels), so a morphology error on a head is never counted as a role or scope fault:
  - negation preservation: same number of neg nodes;
  - negation scope: same set of neg addresses;
  - role preservation: every leaf present in both trees sits at the same address.
Descriptive measures: exact structure (with bootstrap CI), argument F1, head F1, coverage/abstention.
An in-convention None counts as a coverage failure and as a non-exact item: abstention can never
raise the headline exactness.
"""
from __future__ import annotations

import random
from collections import Counter
from typing import Iterable, Optional

BOOTSTRAP_SEED, BOOTSTRAP_N = 20260925, 10_000


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


def neg_addresses(tree, address=()) -> set:
    """Address (tuple of child indices from the root) of every neg node."""
    if isinstance(tree, str):
        return set()
    here = {address} if tree[0] == "neg" else set()
    for i, child in enumerate(tree[1:], start=1):
        here |= neg_addresses(child, address + (i,))
    return here


def leaf_addresses(tree, address=()) -> dict:
    """leaf -> set of addresses where it occurs (index-only paths)."""
    if isinstance(tree, str):
        return {tree: {address}}
    out: dict = {}
    for i, child in enumerate(tree[1:], start=1):
        for leaf, addrs in leaf_addresses(child, address + (i,)).items():
            out.setdefault(leaf, set()).update(addrs)
    return out


def _prf(pred: Counter, gold: Counter) -> dict:
    common = sum((pred & gold).values())
    p = common / sum(pred.values()) if pred else (1.0 if not gold else 0.0)
    r = common / sum(gold.values()) if gold else (1.0 if not pred else 0.0)
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}


def score_item(pred: Optional[object], gold: Optional[object]) -> dict:
    if gold is None:  # out of convention: the correct output is an abstention
        return {"in_convention": False, "pred_abstain": pred is None, "exact": pred is None}
    if pred is None:
        return {"in_convention": True, "pred_abstain": True, "exact": False}
    pa, ga = leaf_addresses(pred), leaf_addresses(gold)
    shared = set(pa) & set(ga)
    return {
        "in_convention": True, "pred_abstain": False,
        "exact": pred == gold,
        "gate_negation_preserved": len(neg_addresses(pred)) == len(neg_addresses(gold)),
        "gate_negation_scope": neg_addresses(pred) == neg_addresses(gold),
        "gate_roles_preserved": all(pa[leaf] == ga[leaf] for leaf in shared),
        "arguments": _prf(leaves(pred), leaves(gold)),
        "heads": _prf(heads(pred), heads(gold)),
    }


def bootstrap_ci(values: list[bool], n: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> Optional[list]:
    if not values:
        return None
    rng = random.Random(seed)
    k = len(values)
    means = sorted(sum(values[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n) - 1], 4)]


def aggregate(scores: Iterable[dict], bootstrap_n: int = BOOTSTRAP_N) -> dict:
    scores = list(scores)
    in_conv = [s for s in scores if s["in_convention"]]
    answered = [s for s in in_conv if not s["pred_abstain"]]
    out_conv = [s for s in scores if not s["in_convention"]]
    rate = lambda xs, key: round(sum(x[key] for x in xs) / len(xs), 4) if xs else None
    mean = lambda key, sub: round(sum(s[key][sub] for s in answered) / len(answered), 4) if answered else None
    gates = {g: rate(answered, g) for g in ("gate_negation_preserved", "gate_negation_scope", "gate_roles_preserved")}
    exact_in_conv = [s["exact"] for s in in_conv]
    return {
        "items": len(scores), "in_convention": len(in_conv), "answered": len(answered), "out_of_convention": len(out_conv),
        "safety_gates": gates,
        "safety_gates_pass": bool(answered) and all(v == 1.0 for v in gates.values()),
        "exact_in_convention": rate(in_conv, "exact"),  # headline: an abstention counts as not exact
        "exact_in_convention_ci95": bootstrap_ci(exact_in_conv, bootstrap_n),
        "exact_answered": rate(answered, "exact"),
        "coverage_in_convention": round(len(answered) / len(in_conv), 4) if in_conv else None,
        "correct_abstention_out_of_convention": rate(out_conv, "pred_abstain"),
        "arguments_f1": mean("arguments", "f1"),
        "heads_f1": mean("heads", "f1"),
    }
