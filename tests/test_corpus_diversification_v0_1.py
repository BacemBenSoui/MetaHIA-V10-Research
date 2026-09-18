"""Independent second-domain corpus validation v0.1."""
from __future__ import annotations

import json
from pathlib import Path

from m6_corpus_from_organization_v0_1 import CORPUS_PATH, CLAIMS_PATH, build_organization_corpus
from m6_structural_learning_v0_1 import StructuralLearningPolicy, brier_score_multiclass, split_by_rule

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "corpus" / "family_tree_facts_v0_2.json"


def test_organization_corpus_is_independent_second_domain():
    org = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    assert org["corpus_id"] != family["corpus_id"]
    org_labels = {f[1] for f in org["discovery_facts"]}
    family_labels = {f[1] for f in family["discovery_facts"]}
    assert org_labels.isdisjoint(family_labels)
    assert len(org["discovery_facts"]) == 18
    assert len(org["evidence_facts"]) == 10


def test_organization_pipeline_produces_real_m6_records_with_both_outcomes_and_two_depths():
    report = build_organization_corpus()
    assert report.candidate_patterns_considered == 27
    assert len(report.records) == 24
    assert len(report.excluded_no_verification_claim) == 15
    assert {r.outcome for r in report.records} == {"SUPPORTED", "CONTRADICTED"}
    assert {r.depth for r in report.records} == {1, 2}
    assert len({r.rule_signature for r in report.records}) == 12


def test_organization_corpus_has_non_empty_rule_holdout_and_no_claimed_perfect_transfer():
    report = build_organization_corpus()
    train, val, holdout = split_by_rule(report.records, val_fraction=0.2, holdout_fraction=0.2, seed=0)
    assert len(train) == 16
    assert len(val) == 4
    assert len(holdout) == 4
    assert {r.rule_signature for r in train}.isdisjoint({r.rule_signature for r in holdout})
    policy = StructuralLearningPolicy().fit(train)
    score = brier_score_multiclass(policy, holdout)
    assert 0.0 <= score <= 2.0
    assert score == 0.6953125


def test_organization_corpus_is_repeatable():
    """Same inputs, same outputs -- no hidden nondeterminism (e.g. dict/set
    iteration order) in the corpus builder."""
    report_a = build_organization_corpus()
    report_b = build_organization_corpus()
    assert [r.record_id for r in report_a.records] == [r.record_id for r in report_b.records]
    assert [r.outcome for r in report_a.records] == [r.outcome for r in report_b.records]


def test_organization_corpus_accounting_is_honest_no_pattern_dropped_or_double_counted():
    """Every candidate pattern either produced at least one record or was
    explicitly excluded -- never neither (silently dropped) and never both
    (double-counted). Mirrors the same check already applied to the
    family-tree v0.2 mechanism (test_c07 in test_m6_v0_2_critical_validation_v0_1.py),
    after a real accounting bug was once found there."""
    report = build_organization_corpus()
    patterns_with_records = {r.record_id[len("orgv1::"):].rsplit("::", 1)[0] for r in report.records}
    excluded_patterns = {msg.split(": ", 1)[0] for msg in report.excluded_no_verification_claim}
    assert patterns_with_records.isdisjoint(excluded_patterns)
    assert len(patterns_with_records) + len(excluded_patterns) == report.candidate_patterns_considered


def test_organization_corpus_records_are_all_grounded_direct():
    report = build_organization_corpus()
    assert all(r.provenance == "GROUNDED_DIRECT" for r in report.records)


def test_organization_corpus_record_ids_do_not_collide_with_family_tree_v0_2_prefix():
    """Regression guard for a real naming bug found during review 2026-09-18:
    the corpus builder originally reused m6_corpus_from_m4_m5_v0_2.py's
    "realv2::" record_id prefix, which would make organization and
    family-tree records indistinguishable if ever combined into one mixed
    corpus (a scenario this module's own docstring anticipates: "transfer
    validation" across domains)."""
    report = build_organization_corpus()
    assert all(r.record_id.startswith("orgv1::") for r in report.records)
    assert not any(r.record_id.startswith("realv2::") for r in report.records)
