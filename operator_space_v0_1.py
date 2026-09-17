"""MetaHIA operator-space spike v0.1.

Experimental layer built on K3 primitives. It does NOT add a new primitive to
kernel2.py. The purpose is to test the proposed meta-level mechanism:

    structural relation R(S1,S2)
        -> operator relation R'(O1,O2)
        -> existing-operator identification OR operator construction
        -> replayable operation object

Operator properties are treated as opaque structural tokens. No semantic
property detector is hard-coded here. Evidence about properties must enter as
structural facts (OperatorEvidence nodes).

Reference/value invariant:
  operator identity is NodeRef-based;
  operator structures are RefObjects/PatternRefs;
  values/properties never establish reference identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from kernel2 import Node, NodeRef, RefObject, OBSERVATION, PATTERN, PatternRef
from kernel2 import reference_equal, structural_equal, structural_signature, ref_object

OPERATOR_EVIDENCE = "OPERATOR_EVIDENCE"
OPERATOR_COMPOSITION = "OPERATOR_COMPOSITION"
OPERATOR_RELATION = "OPERATOR_RELATION"


@dataclass(frozen=True)
class OperatorRef:
    """Identity handle for an operator. Payload/name is external/opaque."""
    ref: NodeRef


def operator_ref(ref_id: str) -> OperatorRef:
    return OperatorRef(NodeRef(ref_id))


def operator_token(op: OperatorRef | NodeRef | str) -> NodeRef:
    if isinstance(op, OperatorRef):
        return op.ref
    if isinstance(op, NodeRef):
        return op
    return NodeRef(op)


def observation_with_operator(node_id: str, op: OperatorRef | NodeRef | str, *operands: object) -> Node:
    """Build an opaque observation whose first child is the operator ref."""
    return Node(node_id, OBSERVATION, (operator_token(op),) + tuple(operands))


def extract_operator(observation: Node) -> NodeRef:
    if observation.kind != OBSERVATION or not observation.children:
        raise ValueError("operator extraction requires a non-empty OBSERVATION")
    op = observation.children[0]
    if not isinstance(op, NodeRef):
        raise ValueError("operator position must carry a NodeRef")
    return op


def operator_property(op: OperatorRef | NodeRef | str, property_id: str) -> Node:
    """Opaque evidence: operator has property token property_id."""
    op_ref = operator_token(op)
    return Node(
        f"prop::{op_ref.ref_id}::{property_id}",
        OPERATOR_EVIDENCE,
        (op_ref, NodeRef(property_id)),
    )


def operator_relation_fact(
    op1: OperatorRef | NodeRef | str,
    op2: OperatorRef | NodeRef | str,
    relation_id: str,
) -> Node:
    """Opaque evidence about a relation between two operators."""
    return Node(
        f"rel::{operator_token(op1).ref_id}::{operator_token(op2).ref_id}::{relation_id}",
        OPERATOR_RELATION,
        (operator_token(op1), operator_token(op2), NodeRef(relation_id)),
    )


def operator_profile(
    op: OperatorRef | NodeRef | str,
    *,
    arity: int,
    properties: Iterable[str] = (),
    relation_facts: Iterable[Node] = (),
) -> Node:
    """Create a structural operator profile from opaque evidence."""
    op_ref = operator_token(op)
    prop_nodes = tuple(NodeRef(p) for p in sorted(set(properties)))
    return Node(
        f"profile::{op_ref.ref_id}",
        OPERATOR_EVIDENCE,
        (
            op_ref,
            NodeRef(f"ARITY:{arity}"),
            Node("properties", OPERATOR_EVIDENCE, prop_nodes),
            Node("relations", OPERATOR_EVIDENCE, tuple(relation_facts)),
        ),
    )


def profile_properties(profile: Node) -> Tuple[NodeRef, ...]:
    props = profile.children[2]
    if not isinstance(props, Node) or props.kind != OPERATOR_EVIDENCE:
        return ()
    return tuple(x for x in props.children if isinstance(x, NodeRef))


def profile_relations(profile: Node) -> Tuple[Node, ...]:
    rels = profile.children[3]
    if not isinstance(rels, Node) or rels.kind != OPERATOR_EVIDENCE:
        return ()
    return tuple(x for x in rels.children if isinstance(x, Node))


def common_property_refs(p1: Node, p2: Node) -> Tuple[NodeRef, ...]:
    """Intersection by reference identity, never by external payload value."""
    a = {x.ref_id: x for x in profile_properties(p1)}
    b = {x.ref_id: x for x in profile_properties(p2)}
    return tuple(a[k] for k in sorted(set(a) & set(b)))


def relation_facts_between(p1: Node, p2: Node) -> Tuple[Node, ...]:
    """Return relation facts whose first two operands match the profile ops."""
    o1, o2 = p1.children[0], p2.children[0]
    if not isinstance(o1, NodeRef) or not isinstance(o2, NodeRef):
        return ()
    facts = []
    for fact in profile_relations(p1) + profile_relations(p2):
        if fact.kind != OPERATOR_RELATION or len(fact.children) != 3:
            continue
        a, b = fact.children[:2]
        if isinstance(a, NodeRef) and isinstance(b, NodeRef):
            if (reference_equal(a, o1) and reference_equal(b, o2)) or (
                reference_equal(a, o2) and reference_equal(b, o1)
            ):
                facts.append(fact)
    return tuple(facts)


def build_composed_operator(op1: OperatorRef | NodeRef | str, op2: OperatorRef | NodeRef | str, *, relation_facts: Sequence[Node] = (), common_properties: Sequence[NodeRef] = (), new_ref_id: Optional[str] = None) -> RefObject:
    """Create a referencable operator composition object.

    The operator body is itself structural; it is NOT evaluated numerically.
    """
    a, b = operator_token(op1), operator_token(op2)
    body = Node(
        f"opcomp::body::{a.ref_id}::{b.ref_id}",
        OPERATOR_COMPOSITION,
        (
            a,
            b,
            Node("common_properties", OPERATOR_EVIDENCE, tuple(common_properties)),
            Node("relation_facts", OPERATOR_EVIDENCE, tuple(relation_facts)),
        ),
    )
    ref_id = new_ref_id or f"OP::compose::{a.ref_id}::{b.ref_id}"
    return ref_object(ref_id, body)


def identify_existing_operator(candidate: RefObject, existing: Sequence[RefObject]) -> Optional[RefObject]:
    """Find an existing operator with structurally equivalent body."""
    for item in existing:
        if structural_equal(candidate.structure, item.structure):
            return item
    return None


def derive_operator(candidate_pair: RefObject, existing: Sequence[RefObject]) -> Tuple[str, RefObject]:
    """Identify an existing operator, otherwise retain the generated one."""
    hit = identify_existing_operator(candidate_pair, existing)
    if hit is not None:
        return "IDENTIFIED_EXISTING", hit
    return "CREATED_NEW", candidate_pair


def compose_existing_operator_profile(
    p1: Node,
    p2: Node,
    *,
    existing: Sequence[RefObject] = (),
    relation_facts: Sequence[Node] = (),
    new_ref_id: Optional[str] = None,
) -> Tuple[str, RefObject]:
    """End-to-end operator-space step: relation -> composed object -> identify/create."""
    op1, op2 = p1.children[0], p2.children[0]
    if not isinstance(op1, NodeRef) or not isinstance(op2, NodeRef):
        raise ValueError("operator profiles must start with NodeRef operator identities")
    common = common_property_refs(p1, p2)
    rels = tuple(relation_facts) + relation_facts_between(p1, p2)
    candidate = build_composed_operator(op1, op2, common_properties=common, relation_facts=rels, new_ref_id=new_ref_id)
    return derive_operator(candidate, existing)


def describe_operator_structure(obj: RefObject) -> tuple:
    """Stable structural view for tests/replay traces."""
    return structural_signature(obj)
