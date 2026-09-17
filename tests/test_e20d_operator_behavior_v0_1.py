import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel2 import Node, NodeRef, OBSERVATION, ref_object, structural_equal
from e20d_operator_behavior_v0_1 import (
    behavior_witness, discover_embedded_operator_relation, relation_as_ref,
    identify_or_create_relation, cumulative_property_structure,
)
from operator_space_v0_1 import operator_profile


def app(i, op, *args):
    return Node(i, OBSERVATION, (NodeRef(op),) + tuple(NodeRef(a) for a in args))


def repeated_witness(i, op, arg, n=3):
    # Structural witness: op(arg, op(arg, ...))
    inner = Node(f"{i}-0", OBSERVATION, (NodeRef(op), NodeRef(arg)))
    for k in range(1, n):
        inner = Node(f"{i}-{k}", OBSERVATION, (NodeRef(op), NodeRef(arg), inner))
    return inner


def test_repeated_behavior_discovers_embedded_operator_relation():
    ws = [
        behavior_witness(app("s1", "*", "a1", "b1"), repeated_witness("w1", "+", "a1", 3)),
        behavior_witness(app("s2", "*", "a2", "b2"), repeated_witness("w2", "+", "a2", 3)),
        behavior_witness(app("s3", "*", "a3", "b3"), repeated_witness("w3", "+", "a3", 3)),
    ]
    r = discover_embedded_operator_relation(ws)
    assert r is not None
    assert r.source_operator.ref_id == "*"
    assert r.target_operator.ref_id == "+"
    assert r.repeat_count == 3


def test_reference_identity_not_value_identity():
    r1 = discover_embedded_operator_relation([
        behavior_witness(app("s1", "*", "a1"), repeated_witness("w1", "+", "a1", 2)),
        behavior_witness(app("s2", "*", "a2"), repeated_witness("w2", "+", "a2", 2)),
        behavior_witness(app("s3", "*", "a3"), repeated_witness("w3", "+", "a3", 2)),
    ])
    assert r1 is not None


def test_inconsistent_counts_fail_closed():
    ws = [
        behavior_witness(app("s1", "*", "a1"), repeated_witness("w1", "+", "a1", 2)),
        behavior_witness(app("s2", "*", "a2"), repeated_witness("w2", "+", "a2", 3)),
        behavior_witness(app("s3", "*", "a3"), repeated_witness("w3", "+", "a3", 2)),
    ]
    assert discover_embedded_operator_relation(ws) is None


def test_non_embedded_target_operator_fails_closed():
    w1 = Node("w1", OBSERVATION, (NodeRef("+"), NodeRef("a")))
    w2 = Node("w2", OBSERVATION, (NodeRef("+"), NodeRef("b")))
    w3 = Node("w3", OBSERVATION, (NodeRef("+"), NodeRef("c")))
    assert discover_embedded_operator_relation([
        behavior_witness(app("s1", "*", "a"), w1),
        behavior_witness(app("s2", "*", "b"), w2),
        behavior_witness(app("s3", "*", "c"), w3),
    ]) is None


def test_relation_is_reified_without_semantic_label():
    ws = [
        behavior_witness(app("s1", "*", "a1"), repeated_witness("w1", "+", "a1", 2)),
        behavior_witness(app("s2", "*", "a2"), repeated_witness("w2", "+", "a2", 2)),
        behavior_witness(app("s3", "*", "a3"), repeated_witness("w3", "+", "a3", 2)),
    ]
    r = discover_embedded_operator_relation(ws)
    ref = relation_as_ref(r, "REL1")
    assert ref.ref.ref_id == "REL1"
    assert ref.structure.children[0] == NodeRef("*")
    assert ref.structure.children[1] == NodeRef("+")


def test_identified_existing_uses_structure_not_ref_id():
    ws = [
        behavior_witness(app("s1", "*", "a1"), repeated_witness("w1", "+", "a1", 2)),
        behavior_witness(app("s2", "*", "a2"), repeated_witness("w2", "+", "a2", 2)),
        behavior_witness(app("s3", "*", "a3"), repeated_witness("w3", "+", "a3", 2)),
    ]
    r = discover_embedded_operator_relation(ws)
    existing = [relation_as_ref(r, "EXISTING")]
    status, obj = identify_or_create_relation(r, existing, new_ref_id="NEW")
    assert status == "IDENTIFIED_EXISTING"
    assert obj.ref.ref_id == "EXISTING"


def test_new_relation_when_structure_unseen():
    ws = [
        behavior_witness(app("s1", "*", "a1"), repeated_witness("w1", "+", "a1", 2)),
        behavior_witness(app("s2", "*", "a2"), repeated_witness("w2", "+", "a2", 2)),
        behavior_witness(app("s3", "*", "a3"), repeated_witness("w3", "+", "a3", 2)),
    ]
    r = discover_embedded_operator_relation(ws)
    status, obj = identify_or_create_relation(r, [], new_ref_id="NEW")
    assert status == "CREATED_NEW"
    assert obj.ref.ref_id == "NEW"


def test_cumulative_properties_keep_only_structural_commonality():
    p1 = operator_profile("*", arity=2, properties=["COMMUTATIVE", "ITERATIVE"])
    p2 = operator_profile("+", arity=2, properties=["COMMUTATIVE", "ITERATIVE", "OTHER"])
    r = discover_embedded_operator_relation([
        behavior_witness(app("s1","*","a1"), repeated_witness("w1","+","a1",2)),
        behavior_witness(app("s2","*","a2"), repeated_witness("w2","+","a2",2)),
        behavior_witness(app("s3","*","a3"), repeated_witness("w3","+","a3",2)),
    ])
    c = cumulative_property_structure(p1,p2,r)
    common = c.children[0]
    assert common.children == (NodeRef("COMMUTATIVE"), NodeRef("ITERATIVE"))


def test_same_structure_different_relation_reference_is_not_identity():
    ws = [
        behavior_witness(app("s1", "*", "a1"), repeated_witness("w1", "+", "a1", 2)),
        behavior_witness(app("s2", "*", "a2"), repeated_witness("w2", "+", "a2", 2)),
        behavior_witness(app("s3", "*", "a3"), repeated_witness("w3", "+", "a3", 2)),
    ]
    r = discover_embedded_operator_relation(ws)
    a = relation_as_ref(r, "R1")
    b = relation_as_ref(r, "R2")
    assert a.ref != b.ref
    assert structural_equal(a, b)


def test_minimum_evidence_is_enforced():
    ws = [behavior_witness(app("s","*","a"), repeated_witness("w","+","a",2))]
    try:
        discover_embedded_operator_relation(ws)
    except ValueError:
        return
    assert False
