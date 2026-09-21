"""Independent fourth-domain corpus validation v0.1."""
from __future__ import annotations

import json
from pathlib import Path

from m6_corpus_from_organization_v0_1 import CORPUS_PATH as ORG_CORPUS_PATH
from m6_corpus_from_supply_chain_v0_1 import CORPUS_PATH as SUPPLY_CORPUS_PATH
from m6_corpus_from_library_v0_1 import CORPUS_PATH, CLAIMS_PATH, build_library_corpus
from m6_structural_learning_v0_1 import StructuralLearningPolicy, brier_score_multiclass, split_by_rule

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "corpus" / "family_tree_facts_v0_2.json"


def test_library_corpus_is_independent_fourth_domain():
    library = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    org = json.loads(ORG_CORPUS_PATH.read_text(encoding="utf-8"))
    supply = json.loads(SUPPLY_CORPUS_PATH.read_text(encoding="utf-8"))
    assert library["corpus_id"] not in (family["corpus_id"], org["corpus_id"], supply["corpus_id"])
    library_labels = {f[1] for f in library["discovery_facts"]}
    for other in (family, org, supply):
        assert library_labels.isdisjoint({f[1] for f in other["discovery_facts"]})
    assert len(library["discovery_facts"]) == 17
    assert len(library["evidence_facts"]) == 8


def test_library_topology_is_not_an_isomorphic_renaming_of_any_prior_domain():
    """Uneven author/publisher branching (2/1/3 books per author, 2/1
    authors per publisher) -- a different shape from both organization's
    uniform 2x2 and supply chain's single-branch concentration."""
    library = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    ecrit = [f for f in library["discovery_facts"] if f[1] == "ECRIT_PAR"]
    by_author: dict[str, int] = {}
    for _fid, _rel, _livre, auteur in ecrit:
        by_author[auteur] = by_author.get(auteur, 0) + 1
    assert sorted(by_author.values()) == [1, 2, 3]

    publie = [f for f in library["discovery_facts"] if f[1] == "PUBLIE_CHEZ"]
    by_publisher: dict[str, int] = {}
    for _fid, _rel, _auteur, editeur in publie:
        by_publisher[editeur] = by_publisher.get(editeur, 0) + 1
    assert sorted(by_publisher.values()) == [1, 2]


def test_library_pipeline_produces_real_m6_records_with_both_outcomes_and_two_depths():
    report = build_library_corpus()
    assert len(report.records) == 20
    assert {r.outcome for r in report.records} == {"SUPPORTED", "CONTRADICTED"}
    assert {r.depth for r in report.records} == {1, 2}
    assert len({r.rule_signature for r in report.records}) == 10


def test_library_corpus_has_non_empty_rule_holdout_and_no_claimed_perfect_transfer():
    report = build_library_corpus()
    train, val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert len(holdout) > 0
    assert {r.rule_signature for r in train}.isdisjoint({r.rule_signature for r in holdout})
    policy = StructuralLearningPolicy().fit(train)
    score = brier_score_multiclass(policy, holdout)
    assert 0.0 <= score <= 2.0
    assert score == 0.375


def test_library_corpus_is_repeatable():
    report_a = build_library_corpus()
    report_b = build_library_corpus()
    assert [r.record_id for r in report_a.records] == [r.record_id for r in report_b.records]
    assert [r.outcome for r in report_a.records] == [r.outcome for r in report_b.records]


def test_library_corpus_accounting_is_honest_no_pattern_dropped_or_double_counted():
    report = build_library_corpus()
    patterns_with_records = {r.record_id[len("libraryv1::"):].rsplit("::", 1)[0] for r in report.records}
    excluded_patterns = {msg.split(": ", 1)[0] for msg in report.excluded_no_verification_claim}
    assert patterns_with_records.isdisjoint(excluded_patterns)
    assert len(patterns_with_records) + len(excluded_patterns) == report.candidate_patterns_considered


def test_library_corpus_records_are_all_grounded_direct():
    report = build_library_corpus()
    assert all(r.provenance == "GROUNDED_DIRECT" for r in report.records)


def test_library_corpus_record_ids_do_not_collide_with_other_domain_prefixes():
    report = build_library_corpus()
    assert all(r.record_id.startswith("libraryv1::") for r in report.records)
    assert not any(r.record_id.startswith(("realv2::", "orgv1::", "supplyv1::")) for r in report.records)


def test_claims_file_is_loadable_and_has_both_agreeing_and_conflicting_endpoints():
    claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))["claims"]
    assert any(c["claimed_object"] == "WRONG_ENDPOINT" for c in claims)
    assert any(c["claimed_object"] != "WRONG_ENDPOINT" for c in claims)
