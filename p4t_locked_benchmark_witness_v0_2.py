"""P4-T.2 v0.2 -- locked benchmark: ground truth (WITNESS ONLY).

This is the ONLY file in this repository that contains the correct
answers for `p4t_locked_benchmark_cases_v0_2.py`'s holdout cases. A plain,
separate module for exactly the same reason as
`p4t_locked_benchmark_witness_v0_1.py`: so
`p4t_locked_benchmark_runner_v0_2.py` can be shown, mechanically, to never
import it before predictions are already committed to disk -- see that
module's own docstring and
`tests/test_p4t_locked_benchmark_v0_2.py`'s static + dynamic checks.

Every expected value here was computed once, by directly running
`p4t_structural_transformation_induction_v0_1.py`'s already-validated
`discover_all_hypotheses()`/`select_hypothesis()`/`freeze()`/
`blind_replay()` on the cases file -- via
`p4t_locked_benchmark_runner_v0_2.run_discovery_and_replay()` itself, the
exact function the runner will independently redo. A locked benchmark
with a deterministic mechanism cannot have a witness computed any other
way; the scientific content is the STRUCTURAL SEPARATION and the enforced
order of operations (here, additionally: that the mechanism itself, not
this file or the cases file, chose which position pair to use), not
secrecy of the answer.
"""
from __future__ import annotations

from kernel2 import Node, NodeRef, OBSERVATION

WITNESS_SELECTION_OUTCOME = {
    "V2C01_PROJECTION": "RETAINED",
    "V2C02_DUPLICATION": "RETAINED",
    "V2C03_TWO_HYPOTHESES_UNIQUE_WINNER": "RETAINED",
    "V2C04_AMBIGUOUS_SELECTION": "AMBIGUOUS_SELECTION",
    "V2C05_COMPOSED": "RETAINED",
    "V2C06_NO_HYPOTHESES": "NO_HYPOTHESES",
}

# Predicted holdout values, computed once by direct execution (see module
# docstring). None of these holdout-derived NodeRef ids are ever assigned
# in p4t_locked_benchmark_cases_v0_2.py's train_rows for the same case.
WITNESS_PREDICTIONS = {
    "V2C01_PROJECTION": (
        Node("w_v2c01_1", OBSERVATION, (NodeRef("v2c01_h1a"),)),
        Node("w_v2c01_2", OBSERVATION, (NodeRef("v2c01_h2a"),)),
        Node("w_v2c01_3", OBSERVATION, (NodeRef("v2c01_h3a"),)),
    ),
    "V2C02_DUPLICATION": (
        Node("w_v2c02_1", OBSERVATION, (NodeRef("v2c02_h1a"), NodeRef("v2c02_h1a"), NodeRef("v2c02_h1b"))),
        Node("w_v2c02_2", OBSERVATION, (NodeRef("v2c02_h2a"), NodeRef("v2c02_h2a"), NodeRef("v2c02_h2b"))),
        Node("w_v2c02_3", OBSERVATION, (NodeRef("v2c02_h3a"), NodeRef("v2c02_h3a"), NodeRef("v2c02_h3b"))),
    ),
    # Winning hypothesis is the rank-2 SELECTION_MAPPING at (2, 3) -- picks
    # position 0 of the 3-tuple source, exactly like V2C01 above, despite
    # the two rank-3 COMPARE_RECURSIVE hypotheses tied at (0,1)/(1,0)
    # coexisting in the same training rows.
    "V2C03_TWO_HYPOTHESES_UNIQUE_WINNER": (
        Node("w_v2c03_1", OBSERVATION, (NodeRef("v2c03_h1a"),)),
        Node("w_v2c03_2", OBSERVATION, (NodeRef("v2c03_h2a"),)),
        Node("w_v2c03_3", OBSERVATION, (NodeRef("v2c03_h3a"),)),
    ),
    # V2C04_AMBIGUOUS_SELECTION: no prediction exists -- selection genuinely
    # refuses to pick a winner among the tied hypotheses.
    # V2C05_COMPOSED: inner picks (position 2, position 0) = (c, a); outer
    # then picks position 1 of that pair = a.
    "V2C05_COMPOSED": (
        Node("w_v2c05_1", OBSERVATION, (NodeRef("v2c05_h1a"),)),
        Node("w_v2c05_2", OBSERVATION, (NodeRef("v2c05_h2a"),)),
        Node("w_v2c05_3", OBSERVATION, (NodeRef("v2c05_h3a"),)),
    ),
    # V2C06_NO_HYPOTHESES: no prediction exists -- zero discoverable
    # hypotheses at all (constant target, Gate E).
}


__all__ = ["WITNESS_SELECTION_OUTCOME", "WITNESS_PREDICTIONS"]
