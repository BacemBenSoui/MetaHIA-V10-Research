"""E20-D.17 — Emergent structure generation from a reified operation.

This layer tests the generative consequence of D15/D16 without adding a new
K3 primitive. A structurally synthesized operation is applied to operands that
need not already form an observed relation in the input graph. The produced
Node is a new structural object; its semantic meaning remains Unknown.

Contract:
  OperationRef + novel operands -> newly constructed Node
  - no semantic decoder
  - no requirement that the output relation existed in the source graph
  - provenance is explicit
  - reference identity remains separate from structure
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from kernel2 import Node, NodeRef, RefObject, OBSERVATION, apply_operator, structural_equal

EMERGENT_STATUS_CREATED = "CREATED_EMERGENT"
EMERGENT_STATUS_NOT_NEW = "NOT_NEW"


@dataclass(frozen=True)
class EmergentStructureResult:
    status: str
    structure: Node
    operation_ref: NodeRef
    operands: Tuple[object, ...]
    provenance: Tuple[str, ...]
    novelty_verified: bool


def _observed_contains(candidate: Node, observed: Iterable[Node]) -> bool:
    return any(structural_equal(candidate, item) for item in observed)


def generate_emergent_structure(
    operation: RefObject,
    *operands: object,
    observed: Iterable[Node] = (),
    node_id: Optional[str] = None,
    provenance: Tuple[str, ...] = (),
) -> EmergentStructureResult:
    """Apply a reified operation to operands and verify the result is novel."""
    if not isinstance(operation, RefObject):
        raise TypeError("operation must be a reference-bearing structural object")
    if not operands:
        raise ValueError("at least one operand is required")

    result = apply_operator(
        operation,
        *operands,
        node_id=node_id,
        provenance=provenance,
    )
    is_new = not _observed_contains(result, observed)
    return EmergentStructureResult(
        status=EMERGENT_STATUS_CREATED if is_new else EMERGENT_STATUS_NOT_NEW,
        structure=result,
        operation_ref=operation.ref,
        operands=tuple(operands),
        provenance=tuple(provenance),
        novelty_verified=is_new,
    )


def structural_trace(result: EmergentStructureResult) -> tuple:
    return (
        result.status,
        result.operation_ref,
        result.operands,
        result.structure,
        result.provenance,
        result.novelty_verified,
    )
