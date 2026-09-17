from operator_space_v0_1 import (
    operator_ref, operator_property, operator_relation_fact,
    operator_profile, compose_existing_operator_profile,
    build_composed_operator, identify_existing_operator,
)
from kernel2 import NodeRef, ref_object, structural_equal, reference_equal, OBSERVATION


def test_identity_same_operator_reification():
    plus = operator_ref("+")
    p1 = operator_profile(plus, arity=2, properties=["COMMUTATIVE", "ITERABLE"])
    p2 = operator_profile(plus, arity=2, properties=["COMMUTATIVE", "ITERABLE"])
    status, obj = compose_existing_operator_profile(p1, p2)
    assert status == "CREATED_NEW"
    body = obj.structure
    assert body.children[0] == NodeRef("+")
    assert body.children[1] == NodeRef("+")


def test_same_reference_distinct_structure_is_not_structural_equality():
    r = NodeRef("+")
    a = build_composed_operator(r, r, common_properties=[NodeRef("P")], new_ref_id="X")
    b = build_composed_operator(r, r, common_properties=[NodeRef("Q")], new_ref_id="Y")
    assert reference_equal(a, b) is False
    assert structural_equal(a, b) is False


def test_existing_composition_can_be_identified():
    plus, times = operator_ref("+"), operator_ref("*")
    common = [NodeRef("ARITY2")]
    expected = build_composed_operator(plus, times, common_properties=common, new_ref_id="OP::existing")
    candidate = build_composed_operator(plus, times, common_properties=common, new_ref_id="OP::candidate")
    hit = identify_existing_operator(candidate, [expected])
    assert hit is expected


def test_different_operators_create_new_operator_when_no_match():
    plus, times = operator_ref("+"), operator_ref("*")
    p1 = operator_profile(plus, arity=2, properties=["COMMUTATIVE", "ADDITIVE"])
    p2 = operator_profile(times, arity=2, properties=["COMMUTATIVE", "ITERATIVE"])
    status, new_op = compose_existing_operator_profile(
        p1, p2, existing=(), new_ref_id="OP::plus_times"
    )
    assert status == "CREATED_NEW"
    assert new_op.ref.ref_id == "OP::plus_times"
    assert new_op.structure.children[0].ref_id == "+"
    assert new_op.structure.children[1].ref_id == "*"


def test_common_properties_use_reference_identity():
    p1 = operator_profile("O1", arity=2, properties=["P", "Q"])
    p2 = operator_profile("O2", arity=2, properties=["P", "R"])
    status, obj = compose_existing_operator_profile(p1, p2)
    common = obj.structure.children[2]
    assert [x.ref_id for x in common.children] == ["P"]


def test_relation_fact_is_structurally_carried_into_composition():
    plus, times = operator_ref("+"), operator_ref("*")
    fact = operator_relation_fact(plus, times, "ITERATION_RELATION")
    p1 = operator_profile(plus, arity=2, properties=["COMMUTATIVE"], relation_facts=[fact])
    p2 = operator_profile(times, arity=2, properties=["COMMUTATIVE"], relation_facts=[fact])
    status, obj = compose_existing_operator_profile(p1, p2)
    rels = obj.structure.children[3]
    assert len(rels.children) >= 1
    assert rels.children[0].children[2] == NodeRef("ITERATION_RELATION")


def test_composed_operator_is_referencable_and_reusable_as_operand():
    plus, times = operator_ref("+"), operator_ref("*")
    comp = build_composed_operator(plus, times, new_ref_id="OP::C")
    outer = build_composed_operator(comp.ref, plus, new_ref_id="OP::D")
    assert outer.structure.children[0] == comp.ref
    assert outer.ref.ref_id == "OP::D"
