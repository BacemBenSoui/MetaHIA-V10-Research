"""P4-T.5 -- emergent structure generation from a frozen transformation.

Mirrors `tests/test_e20d17_emergent_structure_v0_1.py`'s own coverage
shape (novelty against an observed set, exact-duplicate rejection,
provenance preservation) for the P4-T-specific adapter in
`p4t_emergent_structure_v0_1.py`, plus coverage of a real scope boundary
discovered by direct execution before any test was written: a
pattern-based family (COMPARE_RECURSIVE) cannot produce a structure from
a single novel operand the way SELECTION_MAPPING can, since its frozen
replay mechanism requires a batch matching the original training row
count -- confirmed here as a permanent regression (fail-closed
`NO_PREDICTION`, never a wrong guess), not treated as a bug to route
around.
"""
from __future__ import annotations

from kernel2 import Node, NodeRef, OBSERVATION

import p4t_structural_transformation_induction_v0_1 as p4t
from p4t_emergent_structure_v0_1 import (
    EMERGENT_STATUS_CREATED,
    EMERGENT_STATUS_NOT_NEW,
    EMERGENT_STATUS_NO_PREDICTION,
    generate_emergent_structure_from_frozen,
)


def _row(row_id: str, op: str, source, target) -> Node:
    return Node(row_id, OBSERVATION, (NodeRef(op), source, target))


def _frozen_projection(frozen_id: str) -> p4t.FrozenTransformation:
    """Arity 3 -> 1, picks position 0 -- the same shape as P4-T.2's own
    C03/V2C01 locked cases, built fresh here to keep this test file
    self-contained."""
    rows = tuple(
        _row(
            f"row{i}", f"op{i}",
            Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c"))),
            Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),)),
        )
        for i in range(1, 4)
    )
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    return p4t.freeze(candidate, frozen_id=frozen_id)


def _frozen_duplication(frozen_id: str) -> p4t.FrozenTransformation:
    """Arity 2 -> 3, (a, a, b)."""
    rows = tuple(
        _row(
            f"row{i}", f"op{i}",
            Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"))),
            Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}a"), NodeRef(f"{i}b"))),
        )
        for i in range(1, 4)
    )
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    return p4t.freeze(candidate, frozen_id=frozen_id)


def _frozen_recursive_permutation(frozen_id: str) -> p4t.FrozenTransformation:
    rows = tuple(
        _row(
            f"row{i}", f"op{i}",
            Node(f"rsrc{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("z"))),
            Node(f"rtgt{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("z"))),
        )
        for i in range(1, 4)
    )
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.family == p4t.FAMILY_RECURSIVE_PERMUTATION
    return p4t.freeze(candidate, frozen_id=frozen_id)


def test_projection_applied_to_a_genuinely_novel_operand_creates_emergent_structure():
    """The operand here was never part of any training row, and `observed`
    is empty -- matching E20-D.17's own contract: "operands need not
    already form an observed relation in the input graph"."""
    frozen = _frozen_projection("EM_PROJ_1")
    novel_operand = Node("novel_src", OBSERVATION, (NodeRef("FOREIGN_P"), NodeRef("FOREIGN_Q"), NodeRef("FOREIGN_R")))
    result = generate_emergent_structure_from_frozen(frozen, novel_operand, observed=[])
    assert result.status == EMERGENT_STATUS_CREATED
    assert result.novelty_verified
    assert result.structure.children == (NodeRef("FOREIGN_P"),)
    assert result.operation_digest == frozen.structural_digest


def test_exact_observed_structure_is_not_claimed_novel():
    """Mirrors e20d_emergent_structure_v0_1.py's own
    test_exact_observed_structure_is_not_claimed_novel: if the predicted
    structure is already present in `observed` (structural_equal, never
    payload-only), it must not be reported as newly created."""
    frozen = _frozen_projection("EM_PROJ_2")
    operand = Node("src", OBSERVATION, (NodeRef("X"), NodeRef("Y"), NodeRef("Z")))
    first = generate_emergent_structure_from_frozen(frozen, operand, observed=[])
    assert first.status == EMERGENT_STATUS_CREATED
    second = generate_emergent_structure_from_frozen(frozen, operand, observed=[first.structure])
    assert second.status == EMERGENT_STATUS_NOT_NEW
    assert not second.novelty_verified


def test_duplication_family_also_produces_novel_structure():
    """Confirms the adapter is not SELECTION_MAPPING-subtype-specific --
    duplication (arity-increasing) works exactly like projection
    (arity-decreasing), both via the same row-independent blind_replay
    branch."""
    frozen = _frozen_duplication("EM_DUP_1")
    novel_operand = Node("novel", OBSERVATION, (NodeRef("FOREIGN_A"), NodeRef("FOREIGN_B")))
    result = generate_emergent_structure_from_frozen(frozen, novel_operand, observed=[])
    assert result.status == EMERGENT_STATUS_CREATED
    assert result.structure.children == (NodeRef("FOREIGN_A"), NodeRef("FOREIGN_A"), NodeRef("FOREIGN_B"))


def test_pattern_based_family_with_a_single_operand_fails_closed_not_created():
    """Real scope boundary, verified by direct execution before this test
    was written (not assumed): COMPARE_RECURSIVE's frozen replay
    mechanism requires a batch matching the original training row count
    (its own top-level PATTERN arity), so a single novel operand can
    never shape-match. This module must report NO_PREDICTION here, never
    fabricate a structure from a shape it cannot actually apply."""
    frozen = _frozen_recursive_permutation("EM_RECURSIVE_1")
    novel_operand = Node("novel", OBSERVATION, ("O", NodeRef("FOREIGN_X"), NodeRef("FOREIGN_Y"), NodeRef("FOREIGN_Z")))
    result = generate_emergent_structure_from_frozen(frozen, novel_operand, observed=[])
    assert result.status == EMERGENT_STATUS_NO_PREDICTION
    assert result.structure is None
    assert not result.novelty_verified


def test_shape_mismatch_within_selection_mapping_also_fails_closed():
    """A SELECTION_MAPPING frozen transformation given an operand of the
    wrong arity must also refuse rather than guess -- the same
    fail-closed discipline `_blind_replay_one` already enforces, verified
    here through this module's own entry point."""
    frozen = _frozen_projection("EM_PROJ_BAD_SHAPE")
    wrong_arity_operand = Node("bad", OBSERVATION, (NodeRef("ONLY_ONE"),))
    result = generate_emergent_structure_from_frozen(frozen, wrong_arity_operand, observed=[])
    assert result.status == EMERGENT_STATUS_NO_PREDICTION
    assert result.structure is None


def test_operation_digest_distinguishes_two_different_frozen_transformations():
    """frozen.structural_digest (already canonical and training-entity-
    invariant since P4-T.1 bis) is this module's stand-in for E20-D.17's
    RefObject.ref identity -- confirms it is actually discriminating, not
    a constant placeholder."""
    frozen_proj = _frozen_projection("EM_DIGEST_PROJ")
    frozen_dup = _frozen_duplication("EM_DIGEST_DUP")
    result_proj = generate_emergent_structure_from_frozen(
        frozen_proj, Node("s1", OBSERVATION, (NodeRef("A"), NodeRef("B"), NodeRef("C"))), observed=[]
    )
    result_dup = generate_emergent_structure_from_frozen(
        frozen_dup, Node("s2", OBSERVATION, (NodeRef("D"), NodeRef("E"))), observed=[]
    )
    assert result_proj.operation_digest != result_dup.operation_digest


def test_provenance_is_preserved_on_emergent_structure():
    frozen = _frozen_projection("EM_PROV")
    operand = Node("src", OBSERVATION, (NodeRef("X"), NodeRef("Y"), NodeRef("Z")))
    result = generate_emergent_structure_from_frozen(frozen, operand, observed=[])
    assert result.provenance == result.structure.provenance
    assert result.provenance == ("EM_PROV", "src")


def test_emergent_result_structure_is_still_an_ordinary_k3_node():
    frozen = _frozen_projection("EM_NODE")
    operand = Node("src", OBSERVATION, (NodeRef("X"), NodeRef("Y"), NodeRef("Z")))
    result = generate_emergent_structure_from_frozen(frozen, operand, observed=[])
    assert isinstance(result.structure, Node)
    assert result.structure.kind == OBSERVATION
