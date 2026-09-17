from kernel2 import Node, NodeRef, OBSERVATION
from e20d_operator_relation_v0_1 import (
    discover_operator_relation,
    mapping_relation_fact,
    build_operator_from_discovered_relation,
)
from operator_space_v0_1 import operator_profile, build_composed_operator


def obs(i, op, a, b):
    return Node(i, OBSERVATION, (NodeRef(op), NodeRef(a), NodeRef(b)))


def test_identity_operator_relation_is_discovered():
    pairs = [
        (obs("s1", "+", "a1", "b1"), obs("t1", "+", "a1", "b1")),
        (obs("s2", "+", "a2", "b2"), obs("t2", "+", "a2", "b2")),
        (obs("s3", "+", "a3", "b3"), obs("t3", "+", "a3", "b3")),
    ]
    d = discover_operator_relation(pairs)
    assert not d.contradictions
    assert len(d.candidates) == 1
    assert d.candidates[0].source_operator.ref_id == "+"
    assert d.candidates[0].target_operator.ref_id == "+"


def test_nontrivial_operator_mapping_is_discovered():
    pairs = [
        (obs("s1", "+", "a1", "b1"), obs("t1", "*", "a1", "b1")),
        (obs("s2", "+", "a2", "b2"), obs("t2", "*", "a2", "b2")),
        (obs("s3", "+", "a3", "b3"), obs("t3", "*", "a3", "b3")),
    ]
    d = discover_operator_relation(pairs)
    c = d.candidates[0]
    assert c.source_operator.ref_id == "+"
    assert c.target_operator.ref_id == "*"


def test_contradictory_mapping_fails_closed():
    pairs = [
        (obs("s1", "+", "a1", "b1"), obs("t1", "*", "a1", "b1")),
        (obs("s2", "+", "a2", "b2"), obs("t2", "/", "a2", "b2")),
        (obs("s3", "+", "a3", "b3"), obs("t3", "*", "a3", "b3")),
    ]
    d = discover_operator_relation(pairs)
    assert len(d.candidates) == 1
    assert d.candidates[0].target_operator.ref_id == "*"
    assert len(d.contradictions) == 1


def test_mapping_fact_is_structural_not_semantic():
    c = discover_operator_relation([
        (obs("s1", "O1", "a", "b"), obs("t1", "O2", "a", "b")),
        (obs("s2", "O1", "c", "d"), obs("t2", "O2", "c", "d")),
        (obs("s3", "O1", "e", "f"), obs("t3", "O2", "e", "f")),
    ]).candidates[0]
    fact = mapping_relation_fact(c)
    assert fact.children[0] == NodeRef("O1")
    assert fact.children[1] == NodeRef("O2")
    assert fact.children[2] == NodeRef("OPERATOR_MAPPING")


def test_discovered_relation_feeds_existing_operator_space():
    p1 = operator_profile("+", arity=2, properties=["COMMUTATIVE", "ADDITIVE"])
    p2 = operator_profile("*", arity=2, properties=["COMMUTATIVE", "ITERATIVE"])
    c = discover_operator_relation([
        (obs("s1", "+", "a1", "b1"), obs("t1", "*", "a1", "b1")),
        (obs("s2", "+", "a2", "b2"), obs("t2", "*", "a2", "b2")),
        (obs("s3", "+", "a3", "b3"), obs("t3", "*", "a3", "b3")),
    ]).candidates[0]
    status, obj = build_operator_from_discovered_relation(c, p1, p2, new_ref_id="OP::derived")
    assert status == "CREATED_NEW"
    assert obj.ref.ref_id == "OP::derived"
    assert obj.structure.children[0] == NodeRef("+")
    assert obj.structure.children[1] == NodeRef("*")
