import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "cli_preprod_v0_1.py"


def _run(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_manifest_excludes_m7_and_names_the_basis_limitation():
    code, out, _err = _run("manifest")
    assert code == 0
    payload = json.loads(out)
    assert payload["m7_excluded"] is True
    assert "BASIS_EXACT_BUCKET" in payload["known_limitation"]
    assert "global class-frequency" in payload["known_limitation"]


def test_list_records_returns_every_domain_record():
    code, out, _err = _run("list-records", "--domain", "organization")
    assert code == 0
    payload = json.loads(out)
    assert payload["record_count"] == 24
    assert len(payload["records"]) == 24
    assert all("record_id" in r and "outcome" in r for r in payload["records"])


def test_regression_matches_the_already_validated_family_baseline():
    code, out, _err = _run("regression", "--domain", "family")
    assert code == 0
    payload = json.loads(out)
    assert payload["records"] == 26
    assert payload["rules"] == 20
    assert payload["holdout_rules_disjoint_from_train"] is True
    assert abs(payload["brier_holdout"] - 0.48125) < 1e-9


def test_regression_matches_the_already_validated_organization_baseline():
    code, out, _err = _run("regression", "--domain", "organization")
    assert code == 0
    payload = json.loads(out)
    assert payload["records"] == 24
    assert payload["rules"] == 12
    assert abs(payload["brier_holdout"] - 0.6953125) < 1e-9


def test_regression_matches_the_already_validated_supply_chain_baseline():
    code, out, _err = _run("regression", "--domain", "supply_chain")
    assert code == 0
    payload = json.loads(out)
    assert payload["records"] == 24
    assert payload["rules"] == 12
    assert abs(payload["brier_holdout"] - 0.375) < 1e-9


def test_regression_matches_the_already_validated_library_baseline():
    code, out, _err = _run("regression", "--domain", "library")
    assert code == 0
    payload = json.loads(out)
    assert payload["records"] == 20
    assert payload["rules"] == 10
    assert abs(payload["brier_holdout"] - 0.375) < 1e-9


def test_regression_combined_matches_the_already_validated_p7_four_domain_baseline():
    """combined's own definition evolves as REAL_DOMAINS grows -- it always
    means 'everything currently known' (see cli_preprod_v0_1.py's comment),
    so this test intentionally supersedes the earlier three-domain
    assertion rather than adding a parallel one."""
    code, out, _err = _run("regression", "--domain", "combined")
    assert code == 0
    payload = json.loads(out)
    assert payload["records"] == 94
    assert payload["rules"] == 54
    assert abs(payload["brier_holdout"] - 0.37540049839800665) < 1e-9
    assert payload["corpus_id"] == "FAMILY-TREE-V0.2+ORGANIZATION-V0.1+SUPPLY-CHAIN-V0.1+LIBRARY-V0.1"


def test_manifest_lists_combined_and_names_it_is_not_a_transfer_claim():
    code, out, _err = _run("manifest")
    assert code == 0
    payload = json.loads(out)
    assert "combined" in payload["domains_available"]
    assert "NOT a cross-domain transfer claim" in payload["combined_domain_caveat"]


def test_list_records_combined_pools_all_four_real_domains():
    code, out, _err = _run("list-records", "--domain", "combined")
    assert code == 0
    payload = json.loads(out)
    assert payload["record_count"] == 94
    prefixes = {r["record_id"].split("::", 1)[0] for r in payload["records"]}
    assert prefixes == {"realv2", "orgv1", "supplyv1", "libraryv1"}


def test_predict_never_hides_its_own_basis_and_matches_actual_for_a_known_record():
    code, out, _err = _run("list-records", "--domain", "organization")
    records = json.loads(out)["records"]
    known = records[0]
    code, out, _err = _run(
        "predict", "--domain", "organization", "--record-id", known["record_id"]
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["basis"] in ("EXACT_BUCKET", "RULE_ONLY", "GLOBAL_PRIOR", "UNIFORM_NO_DATA")
    assert payload["actual_outcome"] == known["outcome"]
    assert "predicted_distribution" in payload


def test_predict_fails_closed_on_unknown_record_id():
    code, _out, err = _run("predict", "--domain", "family", "--record-id", "does-not-exist")
    assert code != 0
    assert "not found" in err


def test_predict_on_a_genuine_holdout_record_reports_global_prior_basis():
    code, out, _err = _run("regression", "--domain", "family")
    assert code == 0
    basis_dist = json.loads(out)["basis_distribution_over_holdout"]
    assert set(basis_dist) == {"GLOBAL_PRIOR"}
    code, out, _err = _run("list-records", "--domain", "family")
    records = json.loads(out)["records"]
    found_holdout_basis = False
    for r in records:
        code, out, _err = _run(
            "predict", "--domain", "family", "--record-id", r["record_id"]
        )
        assert code == 0
        payload = json.loads(out)
        if payload["was_in_holdout_for_this_seed"]:
            assert payload["basis"] == "GLOBAL_PRIOR"
            found_holdout_basis = True
    assert found_holdout_basis
