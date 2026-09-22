"""P4-T.2 -- locked benchmark: ground truth (WITNESS ONLY).

This is the ONLY file in this repository that contains the correct answers
for `p4t_locked_benchmark_cases_v0_1.py`'s holdout cases. It is a plain,
separate Python module specifically so that
`p4t_locked_benchmark_runner_v0_1.py` can be shown, mechanically (not by
promise), to never import it before predictions are already committed to
disk -- see that module's own docstring and
`tests/test_p4t_locked_benchmark_v0_1.py`'s static + dynamic import-order
checks.

Every expected value here was computed once, by directly running
`p4t_structural_transformation_induction_v0_1.py`'s already-validated
discover()/freeze()/blind_replay() on the cases file, exactly like the
runner will independently redo -- this is a determinism/non-circularity
check (the runner must reproduce this without ever reading this file), not
an oracle unavailable to the mechanism itself. A locked benchmark with a
deterministic mechanism cannot have a witness computed any other way; the
scientific content is the STRUCTURAL SEPARATION and the enforced order of
operations, not secrecy of the answer itself.
"""
from __future__ import annotations

from kernel2 import Node, NodeRef, OBSERVATION

WITNESS_OUTCOME = {
    "C01_PERMUTATION": "CANDIDATE",
    "C02_RECURSIVE_PERMUTATION": "CANDIDATE",
    "C03_PROJECTION": "CANDIDATE",
    "C04_DUPLICATION": "CANDIDATE",
    "C05_COMPOSITION": "CANDIDATE",
    "C06_AMBIGUOUS": "AMBIGUOUS",
    "C07_REJECTED": "REJECTED",
}

# Predicted holdout values, computed once by direct execution (see module
# docstring). None of these NodeRef ids appear anywhere in
# p4t_locked_benchmark_cases_v0_1.py's holdout_source tuples.
WITNESS_PREDICTIONS = {
    "C01_PERMUTATION": (
        NodeRef("c01_fresh2"),
        NodeRef("c01_fresh1"),
        NodeRef("c01_fresh3"),
    ),
    "C02_RECURSIVE_PERMUTATION": (
        Node("w_c02_1", OBSERVATION, ("O", NodeRef("c02_h1q"), NodeRef("c02_h1p"), NodeRef("c02_hz"))),
        Node("w_c02_2", OBSERVATION, ("O", NodeRef("c02_h2q"), NodeRef("c02_h2p"), NodeRef("c02_hz"))),
        Node("w_c02_3", OBSERVATION, ("O", NodeRef("c02_h3q"), NodeRef("c02_h3p"), NodeRef("c02_hz"))),
    ),
    "C03_PROJECTION": (
        Node("w_c03_1", OBSERVATION, (NodeRef("c03_h1a"),)),
        Node("w_c03_2", OBSERVATION, (NodeRef("c03_h2a"),)),
        Node("w_c03_3", OBSERVATION, (NodeRef("c03_h3a"),)),
    ),
    "C04_DUPLICATION": (
        Node("w_c04_1", OBSERVATION, (NodeRef("c04_h1a"), NodeRef("c04_h1a"), NodeRef("c04_h1b"))),
        Node("w_c04_2", OBSERVATION, (NodeRef("c04_h2a"), NodeRef("c04_h2a"), NodeRef("c04_h2b"))),
        Node("w_c04_3", OBSERVATION, (NodeRef("c04_h3a"), NodeRef("c04_h3a"), NodeRef("c04_h3b"))),
    ),
    "C05_COMPOSITION": (
        Node("w_c05_1", OBSERVATION, (NodeRef("c05_h1a"),)),
        Node("w_c05_2", OBSERVATION, (NodeRef("c05_h2a"),)),
        Node("w_c05_3", OBSERVATION, (NodeRef("c05_h3a"),)),
    ),
}

__all__ = ["WITNESS_OUTCOME", "WITNESS_PREDICTIONS"]
