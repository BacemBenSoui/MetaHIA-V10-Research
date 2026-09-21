"""P7 four-domain regression tests."""
from __future__ import annotations

from m1_m6_interface_v0_2 import interface_manifest_v0_2
from p7_four_domain_regression_v0_1 import run_p7_regression


def test_stable_interface_json_roundtrip_preserves_learning_payload_for_all_domains():
    report = run_p7_regression()
    assert report.family.interface_roundtrip_ok
    assert report.organization.interface_roundtrip_ok
    assert report.supply_chain.interface_roundtrip_ok
    assert report.library.interface_roundtrip_ok
    assert report.combined_four.interface_roundtrip_ok


def test_prior_domain_baselines_are_unchanged_by_adding_a_fourth_domain():
    """The already-adopted P5/P6 baselines must not shift just because a
    fourth domain is measured alongside them -- each domain's own split is
    computed independently of the others."""
    report = run_p7_regression()
    assert report.family.brier == 0.48125
    assert report.organization.brier == 0.6953125
    assert report.supply_chain.brier == 0.375


def test_library_regression_has_nonempty_rule_holdout_and_expected_baseline():
    report = run_p7_regression().library
    assert report.records == 20
    assert report.rules == 10
    assert report.train == 12
    assert report.holdout > 0
    assert report.brier == 0.375


def test_combined_four_regression_is_rule_disjoint():
    report = run_p7_regression().combined_four
    assert report.records == 94
    assert report.rules == 54
    assert 0.0 <= report.brier <= 2.0
    assert 0.0 <= report.ece <= 1.0


def test_p7_does_not_depend_on_m7():
    assert run_p7_regression().m7_dependency_detected is False


def test_interface_version_is_still_v0_2():
    manifest = interface_manifest_v0_2()
    assert manifest["version"] == "0.2"
    assert run_p7_regression().interface_version == "0.2"
