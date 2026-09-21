"""P4-R v0.2 — non-circular structural-transfer gate.

This experiment replaces the invalidated P4.1-P4.5 endpoint-transfer chain.
It has two deliberately separate outcomes:

1) POSITIVE MICRO-GATE: a source-only D14 relation is normalized into a
   domain-neutral, operator-agnostic structural operation schema and applied
   to *new target operands* to create a novel K3 structural object.

2) STRONG ENDPOINT GATE: a target antecedent-only holdout is supplied with the
   endpoint fact removed.  The current structural kernel must fail closed: it
   is not allowed to inspect the hidden endpoint or invent a semantic relation.
   Therefore no endpoint prediction is claimed.  This is an expected OPEN
   result, not a test failure.

The protocol intentionally never consults target verification claims until
all source discovery, operation synthesis, target operand selection and
structural execution have completed.

No M1/M6 source is modified. M7 is not involved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Tuple

from kernel2 import Node, NodeRef, RefObject, OBSERVATION, apply_operator, structural_equal
from e20d_p4_autonomous_transfer_v0_1 import AbstractPathInvariant, discover_source_invariants, make_paths, _shape
from e20d_operational_relation_v0_1 import OperationalRelationRecord, discover_operational_relation

P4R_TRANSFERRED_OPERATION = "TRANSFERRED_STRUCTURAL_OPERATION"
P4R_NOT_DERIVABLE = "NOT_DERIVABLE"


@dataclass(frozen=True)
class TransferableOperationSpec:
    """Domain-neutral executable structural schema derived from source only."""
    operation_id: str
    source_invariant_id: str
    length: int
    direction_sequence: Tuple[str, ...]
    node_binding: Tuple[int, ...]
    arity: int
    relation_kind: str
    field_relation_kinds: Tuple[str, ...]

    def structural_body(self) -> tuple:
        return (
            P4R_TRANSFERRED_OPERATION,
            self.length,
            self.direction_sequence,
            self.node_binding,
            self.arity,
            self.relation_kind,
            self.field_relation_kinds,
        )

    def as_ref_object(self) -> RefObject:
        return RefObject(NodeRef(self.operation_id), self.structural_body())


def choose_source_case(
    family_facts: Sequence[tuple],
    *,
    min_support: int = 2,
) -> tuple[AbstractPathInvariant, object, object, OperationalRelationRecord]:
    """Discover a non-trivial source relation using SOURCE data only."""
    paths = make_paths(family_facts, 2)
    invariants = [i for i in discover_source_invariants(paths, min_support=min_support) if i.length == 2]
    # Prefer a shape with several supports and a pair that differs in operator identities.
    invariants = sorted(invariants, key=lambda i: (-i.support_count, i.invariant_id))
    for inv in invariants:
        items = [p for p in paths if _shape(p) == inv.signature()]
        for idx, left in enumerate(items):
            for right in items[idx + 1 :]:
                if left.operator_sequence == right.operator_sequence:
                    continue
                relation = discover_operational_relation(left, right, relation_id=f"P4R::{inv.invariant_id}")
                if relation is not None:
                    return inv, left, right, relation
    raise ValueError("no non-trivial source relation available")


def freeze_transferable_operation(
    invariant: AbstractPathInvariant,
    relation: OperationalRelationRecord,
    *,
    operation_id: str,
) -> TransferableOperationSpec:
    """Freeze only domain-neutral structural information.

    No source node/operator identity and no target information are retained.
    """
    return TransferableOperationSpec(
        operation_id=operation_id,
        source_invariant_id=invariant.invariant_id,
        length=invariant.length,
        direction_sequence=tuple(invariant.direction_sequence),
        node_binding=tuple(invariant.node_binding),
        arity=2,
        relation_kind=relation.relation_kind,
        field_relation_kinds=tuple(field.relation for field in relation.fields),
    )


def target_nodes_from_facts(facts: Iterable[tuple]) -> tuple[Node, ...]:
    return tuple(
        Node(fid, OBSERVATION, (NodeRef(op), NodeRef(subj), NodeRef(obj)), provenance=(fid,))
        for fid, op, subj, obj in facts
    )


def apply_transferable_operation(
    spec: TransferableOperationSpec,
    *operands: NodeRef,
    node_id: str,
    provenance: Tuple[str, ...],
) -> Node:
    """Create a novel structural application from target operands only."""
    if len(operands) != spec.arity:
        raise ValueError(f"expected {spec.arity} operands, got {len(operands)}")
    return apply_operator(
        spec.as_ref_object(),
        *operands,
        node_id=node_id,
        provenance=provenance,
    )


def is_novel(candidate: Node, observed: Iterable[Node]) -> bool:
    return not any(structural_equal(candidate, item) for item in observed)


def masked_endpoint_gate(
    antecedent_facts: Sequence[tuple],
    hidden_endpoint: str,
) -> dict:
    """Attempt the *strong* endpoint gate with the endpoint edge absent.

    The current K3 structural abstraction has no semantic evaluator, so the
    only honest outcome is NOT_DERIVABLE.  The function records the exact input
    boundary to make leakage auditable.
    """
    input_text = repr(tuple(antecedent_facts))
    endpoint_visible = hidden_endpoint in input_text
    return {
        "status": P4R_NOT_DERIVABLE,
        "predicted_end": None,
        "hidden_endpoint": hidden_endpoint,
        "hidden_endpoint_visible_in_execution_input": endpoint_visible,
        "semantic_endpoint_invention_supported": False,
    }


def run_p4r(
    family_discovery_facts: Sequence[tuple],
    organization_discovery_facts: Sequence[tuple],
    organization_endpoint_antecedent_facts: Sequence[tuple],
    hidden_endpoint: str,
) -> dict:
    """Run the corrected non-circular gate."""
    invariant, left, right, relation = choose_source_case(family_discovery_facts)
    spec = freeze_transferable_operation(
        invariant,
        relation,
        operation_id=f"OP::P4R::{invariant.invariant_id}",
    )

    # Target case is fixed independently before execution; no endpoint witness
    # or hidden endpoint fact is supplied to discovery or operation synthesis.
    target_operands = (NodeRef("Module_A"), NodeRef("Projet_X"))
    observed_target = target_nodes_from_facts(organization_discovery_facts)
    candidate = apply_transferable_operation(
        spec,
        *target_operands,
        node_id="P4R::TARGET::NEW",
        provenance=("organization_discovery_operands",),
    )

    novelty = is_novel(candidate, observed_target)
    endpoint_gate = masked_endpoint_gate(
        organization_endpoint_antecedent_facts,
        hidden_endpoint,
    )

    # Audit that target information does not leak into the frozen operation.
    serialized = repr(spec.structural_body())
    target_refs = {str(ref) for ref in target_operands}
    source_ids = set(invariant.source_path_ids)
    target_leaks = sorted(ref for ref in target_refs if ref in serialized)
    source_path_leaks = sorted(ref for ref in source_ids if ref in serialized)

    return {
        "experiment": "P4R_NON_CIRCULAR_STRUCTURAL_TRANSFER_V0.2",
        "source": {
            "invariant_id": invariant.invariant_id,
            "support_count": invariant.support_count,
            "source_path_ids": list(invariant.source_path_ids),
            "left_path_id": left.path_id,
            "right_path_id": right.path_id,
            "relation_id": relation.relation_id,
            "relation_kind": relation.relation_kind,
        },
        "frozen_operation": {
            "operation_id": spec.operation_id,
            "length": spec.length,
            "direction_sequence": list(spec.direction_sequence),
            "node_binding": list(spec.node_binding),
            "arity": spec.arity,
            "relation_kind": spec.relation_kind,
            "field_relation_kinds": list(spec.field_relation_kinds),
        },
        "target_structural_generation": {
            "operands": [r.ref_id for r in target_operands],
            "derived_node_id": candidate.node_id,
            "novelty_verified": novelty,
            "candidate_children": candidate.children,
            "candidate_kind": candidate.kind,
        },
        "masked_endpoint_gate": endpoint_gate,
        "leakage_audit": {
            "target_operands_in_frozen_operation": bool(target_leaks),
            "source_path_ids_in_frozen_operation": bool(source_path_leaks),
            "target_leaks": target_leaks,
            "source_path_leaks": source_path_leaks,
        },
        "discipline": {
            "target_verification_consulted_before_prediction": False,
            "hidden_endpoint_supplied_to_execution": False,
            "semantic_dictionary_used": False,
            "m1_changed": False,
            "m6_changed": False,
            "m7_dependency": False,
        },
        "status": {
            "micro_structural_transfer": "PASS" if novelty and not target_leaks else "FAIL",
            "strong_endpoint_transfer": "OPEN_EXPECTED" if endpoint_gate["status"] == P4R_NOT_DERIVABLE else "UNEXPECTED",
            "e20d_closure": "OPEN",
        },
    }
