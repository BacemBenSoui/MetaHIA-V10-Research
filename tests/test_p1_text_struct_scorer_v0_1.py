"""Tests for the H-P1-TEXT-STRUCT scorer (validation/p1_text_struct/scorer.py). No Core, no verdict."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "p1_text_struct_scorer", Path(__file__).resolve().parents[1] / "validation" / "p1_text_struct" / "scorer.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

GOLD = ["neg", ["in", ["run", "man"], "park"]]


def test_exact_match_scores_perfectly():
    s = S.score_item(GOLD, GOLD)
    assert s["exact"] and s["negation_scope_match"]
    assert s["arguments"]["f1"] == s["roles"]["f1"] == s["heads"]["f1"] == 1.0


def test_lost_negation_is_caught_even_when_arguments_are_right():
    s = S.score_item(["in", ["run", "man"], "park"], GOLD)
    assert not s["exact"] and not s["negation_count_match"] and not s["negation_scope_match"]
    assert s["arguments"]["f1"] == 1.0


def test_negation_at_the_wrong_scope_is_caught():
    s = S.score_item(["in", ["neg", ["run", "man"]], "park"], GOLD)
    assert s["negation_count_match"] and not s["negation_scope_match"]


def test_swapped_roles_are_caught_even_with_identical_leaves():
    s = S.score_item(["bite", "man", "dog"], ["bite", "dog", "man"])
    assert s["arguments"]["f1"] == 1.0 and s["roles"]["f1"] < 1.0


def test_unnormalised_head_is_caught():
    s = S.score_item(["running", "man"], ["run", "man"])
    assert s["heads"]["f1"] == 0.0 and s["arguments"]["f1"] == 1.0


def test_abstention_accounting():
    agg = S.aggregate([S.score_item(None, GOLD), S.score_item(GOLD, GOLD), S.score_item(None, None), S.score_item(GOLD, None)])
    assert agg["abstention_rate_in_convention"] == 0.5
    assert agg["correct_abstention_rate_out_of_convention"] == 0.5
    assert agg["exact_rate_answered"] == 1.0


def test_resource_audit_rejects_semantic_knowledge():
    assert S.audit_resources({"determiners": [], "suffix_rules": []}) == []
    problems = S.audit_resources({"synonyms": [], "city_gazetteer": []})
    assert len(problems) >= 3
