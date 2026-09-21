"""MetaHIA P6.1 -- three-domain regression (adds Supply Chain to P5's pair).

Extends P5's stable M1-M6 v0.2 regression (Family Tree + Organization) with a
third, structurally distinct domain (industrial supply chain) to test
whether a third independent domain changes the already-documented
conclusion that cross-domain structural transfer is NOT demonstrated.

By construction it cannot: each domain's rules are built from that domain's
own relation vocabulary (MEMBRE_DE/RESPONSABLE_DE/... for Family,
TRAVAILLE_DANS/RATTACHE_A/... for Supply Chain), so a rule signature from one
domain can never be the SAME rule signature as one from another domain --
`split_by_rule`'s rule-disjoint holdout guarantee makes this structurally
impossible to observe as "transfer" even by accident. What a third domain
CAN change is the COMBINED global-class-frequency estimate (BASIS_GLOBAL_PRIOR,
the only basis this project's holdout evaluations have ever used -- see
documentation/MetaHIA_M6_Structural_Learning_V0_1.md Sec.11) and its
stability. This module measures exactly that, honestly, without asserting a
transfer claim P5 and this module both explicitly disclaim.

M1/M6 unchanged. M7 excluded. No network, no LAN dependency (this repo has
none).
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
class P6RegressionReport:
    interface_version: str
    family: DomainRegressionReport
    organization: DomainRegressionReport
    supply_chain: DomainRegressionReport
    combined_three: DomainRegressionReport
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
    for path in [ROOT / "m1_m6_interface_v0_2.py", ROOT / "p6_three_domain_regression_v0_1.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(forbidden_prefixes):
                return True
            if isinstance(node, ast.Import):
                if any(alias.name.startswith(forbidden_prefixes) for alias in node.names):
                    return True
    return False


def run_p6_regression() -> P6RegressionReport:
    family_id, family_records = _records_for_domain("FAMILY")
    org_id, org_records = _records_for_domain("ORGANIZATION")
    supply_id, supply_records = _records_for_domain("SUPPLY_CHAIN")
    combined_records = tuple(family_records) + tuple(org_records) + tuple(supply_records)

    family = _measure("FAMILY", family_id, family_records)
    organization = _measure("ORGANIZATION", org_id, org_records)
    supply_chain = _measure("SUPPLY_CHAIN", supply_id, supply_records)
    combined_three = _measure(
        "COMBINED_THREE", f"{family_id}+{org_id}+{supply_id}", combined_records
    )

    return P6RegressionReport(
        interface_version=interface_manifest_v0_2()["version"],
        family=family,
        organization=organization,
        supply_chain=supply_chain,
        combined_three=combined_three,
        m7_dependency_detected=_m7_dependency_scan(),
    )


def report_as_dict(report: P6RegressionReport) -> Mapping[str, object]:
    return asdict(report)


if __name__ == "__main__":
    report = run_p6_regression()
    print(json.dumps(report_as_dict(report), ensure_ascii=False, indent=2, sort_keys=True))
