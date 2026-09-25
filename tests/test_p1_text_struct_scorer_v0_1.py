"""Tests for P1-TEXT-STRUCT v0 tooling: scorer, compliance audit, gold tools. No Core, no verdict."""
import importlib.util
from pathlib import Path

import pytest

_DIR = Path(__file__).resolve().parents[1] / "validation" / "p1_text_struct"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"p1ts_{name}", _DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S, A, G = _load("scorer"), _load("compliance_audit"), _load("gold_tools")
GOLD = ["neg", ["in", ["run", "man"], "park"]]


# ------------------------------------------------------------------ scorer

def test_exact_match_passes_every_gate():
    s = S.score_item(GOLD, GOLD)
    assert s["exact"] and s["gate_negation_preserved"] and s["gate_negation_scope"] and s["gate_roles_preserved"]


def test_lost_negation_fails_the_gate():
    s = S.score_item(["in", ["run", "man"], "park"], GOLD)
    assert not s["gate_negation_preserved"] and not s["gate_negation_scope"]


def test_negation_moved_to_an_argument_fails_scope():
    s = S.score_item(["in", ["run", ["neg", "man"]], "park"], ["in", ["neg", ["run", "man"]], "park"])
    assert s["gate_negation_preserved"] and not s["gate_negation_scope"]


def test_swapped_roles_fail_the_gate():
    assert not S.score_item(["bite", "man", "dog"], ["bite", "dog", "man"])["gate_roles_preserved"]


def test_head_morphology_error_is_not_a_role_or_scope_fault():
    s = S.score_item(["neg", ["running", "man"]], ["neg", ["run", "man"]])
    assert not s["exact"] and s["gate_roles_preserved"] and s["gate_negation_scope"]
    assert s["heads"]["f1"] < 1.0


def test_abstention_never_raises_headline_exactness():
    agg = S.aggregate([S.score_item(None, GOLD), S.score_item(GOLD, GOLD)], bootstrap_n=200)
    assert agg["exact_in_convention"] == 0.5 and agg["exact_answered"] == 1.0
    assert agg["coverage_in_convention"] == 0.5 and agg["exact_in_convention_ci95"] is not None


def test_gates_pass_only_when_every_answered_item_passes():
    good = S.aggregate([S.score_item(GOLD, GOLD)], bootstrap_n=50)
    bad = S.aggregate([S.score_item(GOLD, GOLD), S.score_item(["bite", "man", "dog"], ["bite", "dog", "man"])], bootstrap_n=50)
    assert good["safety_gates_pass"] and not bad["safety_gates_pass"]


# ------------------------------------------------------------------ compliance audit (system check, not scorer)

COMPLIANT = '''
import re
RESOURCES = {"DETERMINERS": "determiners", "IRREGULAR": "irregular_forms"}
DETERMINERS = {"the", "a", "an"}
IRREGULAR = {"ran": "run", "children": "child"}
def parse(text):
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in DETERMINERS]
'''


def test_compliant_gateway_passes():
    assert A.audit_source(COMPLIANT) == []


@pytest.mark.parametrize("snippet,expected", [
    ("SYNONYMS = {'lawyer': 'attorney'}", "semantic"),                # hidden lexical knowledge
    ("OSLO_CAIRO = {'oslo', 'cairo'}", "undeclared"),                  # undeclared word list
    ("import spacy", "allowlist"),                                     # statistical model
    ("import os", "allowlist"),                                        # file system access
    ("DATA = open('lexicon.txt').read()", "forbidden"),                # resource loaded at runtime
])
def test_non_compliant_gateways_fail(snippet, expected):
    problems = A.audit_source(COMPLIANT + "\n" + snippet + "\n")
    assert any(expected in p for p in problems), problems


def test_forbidden_category_in_manifest_fails():
    source = COMPLIANT.replace('"IRREGULAR": "irregular_forms"', '"IRREGULAR": "antonym_pairs"')
    assert any("not permitted" in p for p in A.audit_source(source))


# ------------------------------------------------------------------ gold tools

def test_notation_round_trip():
    tree = G.parse_notation("neg(in(run(man), park))")
    assert tree == GOLD and G.parse_notation(G.to_notation(tree)) == GOLD
    assert G.parse_notation("none") is None


def test_convention_checks():
    assert G.convention_problems(GOLD) == []
    assert any("outermost" in p for p in G.convention_problems(["in", ["neg", ["run", "man"]], "park"]))
    assert any("expects" in p for p in G.convention_problems(["attr", "door"]))
    assert any("number" in p for p in G.convention_problems(["play", ["card", "boy", "two"]]))


def test_double_annotation_disagreements():
    report = G.compare_annotations({"H1": GOLD, "H2": None}, {"H1": GOLD, "H2": ["run", "man"]})
    assert report["agreement"] == 0.5 and report["to_adjudicate"] == ["H2"]
