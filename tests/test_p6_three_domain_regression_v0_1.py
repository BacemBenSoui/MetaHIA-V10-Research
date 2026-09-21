"""P6 three-domain regression tests."""
from __future__ import annotations

from m1_m6_interface_v0_2 import interface_manifest_v0_2
from p6_three_domain_regression_v0_1 import run_p6_regression


def test_stable_interface_json_roundtrip_preserves_learning_payload_for_all_domains():
    report = run_p6_regression()
    assert report.family.interface_roundtrip_ok
    assert report.organization.interface_roundtrip_ok
    assert report.supply_chain.interface_roundtrip_ok
    assert report.combined_three.interface_roundtrip_ok


def test_family_and_organization_baselines_are_unchanged_by_adding_a_third_domain():
    """The already-adopted P5 baselines must not shift just because a third
    domain is measured alongside them -- each domain's own split is computed
    independently of the others."""
    report = run_p6_regression()
    assert report.family.brier == 0.48125
    assert report.organization.brier == 0.6953125


def test_supply_chain_regression_has_nonempty_rule_holdout_and_expected_baseline():
    report = run_p6_regression().supply_chain
    assert report.records == 24
    assert report.rules == 12
    assert report.train == 16
    assert report.holdout > 0
    assert report.brier == 0.375


def test_combined_three_regression_is_rule_disjoint():
    report = run_p6_regression().combined_three
    assert report.records == 74
    assert report.rules == 44
    assert 0.0 <= report.brier <= 2.0
    assert 0.0 <= report.ece <= 1.0


def test_p6_does_not_depend_on_m7():
    assert run_p6_regression().m7_dependency_detected is False


def test_interface_version_is_still_v0_2():
    manifest = interface_manifest_v0_2()
    assert manifest["version"] == "0.2"
    assert run_p6_regression().interface_version == "0.2"
