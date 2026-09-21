"""MetaHIA V10 -- minimal M1-M6 preprod CLI for human testing (v0.1).

This is the first human-usable surface over the M1-M6 core algebra.  Before
this file, the only way to exercise M1-M6 was to import Python modules
directly (m1_m6_interface_v0_1.py / v0_2.py are internal composition
contracts, not a CLI/API) -- this is exactly the gap identified when this
research line was asked whether the core algebra could go to human-testing
preprod.

Scope, deliberately narrow:
  - reads the four existing real corpora (Family Tree v0.2, Organization
    v0.1, Supply Chain v0.1, Library v0.1) via the already-validated
    non-degenerate builders, plus a pooled `combined` pseudo-domain (all real
    domains together -- a stabilization baseline over the pooled global
    prior, NOT a cross-domain transfer claim, see
    documentation/P6_Third_Domain_Supply_Chain_V0_1.md Sec.3-4 and
    documentation/P7_Fourth_Domain_Library_V0_1.md; `combined`'s own
    definition evolves as domains are added -- it is a tool's current view,
    not a frozen scientific result);
  - runs the same rule-disjoint split/fit/holdout evaluation M6 always uses;
  - never hides the BASIS_GLOBAL_PRIOR finding: every single prediction this
    CLI prints names its own basis (BASIS_EXACT_BUCKET / BASIS_RULE_ONLY /
    BASIS_GLOBAL_PRIOR / BASIS_UNIFORM_NO_DATA) and support count, so a human
    tester sees exactly how much (or how little) evidence backs each number.

Explicitly out of scope: M7 (LLM layer) is never imported here, matching
m1_m6_interface_v0_2.py's own exclusion.  No network call of any kind.
"""
from __future__ import annotations

import argparse
import json
from typing import Sequence

from m1_m6_interface_v0_2 import interface_manifest_v0_2
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_corpus_from_organization_v0_1 import build_organization_corpus
from m6_corpus_from_supply_chain_v0_1 import build_supply_chain_corpus
from m6_corpus_from_library_v0_1 import build_library_corpus
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    StructuralOutcomeRecord,
    brier_score_multiclass,
    expected_calibration_error_top_label,
    split_by_rule,
)

REAL_DOMAINS = ("family", "organization", "supply_chain", "library")
DOMAINS = REAL_DOMAINS + ("combined",)


def _records_for_domain(domain: str) -> tuple[str, tuple[StructuralOutcomeRecord, ...]]:
    if domain == "family":
        report = build_real_corpus_v2()
        return "FAMILY-TREE-V0.2", tuple(report.records)
    if domain == "organization":
        report = build_organization_corpus()
        return "ORGANIZATION-V0.1", tuple(report.records)
    if domain == "supply_chain":
        report = build_supply_chain_corpus()
        return "SUPPLY-CHAIN-V0.1", tuple(report.records)
    if domain == "library":
        report = build_library_corpus()
        return "LIBRARY-V0.1", tuple(report.records)
    if domain == "combined":
        # Pools all real domains -- mirrors p7_four_domain_regression_v0_1.py's
        # combined_four exactly. This is a regression/stabilization baseline over the
        # pooled global class-frequency prior, NOT a cross-domain transfer claim: each
        # domain's rule signatures come from that domain's own relation vocabulary, so
        # split_by_rule() can never place one domain's rule in another's holdout (see
        # documentation/P6_Third_Domain_Supply_Chain_V0_1.md Sec.3). This pseudo-domain's
        # own definition evolves as REAL_DOMAINS grows -- it always means "everything
        # currently known", not a number frozen at any past commit.
        corpus_ids = []
        all_records: list[StructuralOutcomeRecord] = []
        for real_domain in REAL_DOMAINS:
            corpus_id, records = _records_for_domain(real_domain)
            corpus_ids.append(corpus_id)
            all_records.extend(records)
        return "+".join(corpus_ids), tuple(all_records)
    raise ValueError(f"unknown domain {domain!r}; choose from {DOMAINS}")


def _basis_distribution(policy: StructuralLearningPolicy, records: Sequence[StructuralOutcomeRecord]) -> dict:
    counts: dict[str, int] = {}
    for r in records:
        pred = policy.predict(r.rule, r.novelty, r.redundancy, r.depth, r.provenance)
        counts[pred.basis] = counts.get(pred.basis, 0) + 1
    return counts


def cmd_manifest(_args: argparse.Namespace) -> dict:
    return {
        "cli_version": "0.1",
        "purpose": "human preprod smoke-testing of the M1-M6 core algebra; NOT a production API",
        "domains_available": list(DOMAINS),
        "m7_excluded": True,
        "interface": interface_manifest_v0_2(),
        "known_limitation": (
            "split_by_rule() guarantees a holdout rule's signature is absent from "
            "training, so StructuralLearningPolicy.predict() has never used "
            "BASIS_EXACT_BUCKET/BASIS_RULE_ONLY on any holdout evaluation in this "
            "project's history -- every holdout Brier/ECE number measures global "
            "class-frequency generalization, never rule-specific learning. This CLI "
            "surfaces `basis` on every prediction so this is never hidden."
        ),
        "combined_domain_caveat": (
            "--domain combined pools all three real domains for a stabilization/"
            "regression baseline over the pooled global-class-frequency prior. It is "
            "NOT a cross-domain transfer claim: each domain's rule signatures come "
            "from that domain's own relation vocabulary, so split_by_rule() can never "
            "place one domain's rule in another's holdout."
        ),
    }


def cmd_list_records(args: argparse.Namespace) -> dict:
    _corpus_id, records = _records_for_domain(args.domain)
    return {
        "domain": args.domain,
        "record_count": len(records),
        "records": [
            {
                "record_id": r.record_id,
                "outcome": r.outcome,
                "depth": r.depth,
                "provenance": r.provenance,
                "rule_signature_repr": repr(r.rule_signature)[:120],
            }
            for r in records
        ],
    }


def cmd_regression(args: argparse.Namespace) -> dict:
    corpus_id, records = _records_for_domain(args.domain)
    train, val, holdout = split_by_rule(
        records, val_fraction=0.2, holdout_fraction=0.2, seed=args.seed
    )
    policy = StructuralLearningPolicy().fit(train)
    train_rules = {r.rule_signature for r in train}
    holdout_rules = {r.rule_signature for r in holdout}
    assert train_rules.isdisjoint(holdout_rules), "split_by_rule invariant violated"
    brier = brier_score_multiclass(policy, holdout) if holdout else None
    ece = expected_calibration_error_top_label(policy, holdout) if holdout else None
    return {
        "domain": args.domain,
        "corpus_id": corpus_id,
        "seed": args.seed,
        "records": len(records),
        "rules": len({r.rule_signature for r in records}),
        "train": len(train),
        "validation": len(val),
        "holdout": len(holdout),
        "holdout_rules_disjoint_from_train": True,
        "brier_holdout": brier,
        "ece_holdout": ece,
        "basis_distribution_over_holdout": _basis_distribution(policy, holdout),
    }


def cmd_predict(args: argparse.Namespace) -> dict:
    corpus_id, records = _records_for_domain(args.domain)
    train, _val, holdout = split_by_rule(
        records, val_fraction=0.2, holdout_fraction=0.2, seed=args.seed
    )
    policy = StructuralLearningPolicy().fit(train)
    by_id = {r.record_id: r for r in records}
    record = by_id.get(args.record_id)
    if record is None:
        raise SystemExit(
            f"record_id {args.record_id!r} not found in domain {args.domain!r}; "
            "use `list-records` to see valid ids"
        )
    pred = policy.predict(record.rule, record.novelty, record.redundancy, record.depth, record.provenance)
    in_holdout = any(r.record_id == record.record_id for r in holdout)
    return {
        "domain": args.domain,
        "corpus_id": corpus_id,
        "seed": args.seed,
        "record_id": record.record_id,
        "was_in_holdout_for_this_seed": in_holdout,
        "actual_outcome": record.outcome,
        "predicted_distribution": pred.distribution,
        "basis": pred.basis,
        "support": pred.support,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli_preprod_v0_1.py",
        description=(
            "MetaHIA V10 -- minimal preprod CLI over the M1-M6 core algebra "
            "(research repo, M7 excluded). For human smoke-testing, not production use."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("manifest", help="print interface manifest and known limitations")

    p_list = sub.add_parser("list-records", help="list every record in a domain corpus")
    p_list.add_argument("--domain", required=True, choices=DOMAINS)

    p_reg = sub.add_parser("regression", help="run rule-disjoint holdout regression on a domain")
    p_reg.add_argument("--domain", required=True, choices=DOMAINS)
    p_reg.add_argument("--seed", type=int, default=0)

    p_pred = sub.add_parser("predict", help="predict the outcome distribution for one record")
    p_pred.add_argument("--domain", required=True, choices=DOMAINS)
    p_pred.add_argument("--record-id", required=True)
    p_pred.add_argument("--seed", type=int, default=0)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = {
        "manifest": cmd_manifest,
        "list-records": cmd_list_records,
        "regression": cmd_regression,
        "predict": cmd_predict,
    }[args.command]
    result = handler(args)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
