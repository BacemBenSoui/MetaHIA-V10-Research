"""P5 stable M1-M6 interface and multi-domain regression tests."""
from __future__ import annotations

from m1_m6_interface_v0_2 import M1M6StableEnvelope, interface_manifest_v0_2
from p5_m1_m6_multidomain_regression_v0_1 import run_p5_regression


def test_stable_interface_is_versioned_and_excludes_m7():
    manifest = interface_manifest_v0_2()
    assert manifest["version"] == "0.2"
    assert manifest["modules"] == ("M1", "M2", "M3", "M4", "M5", "M6")
    assert manifest["excluded_dependency"] == "M7"
    assert manifest["domain_metadata_reaches_m6"] is False


def test_stable_interface_json_roundtrip_preserves_learning_payload():
    report = run_p5_regression()
    assert report.family.interface_roundtrip_ok
    assert report.organization.interface_roundtrip_ok
    assert report.combined.interface_roundtrip_ok


def test_family_regression_has_nonempty_rule_holdout_and_expected_baseline():
    report = run_p5_regression().family
    assert report.records == 26
    assert report.rules == 20
    assert report.train == 16
    assert report.validation == 5
    assert report.holdout == 5
    assert report.holdout_rules == 4
    assert report.brier == 0.48125


def test_organization_regression_has_nonempty_rule_holdout_and_expected_baseline():
    report = run_p5_regression().organization
    assert report.records == 24
    assert report.rules == 12
    assert report.train == 16
    assert report.validation == 4
    assert report.holdout == 4
    assert report.holdout_rules == 2
    assert report.brier == 0.6953125


def test_combined_regression_is_rule_disjoint_and_stable():
    report = run_p5_regression().combined
    assert report.records == 50
    assert report.rules == 32
    assert report.train == 31
    assert report.validation == 9
    assert report.holdout == 10
    assert report.holdout_rules == 6
    assert 0.0 <= report.brier <= 2.0
    assert 0.0 <= report.ece <= 1.0


def test_p5_does_not_depend_on_m7():
    assert run_p5_regression().m7_dependency_detected is False


def test_stable_envelope_is_not_a_new_learning_feature():
    report = run_p5_regression().family
    assert report.interface_roundtrip_ok
    manifest = interface_manifest_v0_2()
    assert manifest["learning_payload_fields"] == (
        "record_id", "rule", "novelty", "redundancy", "depth", "provenance", "outcome"
    )

