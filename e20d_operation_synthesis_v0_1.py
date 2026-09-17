"""E20-D.15 — Structural operation synthesis/reification.

This module takes an already discovered OperationalRelationRecord and
reifies an operation object from it. It deliberately does NOT evaluate the
meaning of the operation. The result remains an ordinary reference-bearing
structural object and can therefore be reused by the K3 Apply constructor.

Decision contract:
  IDENTIFIED_EXISTING  -> exactly one structurally equivalent existing op
  CREATED_NEW          -> no equivalent existing op
  AMBIGUOUS            -> more than one distinct existing ref is equivalent

The module is additive to K3: no new ontology primitive is added to
kernel2.py. Identity, structure, value and provenance remain separated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from kernel2 import NodeRef, RefObject, Node, apply_operator, structural_equal, structural_signature
from e20d_operational_relation_v0_1 import OperationalRelationRecord

DERIVED_OPERATION = "DERIVED_OPERATION"
OP_STATUS_IDENTIFIED_EXISTING = "IDENTIFIED_EXISTING"
OP_STATUS_CREATED_NEW = "CREATED_NEW"
OP_STATUS_AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class DerivedOperationRecord:
    """Replayable record for an operation synthesized from a relation."""
    operation_id: str
    operation_ref: NodeRef
    source_left_ref: NodeRef
    source_right_ref: NodeRef
    relation_ref: Optional[NodeRef]
    basis: str
    structure: object
    provenance: Tuple[str, ...]

    def structural_form(self) -> tuple:
        return self.structure if isinstance(self.structure, tuple) else (self.structure,)

    def as_ref_object(self) -> RefObject:
        return RefObject(self.operation_ref, self.structural_form())


def _relation_ref(relation: OperationalRelationRecord) -> Optional[NodeRef]:
    return NodeRef(relation.relation_id)


def build_derived_operation(
    relation: OperationalRelationRecord,
    *,
    new_ref_id: Optional[str] = None,
) -> DerivedOperationRecord:
    """Construct an opaque operation structure from a discovered relation.

    The structure records the two related object references and the relation
    itself. It is a reified algebraic object, not an executable semantic rule.
    """
    if relation.left_ref is None or relation.right_ref is None:
        raise ValueError("operation synthesis requires both relation endpoints")

    operation_id = new_ref_id or f"OP::derived::{relation.relation_id}"
    relation_form = relation.structural_form()
    structure = (
        DERIVED_OPERATION,
        relation.left_ref,
        relation.right_ref,
        relation_form,
    )
    return DerivedOperationRecord(
        operation_id=operation_id,
        operation_ref=NodeRef(operation_id),
        source_left_ref=relation.left_ref,
        source_right_ref=relation.right_ref,
        relation_ref=_relation_ref(relation),
        basis="DISCOVERED_OPERATIONAL_RELATION",
        structure=structure,
        provenance=tuple(relation.provenance),
    )


def _equivalent_existing(
    candidate: RefObject,
    existing: Sequence[RefObject],
) -> Tuple[RefObject, ...]:
    return tuple(item for item in existing if structural_equal(candidate.structure, item.structure))


def synthesize_operation(
    relation: OperationalRelationRecord,
    *,
    existing: Sequence[RefObject] = (),
    new_ref_id: Optional[str] = None,
) -> Tuple[str, RefObject]:
    """Identify an existing operation or create a new structural operation.

    The decision is fail-closed when more than one distinct existing reference
    has the same structure. Identity is never inferred from structure alone.
    """
    candidate = build_derived_operation(relation, new_ref_id=new_ref_id).as_ref_object()
    matches = _equivalent_existing(candidate, existing)
    distinct_refs = {item.ref.ref_id for item in matches}
    if len(distinct_refs) > 1:
        return OP_STATUS_AMBIGUOUS, candidate
    if matches:
        return OP_STATUS_IDENTIFIED_EXISTING, matches[0]
    return OP_STATUS_CREATED_NEW, candidate


def apply_derived_operation(
    operation: RefObject,
    *operands: object,
    node_id: Optional[str] = None,
    provenance: Tuple[str, ...] = (),
) -> Node:
    """Use a synthesized operation as an ordinary K3 operator reference.

    This constructs the next structural application; it does not evaluate a
    semantic meaning for the derived operation.
    """
    return apply_operator(operation, *operands, node_id=node_id, provenance=provenance)


def operation_structural_equal(left: RefObject, right: RefObject) -> bool:
    """Compare operation bodies while keeping reference identity separate."""
    return structural_equal(left.structure, right.structure)


def operation_trace(operation: RefObject) -> tuple:
    """Stable structural trace useful for replay and third-party audit."""
    return structural_signature(operation.structure)
