import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from p4r_non_circular_transfer_v0_2 import run_p4r


def load(path, key):
    return json.loads(Path(path).read_text(encoding="utf-8"))[key]


F = ROOT / "corpus/family_tree_facts_v0_2.json"
O = ROOT / "corpus/organization_facts_v0_1.json"


def test_source_only_operation_freeze_and_target_generation_are_non_circular():
    family = json.loads(F.read_text(encoding="utf-8"))
    org = json.loads(O.read_text(encoding="utf-8"))
    r = run_p4r(
        family["discovery_facts"],
        org["discovery_facts"],
        [["O-E07", "PROJET_DE", "Module_D", "Projet_Q"]],
        "Direction_H",
    )
    assert r["status"]["micro_structural_transfer"] == "PASS"
    assert r["leakage_audit"]["target_operands_in_frozen_operation"] is False
    assert r["leakage_audit"]["source_path_ids_in_frozen_operation"] is False


def test_hidden_endpoint_is_absent_and_strong_gate_fails_closed():
    family = json.loads(F.read_text(encoding="utf-8"))
    org = json.loads(O.read_text(encoding="utf-8"))
    r = run_p4r(
        family["discovery_facts"],
        org["discovery_facts"],
        [["O-E07", "PROJET_DE", "Module_D", "Projet_Q"]],
        "Direction_H",
    )
    gate = r["masked_endpoint_gate"]
    assert gate["hidden_endpoint_visible_in_execution_input"] is False
    assert gate["predicted_end"] is None
    assert r["status"]["strong_endpoint_transfer"] == "OPEN_EXPECTED"
    assert r["status"]["e20d_closure"] == "OPEN"


def test_target_verification_is_not_a_dependency():
    family = json.loads(F.read_text(encoding="utf-8"))
    org = json.loads(O.read_text(encoding="utf-8"))
    r = run_p4r(
        family["discovery_facts"],
        org["discovery_facts"],
        [["O-E07", "PROJET_DE", "Module_D", "Projet_Q"]],
        "Direction_H",
    )
    assert r["discipline"]["target_verification_consulted_before_prediction"] is False
    assert r["discipline"]["hidden_endpoint_supplied_to_execution"] is False
