"""P5.2 multi-seed stability probe tests."""
from __future__ import annotations

from p5_multiseed_regression_v0_1 import run_multiseed_regression


def test_multiseed_uses_nonempty_rule_disjoint_holdouts_for_all_domains():
    report = run_multiseed_regression(range(10))
    for domain in report.values():
        assert len(domain.seeds) == 10
        assert all(item.holdout > 0 for item in domain.seeds)
        assert all(item.holdout_rules > 0 for item in domain.seeds)
        assert all(item.brier >= 0.0 for item in domain.seeds)
        assert all(item.brier <= 2.0 for item in domain.seeds)
        assert all(item.ece >= 0.0 for item in domain.seeds)
        assert all(item.ece <= 1.0 for item in domain.seeds)


def test_multiseed_explicitly_reports_dispersion_rather_than_declaring_metric_stability():
    report = run_multiseed_regression(range(10))
    assert report["FAMILY"].brier_max > report["FAMILY"].brier_min
    assert report["ORGANIZATION"].brier_max > report["ORGANIZATION"].brier_min
    assert report["COMBINED"].brier_max > report["COMBINED"].brier_min
    assert report["FAMILY"].brier_std_population > 0.0
    assert report["ORGANIZATION"].brier_std_population > 0.0
    assert report["COMBINED"].brier_std_population > 0.0


def test_multiseed_does_not_change_the_seed_zero_baseline():
    report = run_multiseed_regression(range(10))
    family_seed0 = next(item for item in report["FAMILY"].seeds if item.seed == 0)
    org_seed0 = next(item for item in report["ORGANIZATION"].seeds if item.seed == 0)
    combined_seed0 = next(item for item in report["COMBINED"].seeds if item.seed == 0)
    assert family_seed0.brier == 0.48125
    assert org_seed0.brier == 0.6953125
    assert combined_seed0.brier == 0.49198751300728405
