import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import NodeRef, RefObject, reference_equal, structural_equal
from e20d_operational_relation_v0_1 import OperationalFieldRelation, OperationalRelationRecord
from e20d_operation_synthesis_v0_1 import (
    OP_STATUS_AMBIGUOUS,
    OP_STATUS_CREATED_NEW,
    OP_STATUS_IDENTIFIED_EXISTING,
    apply_derived_operation,
    build_derived_operation,
    operation_structural_equal,
    operation_trace,
    synthesize_operation,
)


def relation(left="A", right="B", rid="R1"):
    field = OperationalFieldRelation("length", "EQUAL", 2, 2)
    return OperationalRelationRecord(
        relation_id=rid,
        left_ref=NodeRef(left),
        right_ref=NodeRef(right),
        basis="COMMON_STRUCTURAL_PROPERTIES",
        fields=(field,),
        relation_kind="STRUCTURAL_EQUIVALENCE",
        provenance=("s1", "s2"),
    )


def test_new_operation_is_reified_from_relation_only():
    status, op = synthesize_operation(relation(), new_ref_id="OP::NEW")
    assert status == OP_STATUS_CREATED_NEW
    assert isinstance(op, RefObject)
    assert op.ref == NodeRef("OP::NEW")
    assert op.structure[0] == "DERIVED_OPERATION"
    assert op.structure[1:3] == (NodeRef("A"), NodeRef("B"))


def test_existing_structural_operation_is_reused():
    r = relation()
    existing = build_derived_operation(r, new_ref_id="OP::EXISTING").as_ref_object()
    status, op = synthesize_operation(r, existing=(existing,), new_ref_id="OP::CAND")
    assert status == OP_STATUS_IDENTIFIED_EXISTING
    assert op is existing


def test_two_equivalent_existing_refs_fail_closed():
    r = relation()
    a = build_derived_operation(r, new_ref_id="OP::A").as_ref_object()
    b = build_derived_operation(r, new_ref_id="OP::B").as_ref_object()
    status, candidate = synthesize_operation(r, existing=(a, b), new_ref_id="OP::C")
    assert status == OP_STATUS_AMBIGUOUS
    assert not reference_equal(a, b)
    assert structural_equal(a.structure, b.structure)
    assert candidate.ref == NodeRef("OP::C")


def test_relation_structure_is_embedded_without_provenance_inflation():
    r1 = relation(rid="R1")
    r2 = relation(rid="R2")
    a = build_derived_operation(r1, new_ref_id="OP::A").as_ref_object()
    b = build_derived_operation(r2, new_ref_id="OP::B").as_ref_object()
    assert operation_structural_equal(a, b)


def test_distinct_operation_refs_can_share_structure():
    r = relation()
    a = build_derived_operation(r, new_ref_id="OP::A").as_ref_object()
    b = build_derived_operation(r, new_ref_id="OP::B").as_ref_object()
    assert a.ref != b.ref
    assert structural_equal(a, b)


def test_synthesized_operation_can_be_used_by_apply():
    status, op = synthesize_operation(relation(), new_ref_id="OP::APPLY")
    result = apply_derived_operation(op, NodeRef("X"), NodeRef("Y"), node_id="S3", provenance=("R1",))
    assert status == OP_STATUS_CREATED_NEW
    assert result.children[0] == NodeRef("OP::APPLY")
    assert result.children[1:] == (NodeRef("X"), NodeRef("Y"))


def test_operation_trace_is_stable():
    r = relation()
    a = build_derived_operation(r, new_ref_id="OP::A").as_ref_object()
    b = build_derived_operation(r, new_ref_id="OP::B").as_ref_object()
    assert operation_trace(a) == operation_trace(b)


def test_missing_relation_endpoint_is_rejected():
    r = OperationalRelationRecord(
        relation_id="R_BAD", left_ref=None, right_ref=NodeRef("B"),
        basis="COMMON_STRUCTURAL_PROPERTIES", fields=(),
        relation_kind="STRUCTURAL_RELATION", provenance=(),
    )
    try:
        build_derived_operation(r)
        assert False, "expected ValueError"
    except ValueError:
        pass
