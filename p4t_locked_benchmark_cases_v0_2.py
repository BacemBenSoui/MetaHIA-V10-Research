"""P4-T.2 v0.2 -- locked benchmark, TRAIN + HOLDOUT-SOURCE cases (no truth here).

Rebuild of `p4t_locked_benchmark_cases_v0_1.py` addressing two gaps an
external review identified in that first version (2026-09-22 review,
Sections 10-11 -- explicitly framed as later steps, done here by request
after the P4-T.1 bis opacity fix landed separately):

1. `p4t_locked_benchmark_runner_v0_1.py` calls `discover()` directly with
   `source_position`/`target_position` taken straight from each
   `LockedCase` -- the benchmark tells the mechanism which columns to
   compare. P4-T.3's own hypothesis-enumeration/selection layer
   (`discover_all_hypotheses()`/`select_hypothesis()`) exists as a unit
   mechanism but was never exercised inside the locked protocol. This
   version's cases carry NO position fields at all -- see
   `LockedCaseV2` below -- because finding the right position pair is now
   the mechanism's own job, done by
   `p4t_locked_benchmark_runner_v0_2.py`, not asserted by the test data.
2. The review asked for a case with >=2 valid hypotheses that still
   resolves to one unique winner, and a case with >=2 hypotheses tied at
   the same complexity rank (`AMBIGUOUS_SELECTION`). Both are included
   here, verified by direct execution before being locked in (see
   `documentation/P4T2_Locked_Benchmark_V0_1.md` Sec. 6bis for the
   verification trail) -- not assumed from how the training rows "should"
   behave.

A real, honest finding from that verification, disclosed here rather than
engineered around: a bare two-Node-position row (source and target and
nothing else) is directionally ambiguous under real end-to-end selection
for a SELF-INVERSE family (COMPARE_PERMUTATION, COMPARE_RECURSIVE) --
swapping twice undoes itself, so both directions are equally valid
hypotheses and `select_hypothesis()` correctly reports a tie, never
picking one arbitrarily. This is the same "genuinely undirected relation"
property already documented for REFERENCE_EQUALITY
(`p4t_structural_transformation_induction_v0_1.py`'s own
`discover_all_hypotheses` docstring), now confirmed to extend to
permutation-family self-inverse operations too, not previously exercised
end-to-end. Arity-changing SELECTION_MAPPING families (projection,
duplication) are NOT self-inverse in general and were confirmed, by the
same direct execution, to retain a unique hypothesis from a bare
two-Node-position row.

Same non-circularity discipline as v0.1: holdout observations carry
SOURCE information only, never a target, masked or otherwise. Every
entity name in this file uses a `v2c0N_` prefix disjoint from
`p4t_locked_benchmark_cases_v0_1.py`'s `c0N_` prefix and from every other
existing P4-T corpus in this repository -- and holdout entities are
disjoint from training entities within each case too, the exact property
whose absence P4-T.1 bis had to fix for v0.1's C02 (see
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 6.2).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from kernel2 import Node, NodeRef, OBSERVATION


def _row(row_id: str, op: str, source, target) -> Node:
    return Node(row_id, OBSERVATION, (NodeRef(op), source, target))


@dataclass(frozen=True)
class LockedCaseV2:
    case_id: str
    family_expected: Optional[str]  # None when no single family applies (AMBIGUOUS_SELECTION / NO_HYPOTHESES)
    expected_selection_outcome: str  # "RETAINED" | "AMBIGUOUS_SELECTION" | "NO_HYPOTHESES"
    train_rows: Tuple[Node, ...]
    holdout_source: Tuple[object, ...] = ()
    # Only for family_expected == "COMPOSED": discover_all_hypotheses() +
    # select_hypothesis() are run independently on each of these two row
    # sets (both were confirmed, by direct execution, to retain a unique
    # hypothesis on their own), then the two resulting frozen
    # transformations are chained via compose_frozen() exactly like v0.1.
    composed_inner_rows: Optional[Tuple[Node, ...]] = None
    composed_outer_rows: Optional[Tuple[Node, ...]] = None


# --- V2C01: projection (arity 3 -> 1), a single discoverable hypothesis ----
_V2C01_TRAIN = tuple(
    _row(
        f"v2c01_row{i}",
        f"v2c01_op{i}",
        Node(f"v2c01_src{i}", OBSERVATION, (NodeRef(f"v2c01_{i}a"), NodeRef(f"v2c01_{i}b"), NodeRef(f"v2c01_{i}c"))),
        Node(f"v2c01_tgt{i}", OBSERVATION, (NodeRef(f"v2c01_{i}a"),)),
    )
    for i in range(1, 4)
)
_V2C01_HOLDOUT = tuple(
    Node(f"v2c01_hsrc{i}", OBSERVATION, (NodeRef(f"v2c01_h{i}a"), NodeRef(f"v2c01_h{i}b"), NodeRef(f"v2c01_h{i}c")))
    for i in range(1, 4)
)

# --- V2C02: duplication (arity 2 -> 3), a single discoverable hypothesis --
_V2C02_TRAIN = tuple(
    _row(
        f"v2c02_row{i}",
        f"v2c02_op{i}",
        Node(f"v2c02_src{i}", OBSERVATION, (NodeRef(f"v2c02_{i}a"), NodeRef(f"v2c02_{i}b"))),
        Node(f"v2c02_tgt{i}", OBSERVATION, (NodeRef(f"v2c02_{i}a"), NodeRef(f"v2c02_{i}a"), NodeRef(f"v2c02_{i}b"))),
    )
    for i in range(1, 4)
)
_V2C02_HOLDOUT = tuple(
    Node(f"v2c02_hsrc{i}", OBSERVATION, (NodeRef(f"v2c02_h{i}a"), NodeRef(f"v2c02_h{i}b")))
    for i in range(1, 4)
)

# --- V2C03: two competing families in one row -- a rank-3 COMPARE_RECURSIVE
# tie ((0,1) and (1,0), self-inverse, same complexity rank as each other)
# coexists with a rank-2 SELECTION_MAPPING hypothesis at (2,3). Verified by
# direct execution: discover_all_hypotheses() reports all three; the tie at
# rank 3 never enters the decision because only the single best rank (2) is
# compared, so (2,3)/SELECTION_MAPPING is retained uniquely.
_V2C03_TRAIN = tuple(
    Node(
        f"v2c03_row{i}",
        OBSERVATION,
        (
            Node(f"v2c03_rsrc{i}", OBSERVATION, ("O", NodeRef(f"v2c03_{i}x"), NodeRef(f"v2c03_{i}y"), NodeRef("v2c03_z"))),
            Node(f"v2c03_rtgt{i}", OBSERVATION, ("O", NodeRef(f"v2c03_{i}y"), NodeRef(f"v2c03_{i}x"), NodeRef("v2c03_z"))),
            Node(f"v2c03_psrc{i}", OBSERVATION, (NodeRef(f"v2c03_{i}a"), NodeRef(f"v2c03_{i}b"), NodeRef(f"v2c03_{i}c"))),
            Node(f"v2c03_ptgt{i}", OBSERVATION, (NodeRef(f"v2c03_{i}a"),)),
        ),
    )
    for i in range(1, 4)
)
# Holdout mirrors ONLY the winning hypothesis's source shape (position 2,
# the psrc 3-tuple) -- the recursive columns (positions 0-1) exist purely
# to make selection do real work during training and are not needed at
# replay time, exactly as kernel2/P4-T's mechanism only ever reads the
# source position the retained hypothesis actually names.
_V2C03_HOLDOUT = tuple(
    Node(f"v2c03_hsrc{i}", OBSERVATION, (NodeRef(f"v2c03_h{i}a"), NodeRef(f"v2c03_h{i}b"), NodeRef(f"v2c03_h{i}c")))
    for i in range(1, 4)
)

# --- V2C04: genuinely tied hypotheses -- REFERENCE_EQUALITY holds in both
# directions between two column pairs (positions 0<->1 and 2<->3), all four
# tied at the lowest complexity rank (0). Verified by direct execution:
# discover_all_hypotheses() reports (0,1), (1,0), (2,3) and (3,2), all rank
# 0 -- select_hypothesis() correctly refuses to pick one, AMBIGUOUS_SELECTION.
_V2C04_TRAIN = tuple(
    Node(f"v2c04_row{i}", OBSERVATION, (eq, eq, NodeRef(f"v2c04_{i}y"), NodeRef(f"v2c04_{i}y")))
    for i, eq in ((i, NodeRef(f"v2c04_{i}eq")) for i in range(1, 4))
)

# --- V2C05: composition of two independently-selected selection mappings --
# inner: arity 3 -> 2, picks (position 2, position 0); outer: arity 2 -> 1,
# picks position 1. Both confirmed by direct execution to retain a unique
# hypothesis on their own (no tie, no competing family) when run through
# discover_all_hypotheses()/select_hypothesis() independently.
_V2C05_INNER_TRAIN = tuple(
    _row(
        f"v2c05i_row{i}",
        f"v2c05i_op{i}",
        Node(f"v2c05i_src{i}", OBSERVATION, (NodeRef(f"v2c05_{i}a"), NodeRef(f"v2c05_{i}b"), NodeRef(f"v2c05_{i}c"))),
        Node(f"v2c05i_tgt{i}", OBSERVATION, (NodeRef(f"v2c05_{i}c"), NodeRef(f"v2c05_{i}a"))),
    )
    for i in range(1, 4)
)
_V2C05_OUTER_TRAIN = tuple(
    _row(
        f"v2c05o_row{i}",
        f"v2c05o_op{i}",
        Node(f"v2c05o_src{i}", OBSERVATION, (NodeRef(f"v2c05_{i}m0"), NodeRef(f"v2c05_{i}m1"))),
        Node(f"v2c05o_tgt{i}", OBSERVATION, (NodeRef(f"v2c05_{i}m1"),)),
    )
    for i in range(1, 4)
)
_V2C05_HOLDOUT = tuple(
    Node(f"v2c05_hsrc{i}", OBSERVATION, (NodeRef(f"v2c05_h{i}a"), NodeRef(f"v2c05_h{i}b"), NodeRef(f"v2c05_h{i}c")))
    for i in range(1, 4)
)

# --- V2C06: no discoverable hypothesis at all (constant target, Gate E) ---
# Verified by direct execution: discover_all_hypotheses() finds ZERO
# candidates over any position pair (the only Node-bearing pair, (1, 2),
# is REJECTED by discover() itself since the target never varies) --
# select_hypothesis() reports NO_HYPOTHESES, a fail-closed outcome at the
# selection layer distinct from (but consistent with) Gate A's own
# per-pair REJECTED label used in v0.1's C07.
_V2C06_TRAIN = tuple(
    _row(
        f"v2c06_row{i}",
        f"v2c06_op{i}",
        Node(f"v2c06_src{i}", OBSERVATION, (NodeRef(f"v2c06_{i}a"), NodeRef(f"v2c06_{i}b"))),
        Node(f"v2c06_tgt{i}", OBSERVATION, (NodeRef("v2c06_CONST"),)),
    )
    for i in range(3)
)


LOCKED_CASES_V2: Tuple[LockedCaseV2, ...] = (
    LockedCaseV2("V2C01_PROJECTION", "SELECTION_MAPPING", "RETAINED", _V2C01_TRAIN, _V2C01_HOLDOUT),
    LockedCaseV2("V2C02_DUPLICATION", "SELECTION_MAPPING", "RETAINED", _V2C02_TRAIN, _V2C02_HOLDOUT),
    LockedCaseV2("V2C03_TWO_HYPOTHESES_UNIQUE_WINNER", "SELECTION_MAPPING", "RETAINED", _V2C03_TRAIN, _V2C03_HOLDOUT),
    LockedCaseV2("V2C04_AMBIGUOUS_SELECTION", None, "AMBIGUOUS_SELECTION", _V2C04_TRAIN),
    LockedCaseV2(
        "V2C05_COMPOSED", "COMPOSED", "RETAINED", (),
        holdout_source=_V2C05_HOLDOUT,
        composed_inner_rows=_V2C05_INNER_TRAIN,
        composed_outer_rows=_V2C05_OUTER_TRAIN,
    ),
    LockedCaseV2("V2C06_NO_HYPOTHESES", None, "NO_HYPOTHESES", _V2C06_TRAIN),
)


__all__ = ["LockedCaseV2", "LOCKED_CASES_V2"]
