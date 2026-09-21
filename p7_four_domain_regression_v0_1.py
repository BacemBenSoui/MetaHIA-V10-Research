"""MetaHIA P7.1 -- four-domain regression (adds Library to P6's trio).

Extends P6's three-domain regression (Family Tree + Organization + Supply
Chain) with a fourth, structurally distinct domain (library catalogue) to
test whether a fourth independent domain continues the stabilization trend
already observed going from two to three domains (P5 Sec.5 -> P6 Sec.4:
combined holdout Brier population std 0.107167 -> 0.056129).

By construction, cross-domain structural transfer still cannot be
demonstrated here for the same reason documented in
documentation/P6_Third_Domain_Supply_Chain_V0_1.md Sec.3: each domain's
rules are built from that domain's own relation vocabulary, so
split_by_rule() can never place one domain's rule in another's holdout.
This module measures, honestly, whatever effect pooling a fourth domain has
on the combined global-class-frequency estimate's stability -- without
asserting a transfer claim.

M1/M6 unchanged. M7 excluded. No network, no LAN dependency.
"""
from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

from m1_m6_interface_v0_1 import M1StructuralPacket, compose_m1_to_m6
from m1_m6_interface_v0_2 import M1M6StableEnvelope, interface_manifest_v0_2, stabilize_packet
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

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DomainRegressionReport:
    domain_id: str
    corpus_id: str
    records: int
    rules: int
    train: int
    validation: int
    holdout: int
    holdout_rules: int
    brier: float
    ece: float
    interface_roundtrip_ok: bool


@dataclass(frozen=True)
class P7RegressionReport:
    interface_version: str
    family: DomainRegressionReport
    organization: DomainRegressionReport
    supply_chain: DomainRegressionReport
    library: DomainRegressionReport
    combined_four: DomainRegressionReport
    m7_dependency_detected: bool


def _corpus_id_from_file(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data["corpus_id"])


def _records_for_domain(domain_id: str):
    if domain_id == "FAMILY":
        report = build_real_corpus_v2()
        corpus_id = _corpus_id_from_file(ROOT / "corpus" / "family_tree_facts_v0_2.json")
        return corpus_id, tuple(report.records)
    if domain_id == "ORGANIZATION":
        report = build_organization_corpus()
        corpus_id = _corpus_id_from_file(ROOT / "corpus" / "organization_facts_v0_1.json")
        return corpus_id, tuple(report.records)
    if domain_id == "SUPPLY_CHAIN":
        report = build_supply_chain_corpus()
        corpus_id = _corpus_id_from_file(ROOT / "corpus" / "supply_chain_facts_v0_1.json")
        return corpus_id, tuple(report.records)
    if domain_id == "LIBRARY":
        report = build_library_corpus()
        corpus_id = _corpus_id_from_file(ROOT / "corpus" / "library_facts_v0_1.json")
        return corpus_id, tuple(report.records)
    raise ValueError(f"unknown domain_id={domain_id!r}")


def _packet_from_record(record: StructuralOutcomeRecord):
    structural_packet = compose_m1_to_m6(
        structural=M1StructuralPacket(
            packet_id=record.record_id,
            structure=record.rule,
            depth=record.depth,
            novelty=record.novelty,
            redundancy=record.redundancy,
            provenance=("M4",),
            derived=True,
        ),
        outcome=record.outcome,
        provenance=record.provenance,
        evidence_ids=(record.record_id,),
        independent_evidence_count=1,
        expected_gain=0.0,
        actual_cost=0.0,
        useful=True,
        decision="REGRESSION",
    )
    return structural_packet


def _wrap_and_roundtrip(records: Sequence[StructuralOutcomeRecord], corpus_id: str, domain_id: str) -> bool:
    for record in records:
        packet = _packet_from_record(record)
        env = stabilize_packet(packet, corpus_id=corpus_id, domain_id=domain_id)
        restored = M1M6StableEnvelope.from_json(
            env.to_json(),
            rule_resolver=lambda _packet_id, _wire, original=record.rule: original,
        )
        if restored.as_record_kwargs() != env.as_record_kwargs():
            return False
        if restored.as_record_kwargs()["record_id"] != record.record_id:
            return False
        if restored.domain_id != domain_id or restored.corpus_id != corpus_id:
            return False
    return True


def _measure(domain_id: str, corpus_id: str, records: Sequence[StructuralOutcomeRecord]) -> DomainRegressionReport:
    train, val, holdout = split_by_rule(records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    policy = StructuralLearningPolicy().fit(train)
    holdout_rules = {r.rule_signature for r in holdout}
    train_rules = {r.rule_signature for r in train}
    assert train_rules.isdisjoint(holdout_rules)
    brier = brier_score_multiclass(policy, holdout) if holdout else float("nan")
    ece = expected_calibration_error_top_label(policy, holdout) if holdout else float("nan")
    return DomainRegressionReport(
        domain_id=domain_id,
        corpus_id=corpus_id,
        records=len(records),
        rules=len({r.rule_signature for r in records}),
        train=len(train),
        validation=len(val),
        holdout=len(holdout),
        holdout_rules=len(holdout_rules),
        brier=brier,
        ece=ece,
        interface_roundtrip_ok=_wrap_and_roundtrip(records, corpus_id, domain_id),
    )


def _m7_dependency_scan() -> bool:
    forbidden_prefixes = ("m7_",)
    for path in [ROOT / "m1_m6_interface_v0_2.py", ROOT / "p7_four_domain_regression_v0_1.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(forbidden_prefixes):
                return True
            if isinstance(node, ast.Import):
                if any(alias.name.startswith(forbidden_prefixes) for alias in node.names):
                    return True
    return False


def run_p7_regression() -> P7RegressionReport:
    family_id, family_records = _records_for_domain("FAMILY")
    org_id, org_records = _records_for_domain("ORGANIZATION")
    supply_id, supply_records = _records_for_domain("SUPPLY_CHAIN")
    library_id, library_records = _records_for_domain("LIBRARY")
    combined_records = (
        tuple(family_records) + tuple(org_records) + tuple(supply_records) + tuple(library_records)
    )

    family = _measure("FAMILY", family_id, family_records)
    organization = _measure("ORGANIZATION", org_id, org_records)
    supply_chain = _measure("SUPPLY_CHAIN", supply_id, supply_records)
    library = _measure("LIBRARY", library_id, library_records)
    combined_four = _measure(
        "COMBINED_FOUR", f"{family_id}+{org_id}+{supply_id}+{library_id}", combined_records
    )

    return P7RegressionReport(
        interface_version=interface_manifest_v0_2()["version"],
        family=family,
        organization=organization,
        supply_chain=supply_chain,
        library=library,
        combined_four=combined_four,
        m7_dependency_detected=_m7_dependency_scan(),
    )


def report_as_dict(report: P7RegressionReport) -> Mapping[str, object]:
    return asdict(report)


if __name__ == "__main__":
    report = run_p7_regression()
    print(json.dumps(report_as_dict(report), ensure_ascii=False, indent=2, sort_keys=True))
