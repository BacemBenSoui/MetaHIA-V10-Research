"""MetaHIA E20-D.7 — structural operator-property discovery v0.1.

Goal
----
Discover operator properties from behaviour observations *without* providing
semantic property names such as COMMUTATIVE or ITERATIVE in the input corpus.
The mechanism only uses generic structural facts:
  - operator identity is a NodeRef;
  - input positions are references;
  - output identity/structure can be compared with those references;
  - alternative input arrangements can be compared;
  - discovered regularities are reified as opaque structural objects.

This is deliberately a microstructural experiment. It does not claim that a
particular derived token means a mathematical property; it only creates a
reference-bearing evidence object describing an observed invariant.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple

from kernel2 import Node, NodeRef, RefObject, OBSERVATION, reference_equal, structural_equal, ref_object

PROPERTY_DISCOVERY = "PROPERTY_DISCOVERY"
WITNESS_SET = "WITNESS_SET"
INVARIANT = "INVARIANT"
PERMUTATION = "PERMUTATION"
SELF_REFERENCE = "SELF_REFERENCE"


@dataclass(frozen=True)
class BehaviorCase:
    operator: NodeRef
    inputs: Tuple[NodeRef, ...]
    output: object
    case_id: str


def behavior_case(case_id: str, operator: NodeRef | str, inputs: Iterable[NodeRef], output: object) -> BehaviorCase:
    op = operator if isinstance(operator, NodeRef) else NodeRef(operator)
    return BehaviorCase(op, tuple(inputs), output, case_id)


def _obs(case: BehaviorCase) -> Node:
    return Node(case.case_id, OBSERVATION, (case.operator,) + case.inputs + (case.output,))


def _same_ref_tuple(a: Sequence[object], b: Sequence[object]) -> bool:
    return len(a) == len(b) and all(
        reference_equal(x, y) if isinstance(x, NodeRef) and isinstance(y, NodeRef) else structural_equal(x, y)
        for x, y in zip(a, b)
    )


def discover_arity(cases: Sequence[BehaviorCase]) -> Optional[int]:
    if not cases:
        return None
    arities = {len(c.inputs) for c in cases}
    return next(iter(arities)) if len(arities) == 1 else None


def discover_fixed_point(cases: Sequence[BehaviorCase]) -> bool:
    """Observe x -> x using reference identity, not payload equality."""
    return any(
        isinstance(c.output, NodeRef)
        and len(c.inputs) == 1
        and reference_equal(c.output, c.inputs[0])
        for c in cases
    )


def _index_by_input_refs(cases: Sequence[BehaviorCase]) -> Dict[Tuple[str, ...], BehaviorCase]:
    out: Dict[Tuple[str, ...], BehaviorCase] = {}
    for c in cases:
        if all(isinstance(x, NodeRef) for x in c.inputs):
            out[tuple(x.ref_id for x in c.inputs)] = c  # type: ignore[arg-type]
    return out


def discover_output_invariance_under_swap(cases: Sequence[BehaviorCase]) -> Optional[Node]:
    """Discover a generic 2-slot output invariant under swapping input refs.

    No semantic label is assumed. The emitted structure records the witness:
    the same operator, the same output reference/structure, and a swap of
    input positions.
    """
    two = [c for c in cases if len(c.inputs) == 2 and all(isinstance(x, NodeRef) for x in c.inputs)]
    by_inputs = _index_by_input_refs(two)
    for c in two:
        a, b = c.inputs
        if not isinstance(a, NodeRef) or not isinstance(b, NodeRef):
            continue
        twin = by_inputs.get((b.ref_id, a.ref_id))
        if twin is None or not reference_equal(c.operator, twin.operator):
            continue
        same_out = (
            reference_equal(c.output, twin.output)
            if isinstance(c.output, NodeRef) and isinstance(twin.output, NodeRef)
            else structural_equal(c.output, twin.output)
        )
        if same_out:
            return Node(
                f"swap-invariant::{c.case_id}::{twin.case_id}",
                INVARIANT,
                (
                    c.operator,
                    NodeRef("ARITY:2"),
                    Node(PERMUTATION, WITNESS_SET, (NodeRef("pos1->pos2"), NodeRef("pos2->pos1"))),
                    Node(WITNESS_SET, PROPERTY_DISCOVERY, (NodeRef(c.case_id), NodeRef(twin.case_id))),
                ),
            )
    return None


def build_discovered_property(
    cases: Sequence[BehaviorCase],
    *,
    property_ref_id: str = "PROP::derived",
) -> Optional[RefObject]:
    """Aggregate only *observed* structural invariants into a new property object."""
    arity = discover_arity(cases)
    if arity is None:
        return None
    children = [NodeRef(f"ARITY:{arity}")]
    if discover_fixed_point(cases):
        children.append(Node(SELF_REFERENCE, PROPERTY_DISCOVERY, (NodeRef("observed"),)))
    swap = discover_output_invariance_under_swap(cases)
    if swap is not None:
        children.append(swap)
    if len(children) == 1:
        return ref_object(property_ref_id, Node("derived-properties", PROPERTY_DISCOVERY, tuple(children)))
    return ref_object(property_ref_id, Node("derived-properties", PROPERTY_DISCOVERY, tuple(children)))
