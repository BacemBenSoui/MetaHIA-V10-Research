"""MetaHIA E20-D.5 — behavioral/property-to-operator discovery v0.1.

Goal: derive operator relations from observed structural behaviour, without
assigning semantic meaning to operator labels such as '+', '*', etc.

This layer deliberately uses only generic structure:
  - an operator application is an OBSERVATION whose first child is its operator;
  - another observation can be a structural expansion/witness containing an
    operator reference recursively;
  - repeated source operands in an expansion are preserved by reference;
  - candidate relations are structural facts, not semantic operator labels.

E20-D.5 therefore tests only whether a relation such as

    operator O2 -> structural expansion using O1

can be DISCOVERED from paired behaviour witnesses, then reified as a
reference-bearing relation object. It does not assert that a specific label
means multiplication/addition/iteration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from kernel2 import Node, NodeRef, RefObject, OBSERVATION, reference_equal, structural_equal, ref_object
from operator_space_v0_1 import OPERATOR_RELATION, OPERATOR_EVIDENCE, operator_relation_fact, operator_profile, identify_existing_operator

BEHAVIOR_WITNESS = "BEHAVIOR_WITNESS"
EMBEDDED_OPERATOR = "EMBEDDED_OPERATOR"
REPETITION_COUNT = "REPETITION_COUNT"


@dataclass(frozen=True)
class BehaviorWitness:
    operator: NodeRef
    application: Node
    witness: Node
    source_id: str
    witness_id: str


@dataclass(frozen=True)
class BehavioralRelation:
    source_operator: NodeRef
    target_operator: NodeRef
    relation_structure: Node
    evidence: Tuple[str, ...]
    repeat_count: Optional[int] = None


def behavior_witness(source: Node, witness: Node) -> BehaviorWitness:
    if source.kind != OBSERVATION or not source.children:
        raise ValueError("source must be a non-empty OBSERVATION")
    op = source.children[0]
    if not isinstance(op, NodeRef):
        raise ValueError("source operator must be NodeRef")
    return BehaviorWitness(op, source, witness, source.node_id, witness.node_id)


def _contains_operator(obj: object, target: NodeRef) -> int:
    """Count structural occurrences of target NodeRef recursively."""
    if isinstance(obj, NodeRef):
        return int(reference_equal(obj, target))
    if isinstance(obj, RefObject):
        return _contains_operator(obj.structure, target)
    if isinstance(obj, Node):
        return sum(_contains_operator(x, target) for x in obj.children)
    if isinstance(obj, tuple):
        return sum(_contains_operator(x, target) for x in obj)
    if isinstance(obj, list):
        return sum(_contains_operator(x, target) for x in obj)
    return 0


def _build_relation(source_op: NodeRef, witness_op: NodeRef, repeat_count: int) -> Node:
    children = (
        source_op,
        witness_op,
        Node("evidence", OPERATOR_EVIDENCE, (
            NodeRef(EMBEDDED_OPERATOR),
            NodeRef(f"{REPETITION_COUNT}:{repeat_count}"),
        )),
    )
    return Node(
        f"behavior-rel::{witness_op.ref_id}::{source_op.ref_id}::{repeat_count}",
        OPERATOR_RELATION,
        children,
    )


def discover_embedded_operator_relation(
    witnesses: Sequence[BehaviorWitness], *, min_evidence: int = 3
) -> Optional[BehavioralRelation]:
    """Discover an operator relation from repeated structural witnesses.

    For each witness pair, the target operator must occur recursively in the
    witness structure at least twice (root + nested occurrence). The observed
    occurrence count is recorded. The rule is purely structural: it does not
    interpret the operator label or call the relation "multiplication" or
    "iteration".
    All rows must agree on source/target identities and count. Otherwise the
    result is None (fail closed).
    """
    if len(witnesses) < min_evidence:
        raise ValueError(f"E20-D.5 requires at least {min_evidence} behavior witnesses")
    source_op = witnesses[0].operator
    witness_op = witnesses[0].witness.children[0] if witnesses[0].witness.children else None
    if not isinstance(witness_op, NodeRef):
        raise ValueError("witness must expose an operator in its first position")
    counts = []
    evidence = []
    for w in witnesses:
        op = w.witness.children[0] if w.witness.children else None
        if not isinstance(op, NodeRef):
            return None
        if not reference_equal(w.operator, source_op) or not reference_equal(op, witness_op):
            return None
        # The witness operator must appear structurally beyond its root.
        # The root occurrence alone is not evidence that source_op is related
        # to target_op; repeated target_op embedding is the observable fact.
        count = _contains_operator(w.witness, witness_op)
        if count < 2:
            return None
        counts.append(count)
        evidence.append(f"{w.source_id}->{w.witness_id}")
    if len(set(counts)) != 1:
        return None
    relation = _build_relation(source_op, witness_op, counts[0])
    return BehavioralRelation(source_op, witness_op, relation, tuple(evidence), counts[0])


def relation_as_ref(relation: BehavioralRelation, ref_id: str = "OPREL::derived") -> RefObject:
    return ref_object(ref_id, relation.relation_structure)


def identify_or_create_relation(
    relation: BehavioralRelation,
    existing: Sequence[RefObject] = (),
    *,
    new_ref_id: str = "OPREL::derived",
) -> Tuple[str, RefObject]:
    candidate = relation_as_ref(relation, new_ref_id)
    hit = identify_existing_operator(candidate, existing)
    if hit is not None:
        return "IDENTIFIED_EXISTING", hit
    return "CREATED_NEW", candidate


def cumulative_property_structure(source_profile: Node, target_profile: Node, relation: BehavioralRelation) -> Node:
    """Create a purely structural cumulative property object.

    The operator labels remain NodeRef identities; properties are copied only
    when they are structurally common. The behavioral relation is attached as
    another structural child. No property is interpreted semantically.
    """
    p1 = source_profile.children[2] if len(source_profile.children) > 2 else None
    p2 = target_profile.children[2] if len(target_profile.children) > 2 else None
    props1 = p1.children if isinstance(p1, Node) else ()
    props2 = p2.children if isinstance(p2, Node) else ()
    common = tuple(x for x in props1 if isinstance(x, NodeRef) and any(structural_equal(x, y) for y in props2 if isinstance(y, NodeRef)))
    return Node(
        "cumulative-properties",
        OPERATOR_EVIDENCE,
        (
            Node("common", OPERATOR_EVIDENCE, common),
            relation.relation_structure,
        ),
    )
