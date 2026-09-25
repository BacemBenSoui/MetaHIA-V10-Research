"""Development tests for P1-TEXT-STRUCT gateway A (validation/p1_text_struct/gateway_a.py).

DEVELOPMENT ONLY: every expected structure here was written by the gateway developer on dev material;
none is an independent gold and none of these results is an experimental measure.
"""
import ast
import importlib.util
import json
from pathlib import Path

import pytest

_DIR = Path(__file__).resolve().parents[1] / "validation" / "p1_text_struct"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"p1ts_{name}", _DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GW, AUDIT, GOLD = _load("gateway_a"), _load("compliance_audit"), _load("gold_tools")
SOURCE = (_DIR / "gateway_a.py").read_text(encoding="utf-8")
DEV = [json.loads(line) for line in (_DIR / "dev_corpus.jsonl").read_text(encoding="utf-8").splitlines()]
parse = GW.parse


# ------------------------------------------------------------------ dev corpus (development expectations)

@pytest.mark.parametrize("item", DEV, ids=[d["id"] for d in DEV])
def test_dev_corpus(item):
    expected = item["expected_convention"] if item["gateway_policy"] == "structure" else None
    assert parse(item["sentence"]) == expected


# ------------------------------------------------------------------ mandatory cases (mandate section 5)

@pytest.mark.parametrize("sentence,expected", [
    ("The man sleeps.", ["sleep", "man"]),                                              # active simple
    ("The farmer feeds the horse.", ["feed", "farmer", "horse"]),                       # active with object
    ("The horse was fed by the farmer.", ["feed", "farmer", "horse"]),                  # passive with by
    ("The woman had been helped by the nurse.", ["help", "nurse", "woman"]),
    ("The girl will be reading.", ["read", "girl"]),                                    # tense/aspect/aux removed
    ("The girl was reading.", ["read", "girl"]),
    ("The lamp is bright.", ["attr", "lamp", "bright"]),                                # attribute
    ("A tall tree fell.", ["fall", ["attr", "tree", "tall"]]),                          # epithet
    ("The boy hides behind the door.", ["behind", ["hide", "boy"], "door"]),            # place
    ("The boy quietly closed the door.", ["quietly", ["close", "boy", "door"]]),        # manner
    ("The rain stopped after lunch.", ["after", ["stop", "rain"], "lunch"]),            # time
    ("The pilot is not flying.", ["neg", ["fly", "pilot"]]),                            # not
    ("The pilot never flies the plane.", ["neg", ["fly", "pilot", "plane"]]),           # never
    ("No birds are singing.", ["neg", ["sing", "bird"]]),                               # determiner negation
    ("Four cats sleep.", None),                                                         # base verb after plural: abstain
    ("Four cats slept.", ["sleep", ["card", "cat", "4"]]),                              # cardinal
    ("Every guest smiled.", ["smile", ["q_all", "guest"]]),                             # quantifiers
    ("Several guests smiled.", ["smile", ["q_some", "guest"]]),
    ("A few guests smiled.", ["smile", ["q_some", "guest"]]),
    ("The mayor gave a speech.", ["give", "mayor", "speech"]),                          # R13 no idiom
    ("The sofa hides the cat.", ["hide", "sofa", "cat"]),                               # R14 synonyms kept
    ("The couch hides the cat.", ["hide", "couch", "cat"]),
])
def test_mandatory_case(sentence, expected):
    assert parse(sentence) == expected


# ------------------------------------------------------------------ addendum GEL 1-bis (A1-A4)

def test_a1_participle_after_copula_is_passive_even_without_by():
    assert parse("The letter was signed.") == ["sign", "_", "letter"]
    assert parse("The door is open.") == ["attr", "door", "open"]  # adjective: R4


def test_a2_negative_subject_is_neg_over_reserved_agent():
    assert parse("Nobody opened the gate.") == ["neg", ["open", "_", "gate"]]
    assert parse("Nothing broke the window.") == ["neg", ["break", "_", "window"]]
    assert parse("The man saw nobody.") is None  # subject position only
    assert parse("No one opened the gate.") is None  # not covered by A2


def test_a3_possessives_are_never_deleted_silently():
    assert parse("Her brother opened the gate.") is None
    assert parse("The man opened their gate.") is None


def test_a4_deictic_adverbs_exactly_four():
    assert parse("The boy crossed the bridge yesterday.") == ["yesterday", ["cross", "boy", "bridge"]]
    assert parse("Tonight the baker closes the shop.") == ["tonight", ["close", "baker", "shop"]]
    assert set(GW.DEICTIC_ADVERBS) == {"yesterday", "today", "now", "tonight"}
    assert parse("Tomorrow the baker closes the shop.") is None  # not in the closed class


# ------------------------------------------------------------------ adversarial cases (mandate section 5)

def test_inverted_roles_give_different_structures():
    assert parse("The goat pushed the farmer.") == ["push", "goat", "farmer"]
    assert parse("The farmer pushed the goat.") == ["push", "farmer", "goat"]


def test_passive_agent_is_not_swapped():
    assert parse("The farmer was pushed by the goat.") == ["push", "goat", "farmer"]


def test_plural_and_irregular_forms_are_normalised():
    assert parse("The dogs chased the cats.") == ["chase", "dog", "cat"]
    assert parse("The men ran.") == ["run", "man"]
    assert parse("The children ate the apples.") == ["eat", "child", "apple"]


def test_adjunct_order_does_not_change_the_structure():
    a = parse("The cat slept under the table during the storm.")
    b = parse("The cat slept during the storm under the table.")
    assert a == b == ["during", ["under", ["sleep", "cat"], "table"], "storm"]


@pytest.mark.parametrize("sentence", [
    "The cat ate and the dog slept.",          # coordination
    "Did the bus stop?",                       # question
    "The man who sang left.",                  # subordinate (relative)
    "The girl smiled because the sun rose.",   # subordinate (causal)
    "The man, tired, slept.",                  # punctuation not covered
    "His dog barked.",                         # possessive not covered
])
def test_out_of_convention_is_null(sentence):
    assert parse(sentence) is None


def test_negation_is_never_placed_on_an_argument():
    outputs = [parse(d["sentence"]) for d in DEV]
    for tree in outputs:
        assert GOLD.convention_problems(tree) == [], tree


# ------------------------------------------------------------------ invariants

def test_gateway_is_deterministic():
    assert [parse(d["sentence"]) for d in DEV] == [parse(d["sentence"]) for d in DEV]


def test_gateway_never_calls_the_core_nor_produces_a_verdict():
    tree = ast.parse(SOURCE)
    modules = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    modules |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not any(m.startswith(("kernel2", "verification", "metahia")) for m in modules), modules
    for verdict in ("SUPPORTED", "CONTRADICTED", "UNKNOWN"):
        assert verdict not in SOURCE


def test_gateway_passes_the_compliance_audit():
    assert AUDIT.audit_gateway(_DIR / "gateway_a.py", {"gateway_a.py"}) == []


# ------------------------------------------------------------------ non-contamination (mandate section 7)

@pytest.mark.parametrize("injection,expected", [
    ("SYNONYMS = {'lawyer': 'attorney'}", "semantic"),                         # synonym table
    ("ENTITY_LIST = {'oslo', 'cairo', 'paris'}", "semantic"),                  # entity list
    ("import spacy", "allowlist"),                                              # statistical parser
    ("import os", "allowlist"),                                                 # forbidden I/O module
    ("LEXICON = open('lexicon.txt').read().split()", "forbidden"),             # external lexicon
])
def test_contaminated_gateway_fails_the_audit(injection, expected):
    problems = AUDIT.audit_source(SOURCE + "\n" + injection + "\n")
    assert any(expected in p for p in problems), problems
