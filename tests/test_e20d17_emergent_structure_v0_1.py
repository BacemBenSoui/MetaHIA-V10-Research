import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import Node, NodeRef, OBSERVATION, build_structural_graph, structural_equal
from e20d_operational_relation_v0_1 import OperationalFieldRelation, OperationalRelationRecord
from e20d_operation_synthesis_v0_1 import synthesize_operation
from e20d_emergent_structure_v0_1 import (
    EMERGENT_STATUS_CREATED,
    EMERGENT_STATUS_NOT_NEW,
    generate_emergent_structure,
    structural_trace,
)


def relation(left='A', right='B', rid='R1'):
    field = OperationalFieldRelation('length', 'EQUAL', 2, 2)
    return OperationalRelationRecord(
        relation_id=rid,
        left_ref=NodeRef(left),
        right_ref=NodeRef(right),
        basis='COMMON_STRUCTURAL_PROPERTIES',
        fields=(field,),
        relation_kind='STRUCTURAL_EQUIVALENCE',
        provenance=('s1', 's2'),
    )


def rel(node_id, op, a, b):
    return Node(node_id, OBSERVATION, (NodeRef(op), NodeRef(a), NodeRef(b)), provenance=(node_id,))


def test_generated_operation_creates_structure_absent_from_observed_graph():
    status, operation = synthesize_operation(relation(), new_ref_id='OP::EMERGENT')
    observed = [
        rel('o1', 'R', 'A', 'B'),
        rel('o2', 'R', 'B', 'C'),
    ]
    result = generate_emergent_structure(
        operation,
        NodeRef('X'), NodeRef('Y'),
        observed=observed,
        node_id='S::NEW',
        provenance=('R1', 'D17'),
    )
    assert status == 'CREATED_NEW'
    assert result.status == EMERGENT_STATUS_CREATED
    assert result.novelty_verified
    assert result.structure.node_id == 'S::NEW'
    assert result.structure.children == (NodeRef('OP::EMERGENT'), NodeRef('X'), NodeRef('Y'))
    assert not any(structural_equal(result.structure, x) for x in observed)


def test_same_reified_operation_can_generate_multiple_novel_structures():
    _, operation = synthesize_operation(relation(), new_ref_id='OP::REUSE')
    r1 = generate_emergent_structure(operation, NodeRef('X'), NodeRef('Y'), node_id='N1', provenance=('p1',))
    r2 = generate_emergent_structure(operation, NodeRef('U'), NodeRef('V'), node_id='N2', provenance=('p2',))
    assert r1.status == EMERGENT_STATUS_CREATED
    assert r2.status == EMERGENT_STATUS_CREATED
    assert r1.structure != r2.structure


def test_generated_structure_is_allowed_to_be_semantically_unnamed():
    _, operation = synthesize_operation(relation(), new_ref_id='OP::OPAQUE')
    result = generate_emergent_structure(operation, NodeRef('Sonia'), NodeRef('Moto'), node_id='LINK::OPAQUE', provenance=('family',))
    assert result.novelty_verified
    assert result.structure.children[0] == NodeRef('OP::OPAQUE')
    assert result.structure.children[1:] == (NodeRef('Sonia'), NodeRef('Moto'))


def test_novelty_check_does_not_use_payload_semantics():
    _, operation = synthesize_operation(relation(), new_ref_id='OP::REF')
    observed = [rel('o1', 'R', 'A', 'B')]
    result = generate_emergent_structure(operation, NodeRef('A'), NodeRef('B'), observed=observed, node_id='N', provenance=('x',))
    assert result.status == EMERGENT_STATUS_CREATED


def test_exact_observed_structure_is_not_claimed_novel():
    _, operation = synthesize_operation(relation(), new_ref_id='R')
    observed_candidate = rel('OBS', 'R', 'A', 'B')
    result = generate_emergent_structure(operation, NodeRef('A'), NodeRef('B'), observed=[observed_candidate], node_id='OBS2', provenance=('x',))
    assert result.status == EMERGENT_STATUS_NOT_NEW
    assert not result.novelty_verified


def test_provenance_is_preserved_on_emergent_structure():
    _, operation = synthesize_operation(relation(), new_ref_id='OP::PROV')
    result = generate_emergent_structure(operation, NodeRef('X'), NodeRef('Y'), node_id='NEW', provenance=('s1', 's2'))
    assert result.structure.provenance == ('s1', 's2')
    assert result.provenance == ('s1', 's2')


def test_trace_is_replayable_and_contains_identity():
    _, operation = synthesize_operation(relation(), new_ref_id='OP::TRACE')
    result = generate_emergent_structure(operation, NodeRef('X'), NodeRef('Y'), node_id='NEW', provenance=('s1',))
    trace = structural_trace(result)
    assert trace[1] == NodeRef('OP::TRACE')
    assert trace[5] is True


def test_emergent_result_is_still_an_ordinary_k3_node():
    _, operation = synthesize_operation(relation(), new_ref_id='OP::NODE')
    result = generate_emergent_structure(operation, NodeRef('X'), NodeRef('Y'), node_id='NEW', provenance=('s',))
    assert isinstance(result.structure, Node)
    assert result.structure.kind == OBSERVATION
