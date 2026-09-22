"""P4-T.2 -- locked benchmark: TRAIN + HOLDOUT-SOURCE cases (no truth here).

This module contains ONLY what a genuine blind protocol is allowed to see
before prediction: training rows (source AND target, used for discovery)
and holdout source observations (target withheld entirely -- not masked
with a placeholder, simply absent, exactly like every existing P4-T test's
own non-circularity discipline). The ground truth for every holdout case
lives exclusively in `p4t_locked_benchmark_witness_v0_1.py`, a separate
file this module never imports and has no need to.

Seven cases, spanning every family P4-T currently supports plus the two
fail-closed outcomes (Gate E), so this is a genuine cross-family benchmark,
not a repeat of any single existing unit test under a new name. All
entity names are unique to this file (prefixed `c0N_`) and were never used
in any other P4-T test or corpus in this repository.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

from kernel2 import Node, NodeRef, OBSERVATION


def _row(row_id: str, op: str, source, target) -> Node:
    return Node(row_id, OBSERVATION, (NodeRef(op), source, target))


@dataclass(frozen=True)
class LockedCase:
    case_id: str
    family_expected: str
    source_position: int
    target_position: int
    train_rows: Tuple[Node, ...]
    holdout_source: Tuple[object, ...] = ()  # empty for AMBIGUOUS/REJECTED cases
    # Only for family_expected == "COMPOSED": the two sub-transformations to
    # discover independently and then chain via compose_frozen().
    composed_inner_rows: Optional[Tuple[Node, ...]] = None
    composed_outer_rows: Optional[Tuple[Node, ...]] = None


# --- C01: plain row-permutation -------------------------------------------
_C01_TRAIN = (
    Node("c01_train1", OBSERVATION, (NodeRef("c01_u"), NodeRef("c01_v"))),
    Node("c01_train2", OBSERVATION, (NodeRef("c01_v"), NodeRef("c01_u"))),
    Node("c01_train3", OBSERVATION, (NodeRef("c01_w"), NodeRef("c01_w"))),
)
_C01_HOLDOUT = (NodeRef("c01_fresh1"), NodeRef("c01_fresh2"), NodeRef("c01_fresh3"))

# --- C02: recursive (nested) permutation -----------------------------------
_C02_TRAIN = tuple(
    _row(
        f"c02_row{i}",
        f"c02_op{i}",
        Node(f"c02_src{i}", OBSERVATION, ("O", NodeRef(f"c02_{i}p"), NodeRef(f"c02_{i}q"), NodeRef("c02_z"))),
        Node(f"c02_tgt{i}", OBSERVATION, ("O", NodeRef(f"c02_{i}q"), NodeRef(f"c02_{i}p"), NodeRef("c02_z"))),
    )
    for i in range(1, 4)
)
_C02_HOLDOUT = tuple(
    Node(f"c02_hsrc{i}", OBSERVATION, ("O", NodeRef(f"c02_h{i}p"), NodeRef(f"c02_h{i}q"), NodeRef("c02_hz")))
    for i in range(1, 4)
)

# --- C03: projection (arity 3 -> 1, picks position 0) ----------------------
_C03_TRAIN = tuple(
    _row(
        f"c03_row{i}",
        f"c03_op{i}",
        Node(f"c03_src{i}", OBSERVATION, (NodeRef(f"c03_{i}a"), NodeRef(f"c03_{i}b"), NodeRef(f"c03_{i}c"))),
        Node(f"c03_tgt{i}", OBSERVATION, (NodeRef(f"c03_{i}a"),)),
    )
    for i in range(1, 4)
)
_C03_HOLDOUT = tuple(
    Node(f"c03_hsrc{i}", OBSERVATION, (NodeRef(f"c03_h{i}a"), NodeRef(f"c03_h{i}b"), NodeRef(f"c03_h{i}c")))
    for i in range(1, 4)
)

# --- C04: duplication (arity 2 -> 3, (a, a, b)) -----------------------------
_C04_TRAIN = tuple(
    _row(
        f"c04_row{i}",
        f"c04_op{i}",
        Node(f"c04_src{i}", OBSERVATION, (NodeRef(f"c04_{i}a"), NodeRef(f"c04_{i}b"))),
        Node(f"c04_tgt{i}", OBSERVATION, (NodeRef(f"c04_{i}a"), NodeRef(f"c04_{i}a"), NodeRef(f"c04_{i}b"))),
    )
    for i in range(1, 4)
)
_C04_HOLDOUT = tuple(
    Node(f"c04_hsrc{i}", OBSERVATION, (NodeRef(f"c04_h{i}a"), NodeRef(f"c04_h{i}b")))
    for i in range(1, 4)
)

# --- C05: composition of two independently-frozen selection mappings ------
# inner: arity 3 -> 2, picks (position 2, position 0)
_C05_INNER_TRAIN = tuple(
    _row(
        f"c05i_row{i}",
        f"c05i_op{i}",
        Node(f"c05i_src{i}", OBSERVATION, (NodeRef(f"c05_{i}a"), NodeRef(f"c05_{i}b"), NodeRef(f"c05_{i}c"))),
        Node(f"c05i_tgt{i}", OBSERVATION, (NodeRef(f"c05_{i}c"), NodeRef(f"c05_{i}a"))),
    )
    for i in range(1, 4)
)
# outer: arity 2 -> 1, picks position 1 (i.e. inner's own position 0, "c")
_C05_OUTER_TRAIN = tuple(
    _row(
        f"c05o_row{i}",
        f"c05o_op{i}",
        Node(f"c05o_src{i}", OBSERVATION, (NodeRef(f"c05_{i}m0"), NodeRef(f"c05_{i}m1"))),
        Node(f"c05o_tgt{i}", OBSERVATION, (NodeRef(f"c05_{i}m1"),)),
    )
    for i in range(1, 4)
)
_C05_HOLDOUT = tuple(
    Node(f"c05_hsrc{i}", OBSERVATION, (NodeRef(f"c05_h{i}a"), NodeRef(f"c05_h{i}b"), NodeRef(f"c05_h{i}c")))
    for i in range(1, 4)
)

# --- C06: ambiguous by construction (Gate E) -------------------------------
_C06_SHARED = tuple(NodeRef(f"c06_s{i}") for i in range(3))
_C06_TRAIN = tuple(
    _row(
        f"c06_row{i}",
        f"c06_op{i}",
        Node(f"c06_src{i}", OBSERVATION, (_C06_SHARED[i], _C06_SHARED[i], NodeRef(f"c06_{i}c"))),
        Node(f"c06_tgt{i}", OBSERVATION, (_C06_SHARED[i],)),
    )
    for i in range(3)
)

# --- C07: rejected by construction (Gate E, constant target) --------------
_C07_TRAIN = tuple(
    _row(
        f"c07_row{i}",
        f"c07_op{i}",
        Node(f"c07_src{i}", OBSERVATION, (NodeRef(f"c07_{i}a"), NodeRef(f"c07_{i}b"))),
        Node(f"c07_tgt{i}", OBSERVATION, (NodeRef("c07_CONST"),)),
    )
    for i in range(3)
)


LOCKED_CASES: Tuple[LockedCase, ...] = (
    LockedCase("C01_PERMUTATION", "COMPARE_PERMUTATION", 0, 1, _C01_TRAIN, _C01_HOLDOUT),
    LockedCase("C02_RECURSIVE_PERMUTATION", "COMPARE_RECURSIVE", 1, 2, _C02_TRAIN, _C02_HOLDOUT),
    LockedCase("C03_PROJECTION", "SELECTION_MAPPING", 1, 2, _C03_TRAIN, _C03_HOLDOUT),
    LockedCase("C04_DUPLICATION", "SELECTION_MAPPING", 1, 2, _C04_TRAIN, _C04_HOLDOUT),
    LockedCase(
        "C05_COMPOSITION", "COMPOSED", 1, 2, (),
        holdout_source=_C05_HOLDOUT,
        composed_inner_rows=_C05_INNER_TRAIN,
        composed_outer_rows=_C05_OUTER_TRAIN,
    ),
    LockedCase("C06_AMBIGUOUS", "AMBIGUOUS", 1, 2, _C06_TRAIN),
    LockedCase("C07_REJECTED", "REJECTED", 1, 2, _C07_TRAIN),
)


__all__ = ["LockedCase", "LOCKED_CASES"]
