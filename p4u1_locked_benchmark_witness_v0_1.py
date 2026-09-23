"""P4-U.1 -- locked benchmark: ground truth (WITNESS ONLY).

This is the ONLY file in this repository that contains the correct
Gate A/B/C outcomes for `p4u1_locked_benchmark_cases_v0_1.py`'s
declared candidates. Kept in a separate module specifically so
`p4u1_locked_benchmark_runner_v0_1.py` can be shown, mechanically (not
by promise), to never import it before predictions are already
committed to disk -- see that module's own docstring and
`tests/test_p4u1_locked_benchmark_v0_1.py`'s static + dynamic
import-order checks.

Every expected value here follows directly from the corpus DESIGN
(protocol v0.3 Sec. 8/14) and the fixed thresholds
(`p4u1_locked_benchmark_cases_v0_1.GATE_PARAMS`), confirmed once by
direct pilot execution BEFORE this benchmark's own numeric thresholds
were frozen -- see
`documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`.
This is a determinism/non-circularity check (the runner must reproduce
these outcomes independently, never having read this file), not an
oracle unavailable to the mechanism itself -- the same convention
`p4t_locked_benchmark_witness_v0_1.py` already documents for P4-T.

Keys are `(case_id, candidate_label)` pairs, matching
`p4u1_locked_benchmark_cases_v0_1.LockedCandidate.label` exactly.
"""
from __future__ import annotations

WITNESS_EXPECTED = {
    # --- U1: positive case + three-way competition ------------------------
    ("U1", "REAL_MOTIF"): {
        "gate_a": "DISCOVERED",
        "gate_b": "RETAINED",
        "gate_c": "REPLICATED",
    },
    ("U1", "DECOY_SUB_SEUIL"): {
        "gate_a": "DISCOVERED",
        "gate_b": "REJECTED",
        "gate_c": "NOT_APPLICABLE",
    },
    ("U1", "DECOY_DEPTH1"): {
        # Never even reaches Gate A as a depth>=2 candidate -- filtered by
        # min_depth inside discover_candidates() itself (Sec. 5).
        "gate_a": "NOT_DISCOVERED",
        "gate_b": None,
        "gate_c": None,
    },
    ("U1", "DECOY_TRAIN_ONLY"): {
        # Clears Gate B in TRAIN (same concentration as REAL_MOTIF) but
        # does not repeat at all in HOLDOUT -- Gate C, not Gate B, is
        # what must catch this.
        "gate_a": "DISCOVERED",
        "gate_b": "RETAINED",
        "gate_c": "FAILED",
    },
    # --- U2: the same train-only mechanism, standalone ---------------------
    ("U2", "REAL_MOTIF"): {
        "gate_a": "DISCOVERED",
        "gate_b": "RETAINED",
        "gate_c": "FAILED",
    },
    # --- U3: pure null control -- nothing should ever clear Gate B ---------
    ("U3", "NULL_CANDIDATE_FORWARD"): {
        "gate_a": "DISCOVERED",
        "gate_b": "REJECTED",
        "gate_c": "NOT_APPLICABLE",
    },
    ("U3", "NULL_CANDIDATE_REVERSE"): {
        "gate_a": "DISCOVERED",
        "gate_b": "REJECTED",
        "gate_c": "NOT_APPLICABLE",
    },
}

__all__ = ["WITNESS_EXPECTED"]
