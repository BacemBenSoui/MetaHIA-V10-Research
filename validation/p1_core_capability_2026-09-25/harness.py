#!/usr/bin/env python3
"""P1 core-capability experiment (2026-09-25): what unmodified K3 does on hand-structured P1 pairs.

Pre-registered in PREREGISTRATION.md (sha256 in PREREGISTRATION.sha256). Runs once.
kernel2.py is imported read-only and its sha256 is checked before and after the run.
The projection layer below is the object under test for the epistemic verdicts; it lives
outside K3 on purpose (K3 structural result != semantic interpretation != epistemic verdict).

    python validation/p1_core_capability_2026-09-25/harness.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
KERNEL = ROOT / "kernel2.py"
KERNEL_SHA256 = "c76adfd2eed8e3ba6022200e7eba6c381f262602f626850cd80af65a0efc9aa9"
RESULTS = HERE / "results.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_freeze() -> None:
    if RESULTS.exists():
        raise SystemExit("results.json exists: this experiment runs once")
    expected = dict(line.split()[::-1] for line in (HERE / "PREREGISTRATION.sha256").read_text().splitlines() if line.strip())
    for name, digest in expected.items():
        if sha(HERE / name) != digest:
            raise SystemExit(f"frozen file changed: {name}")
    if sha(KERNEL) != KERNEL_SHA256:
        raise SystemExit("kernel2.py differs from the frozen K3 kernel")


check_freeze()
import kernel2 as K  # noqa: E402  (imported only after the freeze check)

NEG_REF = K.node_ref("op:neg")


def build(expr):
    """string -> opaque leaf NodeRef; '@x' -> operator NodeRef op:x; [head, *args] -> apply(op:head, *args)."""
    if isinstance(expr, str):
        return K.node_ref("op:" + expr[1:]) if expr.startswith("@") else K.node_ref(expr)
    head, *args = expr
    return K.apply(K.node_ref("op:" + head), *[build(a) for a in args])


def kind_of(result) -> str:
    return "None" if result is None else result.kind


def raw_compare(a, b) -> str:
    try:
        return kind_of(K.compare(a, b))
    except ValueError as exc:
        return f"ERROR: {exc}"


# ------------------------------------------------------------------ projection layer (under test)

def is_neg(node) -> bool:
    return isinstance(node, K.Node) and len(node.children) == 2 and K.structural_equal(node.children[0], NEG_REF)


def leaf_differences(a, b) -> list:
    """Positions where two same-shape structures differ, found with K3's own structural_equal."""
    if K.structural_equal(a, b):
        return []
    if isinstance(a, K.Node) and isinstance(b, K.Node) and a.kind == b.kind and len(a.children) == len(b.children):
        out = []
        for ca, cb in zip(a.children, b.children):
            out.extend(leaf_differences(ca, cb))
        return out
    return [(a, b)]


def incompatible(x, y, relations) -> bool:
    """A provided relation incompatible(x, y); declared symmetric by the pre-registration."""
    probe = (K.apply(K.node_ref("op:incompatible"), x, y), K.apply(K.node_ref("op:incompatible"), y, x))
    return any(K.structural_equal(r, p) for r in relations for p in probe)


def project(claim, evidence, relations) -> str:
    if K.structural_equal(claim, evidence):
        return "SUPPORTED"
    if is_neg(claim) != is_neg(evidence):
        negated, other = (claim, evidence) if is_neg(claim) else (evidence, claim)
        return "CONTRADICTED" if K.structural_equal(negated.children[1], other) else "UNKNOWN"
    diffs = leaf_differences(claim, evidence)
    if len(diffs) == 1 and all(isinstance(v, K.NodeRef) for v in diffs[0]) and incompatible(*diffs[0], relations):
        return "CONTRADICTED"
    return "UNKNOWN"


# ------------------------------------------------------------------ run

def main() -> int:
    data = json.loads((HERE / "pairs.json").read_text(encoding="utf-8"))
    items = data["items"]
    opp = [i for i in items if i["category"] == "OPP"]
    rows = []
    for item in items:
        evidence, claim = build(item["struct_premise"]), build(item["struct_hypothesis"])
        row = {"id": item["id"], "category": item["category"], "human_label": item["human_label"],
               "k3_compare": raw_compare(evidence, claim),
               "leaf_differences": len(leaf_differences(claim, evidence)),
               "projection": project(claim, evidence, [])}
        if item["category"] == "NEG":
            negated, affirmative = (claim, evidence) if is_neg(claim) else (evidence, claim)
            aff_expr = item["struct_premise"] if not is_neg(evidence) else item["struct_hypothesis"]
            scope_variant = build([aff_expr[0], ["neg", aff_expr[1]], *aff_expr[2:]])
            row["neg_a1_representable"] = (negated.kind == K.OBSERVATION and is_neg(negated)
                                           and isinstance(negated.children[1], K.Node))
            row["neg_a2_inner_preserved"] = K.structural_equal(negated.children[1], affirmative)
            row["neg_a3_scope_distinct"] = (not K.structural_equal(scope_variant, negated)
                                            and not K.structural_equal(scope_variant, affirmative))
        if item["category"] == "OPP":
            relations = [build(r) for r in item["relations"]]
            reversed_rel = [build([r[0], r[2], r[1]]) for r in item["relations"]]
            other = opp[(opp.index(item) + 1) % len(opp)]
            row["opp_b1_no_relation"] = project(claim, evidence, [])
            row["opp_b2_relation"] = project(claim, evidence, relations)
            row["opp_b3_reversed_relation"] = project(claim, evidence, reversed_rel)
            row["opp_b4_irrelevant_relation"] = project(claim, evidence, [build(r) for r in other["relations"]])
        rows.append(row)
    if sha(KERNEL) != KERNEL_SHA256:
        raise SystemExit("kernel2.py changed during the run")
    RESULTS.write_text(json.dumps({"kernel2_sha256": KERNEL_SHA256, "rows": rows}, indent=1, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
