#!/usr/bin/env python3
"""Single held-out execution of P1-TEXT-STRUCT-A (PREREGISTRATION.md section 5). Frozen at GEL 3.

Refuses to run unless:
  - GEL2.sha256 lists the held-out files and every file given here matches its fingerprint;
  - GEL3.sha256 lists gateway_a.py, run_heldout.py and compliance_report.json, all matching;
  - compliance_report.json says compliant with 0 static violations;
  - heldout_result.json does not exist yet (one run only).
No verdict is produced; the Core is never called.

    python validation/p1_text_struct/run_heldout.py --sentences heldout_sentences.txt \
        --gold gold_adjudicated.tsv --annotation-a annotation_A.tsv --annotation-b annotation_B.tsv \
        [--categories categories.tsv]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "heldout_result.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"p1ts_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fingerprints(name: str) -> dict:
    path = HERE / name
    if not path.exists():
        raise SystemExit(f"{name} missing: the corresponding freeze has not happened")
    return {Path(parts[1]).name: parts[0] for parts in (l.split() for l in path.read_text().splitlines() if l.strip())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sentences", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--annotation-a", type=Path, required=True)
    parser.add_argument("--annotation-b", type=Path, required=True)
    parser.add_argument("--categories", type=Path)
    args = parser.parse_args()
    if RESULT.exists():
        raise SystemExit("heldout_result.json exists: the held-out execution runs once")
    gel3 = _fingerprints("GEL3.sha256")
    for name in ("gateway_a.py", "run_heldout.py", "compliance_report.json"):
        if gel3.get(name) != sha(HERE / name):
            raise SystemExit(f"{name} differs from GEL 3")
    compliance = json.loads((HERE / "compliance_report.json").read_text())
    if not compliance.get("compliant") or compliance["level_1_static_audit"]["count"] != 0:
        raise SystemExit("compliance report is not clean")
    gel2 = _fingerprints("GEL2.sha256")
    given = [args.sentences, args.gold, args.annotation_a, args.annotation_b] + ([args.categories] if args.categories else [])
    for path in given:
        if gel2.get(path.name) != sha(path):
            raise SystemExit(f"{path.name} does not match its GEL 2 fingerprint")

    gold_tools, scorer, gateway = _load("gold_tools"), _load("scorer"), _load("gateway_a")
    sentences = {}
    for line in args.sentences.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item_id, text = line.split("\t", 1)
            sentences[item_id] = text.strip()
    gold = gold_tools.read_tsv(str(args.gold))
    if set(gold) != set(sentences):
        raise SystemExit("gold ids differ from sentence ids")
    categories = {}
    if args.categories:
        for line in args.categories.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item_id, category = line.split("\t", 1)
                categories[item_id] = category.strip()

    rows, scores, by_category = [], [], {}
    for item_id in sorted(sentences):
        pred = gateway.parse(sentences[item_id])
        s = scorer.score_item(pred, gold[item_id])
        scores.append(s)
        by_category.setdefault(categories.get(item_id, "all"), []).append(s)
        rows.append({"id": item_id, "pred": pred, "gold": gold[item_id], **s})
    agreement = gold_tools.compare_annotations(gold_tools.read_tsv(str(args.annotation_a)),
                                               gold_tools.read_tsv(str(args.annotation_b)))
    result = {
        "experiment": "P1-TEXT-STRUCT-A (held-out, single run)",
        "aggregate": scorer.aggregate(scores),
        "by_category": {c: scorer.aggregate(v) for c, v in sorted(by_category.items())},
        "inter_annotator": {"agreement_before_adjudication": agreement["agreement"],
                            "adjudicated_items": len(agreement["to_adjudicate"])},
        "compliance_report_sha256": gel3["compliance_report.json"],
        "rows": rows,
    }
    RESULT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["aggregate"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
