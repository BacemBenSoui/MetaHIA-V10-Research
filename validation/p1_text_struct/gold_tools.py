"""Gold-structure tools for P1-TEXT-STRUCT v0: readable notation, convention checks, double annotation.

Annotators write structures in a readable functional notation, e.g.  neg(in(run(man), park))
which parse_notation() turns into the JSON tree ["neg", ["in", ["run", "man"], "park"]].
"none" means abstention (sentence out of convention). No verdict, no Core, no verifier.
"""
from __future__ import annotations

import re
from typing import Optional

RESERVED_ARITY = {"neg": 1, "attr": 2, "card": 2, "q_all": 1, "q_some": 1}
_TOKEN = re.compile(r"\s*([a-z0-9_]+|\(|\)|,)")
_LEAF = re.compile(r"[a-z0-9_]+")


def parse_notation(text: str) -> Optional[object]:
    text = text.strip()
    if text.lower() in {"none", "null", "abstention"}:
        return None
    tokens, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"unexpected character at {pos}: {text[pos:pos + 10]!r} (use lowercase words, ( ) ,)")
        tokens.append(m.group(1))
        pos = m.end()

    def term(i):
        if i >= len(tokens) or not _LEAF.fullmatch(tokens[i]):
            raise ValueError(f"expected a word at token {i}")
        word, i = tokens[i], i + 1
        if i < len(tokens) and tokens[i] == "(":
            args, i = [], i + 1
            while True:
                arg, i = term(i)
                args.append(arg)
                if i < len(tokens) and tokens[i] == ",":
                    i += 1
                    continue
                if i < len(tokens) and tokens[i] == ")":
                    return [word, *args], i + 1
                raise ValueError("missing ',' or ')'")
        return word, i

    tree, i = term(0)
    if i != len(tokens):
        raise ValueError("trailing tokens after the structure")
    return tree


def to_notation(tree) -> str:
    if tree is None:
        return "none"
    if isinstance(tree, str):
        return tree
    return f"{tree[0]}({', '.join(to_notation(c) for c in tree[1:])})"


def convention_problems(tree) -> list[str]:
    """Machine-checkable parts of STRUCTURE_CONVENTION.md (the rest is the annotators' judgement)."""
    problems: list[str] = []

    def walk(node, depth_under_neg: bool, is_root: bool):
        if isinstance(node, str):
            if not _LEAF.fullmatch(node):
                problems.append(f"invalid leaf {node!r}")
            return
        head, args = node[0], node[1:]
        if not args:
            problems.append(f"{head}: an application needs at least one argument")
        if head in RESERVED_ARITY and len(args) != RESERVED_ARITY[head]:
            problems.append(f"{head}: expects {RESERVED_ARITY[head]} argument(s), got {len(args)}")
        if head == "neg" and not is_root and not depth_under_neg:
            problems.append("neg must be the outermost layer (R10)")
        if head == "card" and len(args) == 2 and not (isinstance(args[1], str) and args[1].isdigit()):
            problems.append("card: second argument must be a number (R11)")
        for child in args:
            walk(child, head == "neg", False)

    if tree is not None:
        walk(tree, False, True)
    return problems


def compare_annotations(a: dict, b: dict) -> dict:
    """a, b: {item_id: tree_or_None}. Exact agreement and the list of disagreements to adjudicate."""
    ids = sorted(set(a) | set(b))
    disagreements = [i for i in ids if a.get(i, "MISSING") != b.get(i, "MISSING")]
    return {"items": len(ids), "agreement": round(1 - len(disagreements) / len(ids), 4) if ids else None,
            "to_adjudicate": disagreements}


# ------------------------------------------------------------------ command line (run by the project owner, offline)

def read_tsv(path: str) -> dict:
    """Annotation file: one line per item, 'id<TAB>sentence<TAB>structure'. Lines starting with '#' are ignored."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, start=1):
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                raise SystemExit(f"{path}:{n}: expected 3 tab-separated columns (id, sentence, structure)")
            try:
                out[parts[0]] = parse_notation(parts[2])
            except ValueError as exc:
                raise SystemExit(f"{path}:{n} ({parts[0]}): {exc}")
    return out


def main(argv=None) -> int:
    import argparse
    import json
    parser = argparse.ArgumentParser(description="P1-TEXT-STRUCT gold tools (offline, owner side)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("tsv")
    c = sub.add_parser("compare"); c.add_argument("tsv_a"); c.add_argument("tsv_b")
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        items = read_tsv(args.tsv)
        bad = {i: convention_problems(t) for i, t in items.items() if convention_problems(t)}
        print(json.dumps({"items": len(items), "abstentions": sum(t is None for t in items.values()),
                          "convention_problems": bad}, indent=1, ensure_ascii=False))
        return 1 if bad else 0
    report = compare_annotations(read_tsv(args.tsv_a), read_tsv(args.tsv_b))
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
