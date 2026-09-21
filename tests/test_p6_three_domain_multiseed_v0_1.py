"""P6.2 three-domain multi-seed stability probe tests."""
from __future__ import annotations

from p6_three_domain_multiseed_v0_1 import DEFAULT_SEEDS, run_multiseed_regression


def test_all_five_slices_present_with_ten_seeds_each():
    report = run_multiseed_regression()
    assert set(report) == {"FAMILY", "ORGANIZATION", "SUPPLY_CHAIN", "COMBINED_TWO", "COMBINED_THREE"}
    for domain_id, domain_report in report.items():
        assert len(domain_report.seeds) == len(DEFAULT_SEEDS)
        assert domain_report.domain_id == domain_id


def test_every_seed_slice_is_rule_disjoint_by_construction():
    """run_multiseed_regression() itself raises if a seed leaks a rule
    between train and holdout -- this test just confirms it completed for
    every domain without raising."""
    report = run_multiseed_regression()
    for domain_report in report.values():
        assert all(0.0 <= s.brier <= 2.0 for s in domain_report.seeds)


def test_combined_two_matches_the_already_documented_p5_dispersion():
    """Regression guard: adding the third domain to this module must not
    silently change P5's own documented combined-two dispersion
    (mean=0.444565, population std=0.107167, seeds 0-9)."""
    report = run_multiseed_regression()["COMBINED_TWO"]
    assert abs(report.brier_mean - 0.444565) < 1e-3
    assert abs(report.brier_std_population - 0.107167) < 1e-3


def test_adding_a_third_domain_changes_the_combined_dispersion_honestly():
    """Whatever direction the dispersion moves, this test only asserts that
    COMBINED_TWO and COMBINED_THREE are actually measured independently
    (not just aliases of each other) -- it does not assert which one is
    'better', since neither is a transfer claim."""
    report = run_multiseed_regression()
    two = report["COMBINED_TWO"]
    three = report["COMBINED_THREE"]
    assert two.seeds != three.seeds
    assert two.brier_mean != three.brier_mean
