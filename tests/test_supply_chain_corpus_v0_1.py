"""Independent third-domain corpus validation v0.1."""
from __future__ import annotations

import json
from pathlib import Path

from m6_corpus_from_organization_v0_1 import CORPUS_PATH as ORG_CORPUS_PATH
from m6_corpus_from_supply_chain_v0_1 import CORPUS_PATH, CLAIMS_PATH, build_supply_chain_corpus
from m6_structural_learning_v0_1 import StructuralLearningPolicy, brier_score_multiclass, split_by_rule

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "corpus" / "family_tree_facts_v0_2.json"


def test_supply_chain_corpus_is_independent_third_domain():
    supply = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    org = json.loads(ORG_CORPUS_PATH.read_text(encoding="utf-8"))
    assert supply["corpus_id"] not in (family["corpus_id"], org["corpus_id"])
    supply_labels = {f[1] for f in supply["discovery_facts"]}
    family_labels = {f[1] for f in family["discovery_facts"]}
    org_labels = {f[1] for f in org["discovery_facts"]}
    assert supply_labels.isdisjoint(family_labels)
    assert supply_labels.isdisjoint(org_labels)
    assert len(supply["discovery_facts"]) == 21
    assert len(supply["evidence_facts"]) == 10


def test_supply_chain_topology_is_not_an_isomorphic_renaming_of_organization():
    """Asymmetric branching (3 workers/3 factories under Atelier_A vs 1
    worker-group/1 factory under Atelier_B, all 4 parts under Atelier_A) --
    a genuinely different graph shape, not just new labels on the
    organization corpus's uniform 2x2 structure."""
    supply = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    rattache = [f for f in supply["discovery_facts"] if f[1] == "RATTACHE_A"]
    by_atelier: dict[str, int] = {}
    for _fid, _rel, atelier, _usine in rattache:
        by_atelier[atelier] = by_atelier.get(atelier, 0) + 1
    assert sorted(by_atelier.values()) == [1, 3]


def test_supply_chain_pipeline_produces_real_m6_records_with_both_outcomes_and_two_depths():
    report = build_supply_chain_corpus()
    assert len(report.records) == 24
    assert {r.outcome for r in report.records} == {"SUPPORTED", "CONTRADICTED"}
    assert {r.depth for r in report.records} == {1, 2}
    assert len({r.rule_signature for r in report.records}) == 12


def test_supply_chain_corpus_has_non_empty_rule_holdout_and_no_claimed_perfect_transfer():
    report = build_supply_chain_corpus()
    train, val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert len(holdout) > 0
    assert {r.rule_signature for r in train}.isdisjoint({r.rule_signature for r in holdout})
    policy = StructuralLearningPolicy().fit(train)
    score = brier_score_multiclass(policy, holdout)
    assert 0.0 <= score <= 2.0
    assert score == 0.375


def test_supply_chain_corpus_is_repeatable():
    report_a = build_supply_chain_corpus()
    report_b = build_supply_chain_corpus()
    assert [r.record_id for r in report_a.records] == [r.record_id for r in report_b.records]
    assert [r.outcome for r in report_a.records] == [r.outcome for r in report_b.records]


def test_supply_chain_corpus_accounting_is_honest_no_pattern_dropped_or_double_counted():
    report = build_supply_chain_corpus()
    patterns_with_records = {r.record_id[len("supplyv1::"):].rsplit("::", 1)[0] for r in report.records}
    excluded_patterns = {msg.split(": ", 1)[0] for msg in report.excluded_no_verification_claim}
    assert patterns_with_records.isdisjoint(excluded_patterns)
    assert len(patterns_with_records) + len(excluded_patterns) == report.candidate_patterns_considered


def test_supply_chain_corpus_records_are_all_grounded_direct():
    report = build_supply_chain_corpus()
    assert all(r.provenance == "GROUNDED_DIRECT" for r in report.records)


def test_supply_chain_corpus_record_ids_do_not_collide_with_other_domain_prefixes():
    report = build_supply_chain_corpus()
    assert all(r.record_id.startswith("supplyv1::") for r in report.records)
    assert not any(r.record_id.startswith(("realv2::", "orgv1::")) for r in report.records)


def test_claims_file_is_loadable_and_has_both_agreeing_and_conflicting_endpoints():
    claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    assert any(c["claimed_object"] == "WRONG_ENDPOINT" for c in claims)
    assert any(c["claimed_object"] != "WRONG_ENDPOINT" for c in claims)
