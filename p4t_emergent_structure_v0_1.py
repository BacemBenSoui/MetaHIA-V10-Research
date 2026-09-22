"""P4-T.5 -- emergent structure generation from a frozen transformation.

Partially covers E20-D.17's own goal (`e20d_emergent_structure_v0_1.py`):
apply a reified, already-learned operation to operands that need not
already form an observed relation anywhere in the graph, and verify the
result is genuinely NEW -- using a P4-T `FrozenTransformation` as the
reified operation instead of E20-D.17's own `RefObject`-wrapped operator.

Why this is a PARALLEL function, not a call to
`e20d_emergent_structure_v0_1.generate_emergent_structure()` (same
architectural discipline already applied by P4-T.6, which refused to
fabricate a fake `kernel2.PathRecord` to call E20-D.19's
`score_candidate()`): that function requires a `RefObject`-wrapped
operator and applies it via `kernel2.apply_operator()`, which literally
produces `Node(node_id, kind, (operator.ref, *operands))` -- one fixed
ref prepended in front of the operands, nothing more. A P4-T
`FrozenTransformation` is not that kind of object: it is a genuine
positional/pattern transformation (permutation, recursive swap,
selection mapping, composition), already applied via `blind_replay()`
(unmodified, reused here exactly as-is). Forcing `FrozenTransformation`
through `apply_operator()`'s single-prepend semantics would either not
type-check (it is not a `RefObject`) or silently discard the actual
transformation logic it carries -- exactly the kind of forced comparison
this project already refuses elsewhere.

What this module adds on top of an unmodified `blind_replay()`:
E20-D.17's own contract requires the produced structure to be verified
NOVEL against a caller-supplied `observed` set, via
`kernel2.structural_equal` and never by payload semantics (mirrored here
from `e20d_emergent_structure_v0_1.py`'s own
`test_novelty_check_does_not_use_payload_semantics`). `blind_replay()`
itself makes no such claim -- it only predicts, and never checks the
prediction against anything. `generate_emergent_structure_from_frozen()`
below is exactly that missing check, layered on top.

Explicit scope boundary, stated plainly rather than left implicit: the
produced structure's semantic meaning remains Unknown, exactly like
E20-D.17's own contract states for its own mechanism -- this module
proves the structure is new and traceable to its generating
transformation, never what it "means".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from kernel2 import Node, structural_equal
import p4t_structural_transformation_induction_v0_1 as p4t

EMERGENT_STATUS_CREATED = "CREATED_EMERGENT"
EMERGENT_STATUS_NOT_NEW = "NOT_NEW"
EMERGENT_STATUS_NO_PREDICTION = "NO_PREDICTION"


@dataclass(frozen=True)
class EmergentStructureResultP4T:
    status: str
    structure: Optional[Node]
    operation_digest: str
    operand: object
    provenance: Tuple[str, ...]
    novelty_verified: bool


def generate_emergent_structure_from_frozen(
    frozen: p4t.FrozenTransformation,
    operand: Node,
    *,
    observed: Iterable[Node] = (),
) -> EmergentStructureResultP4T:
    """Applies `frozen` (already gated through discover/select/freeze) to
    a single novel `operand` that need not already form an observed
    relation anywhere in the training data -- E20-D.17's own contract,
    adapted to a P4-T transformation. `frozen.structural_digest` (already
    canonical and training-entity-invariant since P4-T.1 bis) stands in
    for E20-D.17's `RefObject.ref` as the identity of "which operation
    produced this".

    Fail-closed, never guesses: if `blind_replay()` itself cannot produce
    a prediction (a genuine shape/arity mismatch between `operand` and
    what `frozen` expects -- the only way this happens, since a REJECTED/
    AMBIGUOUS candidate can never reach `freeze()` in the first place),
    this reports `NO_PREDICTION` rather than fabricating a structure.
    """
    predictions = p4t.blind_replay(frozen, (operand,))
    structure = predictions[0] if predictions else None
    if structure is None:
        return EmergentStructureResultP4T(
            status=EMERGENT_STATUS_NO_PREDICTION,
            structure=None,
            operation_digest=frozen.structural_digest,
            operand=operand,
            provenance=(),
            novelty_verified=False,
        )
    is_new = not any(structural_equal(structure, item) for item in observed)
    return EmergentStructureResultP4T(
        status=EMERGENT_STATUS_CREATED if is_new else EMERGENT_STATUS_NOT_NEW,
        structure=structure,
        operation_digest=frozen.structural_digest,
        operand=operand,
        provenance=structure.provenance,
        novelty_verified=is_new,
    )


# ---------------------------------------------------------------------------
# Real, verified-by-execution scope boundary -- not a bug to route around.
#
# `blind_replay()` has two genuinely different replay mechanisms depending
# on family: SELECTION_MAPPING (FAMILY_SELECTION_MAPPING) applies row by
# row, independently -- exactly the "one novel operand -> one new
# structure" shape this module's single-`operand` signature assumes. The
# pattern-based families (REFERENCE_EQUALITY, COMPARE_PERMUTATION,
# COMPARE_RECURSIVE) instead replay a BATCH matching the original
# training row count all at once (confirmed by direct execution: the
# frozen PATTERN's own top-level arity equals the training row count, so
# `apply()` shape-matches only against a same-size batch -- e.g. P4-T.2's
# own locked C02 case already replays on exactly 3 fresh holdout rows,
# never one at a time). Calling `generate_emergent_structure_from_frozen()`
# with a single `operand` against one of those families therefore
# correctly reports `NO_PREDICTION` (verified directly, not assumed) --
# fail-closed, never a wrong guess -- rather than the `CREATED_EMERGENT`
# this module demonstrates for SELECTION_MAPPING. Extending this module to
# cover pattern-based families with their own correct batch-shaped
# operand, and P4-T.4's multi-source families (`blind_replay_multi_source()`,
# a different calling convention entirely), is left as an explicitly
# disclosed extension point, not attempted here.
# ---------------------------------------------------------------------------


__all__ = [
    "EMERGENT_STATUS_CREATED",
    "EMERGENT_STATUS_NOT_NEW",
    "EMERGENT_STATUS_NO_PREDICTION",
    "EmergentStructureResultP4T",
    "generate_emergent_structure_from_frozen",
]
