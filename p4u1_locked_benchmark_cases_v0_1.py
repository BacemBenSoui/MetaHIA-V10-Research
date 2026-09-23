"""P4-U.1 -- locked benchmark: TRAIN + HOLDOUT-SOURCE cases (no truth here).

Implements the three locked cases required by
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
Sec. 14 (U1/U2/U3) with the numeric thresholds fixed by Sec. 16's
checklist, chosen BEFORE this file was written by direct pilot
calibration on throwaway corpora (never on this file's own data) --
see `documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`
for the full calibration record and reasoning.

Mirrors `p4t_locked_benchmark_cases_v0_1.py`'s own separation
discipline: this module contains ONLY what a genuine blind protocol is
allowed to see before prediction (train observations, for both Gate A/B
discovery, and holdout observations, for Gate C replay). It never
imports, and has no need to import, `p4u1_locked_benchmark_witness_v0_1`
-- the expected Gate A/B/C outcome for every declared candidate lives
exclusively there.

Corpus design, chosen so Gate B's "concentrated bridge" requirement and
Gate C's existence-based replay requirement can BOTH genuinely be
exercised on the SAME real motif (the whole point of the v0.3
resolution):

  U1 (Sec. 8/14, competition): a REAL_MOTIF bridge composition
  (REL_A -> BRIDGE -> REL_B, concentrated: several parents converge on
  one bridge node, which fans out to several children -- support is the
  PRODUCT of parent count and child count, not their sum) plus three
  decoys, each rejected for a distinct, separately verifiable reason:
    - DECOY_SUB_SEUIL: a genuine but small bridge (REL_C/REL_D),
      support far below S_min -- tests the SUB_THRESHOLD rejection.
    - DECOY_DEPTH1: a frequent DIRECT relation (REL_E, depth 1) --
      never even reaches Gate A as a depth->=2 candidate (`min_depth`
      filtering happens inside `discover_candidates` itself) -- tests
      NOT_DISCOVERED, not a Gate B rejection.
    - DECOY_TRAIN_ONLY: a bridge on REL_F/REL_G with the SAME
      concentration as REAL_MOTIF (so it legitimately clears Gate B in
      TRAIN) but with no such bridge at all in HOLDOUT -- tests that
      Gate C, not Gate B, is what catches a train-only regularity.
  Each background relation pair also carries plain single-degree
  "distractor" edges (unrelated entities, out-degree/in-degree exactly
  1) so the null model's own resampled pools are large enough that a
  random degree-concentration burst stays well below the real motifs'
  support -- calibrated by direct execution, not guessed.

  U2 (Sec. 14, standalone): the SAME train-only mechanism as
  DECOY_TRAIN_ONLY above, alone, isolating that failure mode without
  U1's competition.

  U3 (Sec. 14, pure null control): `G_train` is itself produced by
  `null_generator()` (the exact SAME procedure Gate B's own null
  distribution is built from, Sec. 6) applied to a flat base structure
  -- literally "no regularity injected anywhere," per the protocol's
  own wording. A fixed seed (0) was chosen after confirming, by direct
  execution across 10 candidate seeds, that this behavior (no candidate
  clears its own null-max) holds robustly, not as a lucky one-off pick.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from kernel2 import Node, OBSERVATION, node_ref
from p4u1_unsupervised_pattern_discovery_v0_1 import SkeletonKey, null_generator


def _obs(fact_id: str, rel: str, subj: str, obj: str) -> Node:
    return Node(fact_id, OBSERVATION, (node_ref(rel), node_ref(subj), node_ref(obj)))


def _bridge_edges(prefix: str, rel_a: str, rel_b: str, bridge_name: str, p_parents: int, q_children: int, start_i: int = 0):
    """`p_parents` REL_A edges converging on one bridge node, `q_children`
    REL_B edges fanning out from it -- support of the resulting depth-2
    composition is `p_parents * q_children` (every parent reaches every
    child through the shared bridge), not their sum. This is the
    concentration Gate B's own null model cannot produce by chance at
    this scale (calibrated by direct execution)."""
    edges = []
    i = start_i
    for p in range(p_parents):
        edges.append(_obs(f"{prefix}_a{i}", rel_a, f"{prefix}_PARENT{p}", bridge_name))
        i += 1
    for q in range(q_children):
        edges.append(_obs(f"{prefix}_b{i}", rel_b, bridge_name, f"{prefix}_CHILD{q}"))
        i += 1
    return edges, i


def _flat_edges(prefix: str, rel: str, n: int, start_i: int = 0):
    """`n` single-degree (source, target) pairs, each entity used exactly
    once -- pure pool-diluting background, never composing with
    anything else (its own entity namespace is never reused elsewhere)."""
    edges = []
    i = start_i
    for d in range(n):
        edges.append(_obs(f"{prefix}_e{i}", rel, f"{prefix}_S{d}", f"{prefix}_T{d}"))
        i += 1
    return edges, i


@dataclass(frozen=True)
class LockedCandidate:
    label: str
    skeleton: SkeletonKey


@dataclass(frozen=True)
class LockedCaseU1:
    case_id: str
    train_observations: Tuple[Node, ...]
    holdout_observations: Tuple[Node, ...]  # empty for U3 -- Gate C is never reached there
    candidates: Tuple[LockedCandidate, ...]
    null_seed_base_train: int = 0
    null_seed_base_holdout: int = 1000


# --- Numeric thresholds fixed BEFORE this file's data was ever compared
# against a holdout result (protocol v0.3 Sec. 16, checklist points
# 2/7/8/11) -- see the calibration record cited in the module docstring.
GATE_PARAMS = {
    "min_depth": 2,
    "max_depth": 3,
    # max_paths=None (Sec. 13's "recommended" default) was tried first and
    # found, by direct execution, to make the 200-replicate null-max
    # computation prohibitively slow (~60s per case) whenever a null
    # replicate randomly concentrates enough degree on one node to
    # combinatorially blow up depth-3 path enumeration -- a real,
    # measured cost, not guessed. A fixed cap is Sec. 13's own documented
    # fallback ("sinon: une limite fixe, IDENTIQUE sur G_train ET tous
    # les G_negative... et sur G_holdout et tous les G_holdout_negative"),
    # applied uniformly below to every discovery call in this benchmark,
    # train and null and holdout alike -- never a different limit on
    # different sides, which would bias the null comparison.
    "max_paths": 1000,
    "n_null": 200,
    "null_percentile": 99.0,
    "s_min": 15,
    "k_min": 15,
    "coverage_min": 0.10,
}


# =============================================================================
# U1 -- positive case + three-way competition (Sec. 8/14).
# =============================================================================

_i = 0
_u1_train: list = []
_edges, _i = _bridge_edges("u1t_real", "REL_A", "REL_B", "U1T_REAL_BRIDGE", 8, 8, _i)
_u1_train += _edges
_edges, _i = _bridge_edges("u1t_sub", "REL_C", "REL_D", "U1T_SUB_BRIDGE", 2, 2, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_depth1", "REL_E", 50, _i)
_u1_train += _edges
_edges, _i = _bridge_edges("u1t_trainonly", "REL_F", "REL_G", "U1T_TRAINONLY_BRIDGE", 8, 8, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_bgab_a", "REL_A", 60, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_bgab_b", "REL_B", 60, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_bgfg_a", "REL_F", 60, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_bgfg_b", "REL_G", 60, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_bgcd_a", "REL_C", 20, _i)
_u1_train += _edges
_edges, _i = _flat_edges("u1t_bgcd_b", "REL_D", 20, _i)
_u1_train += _edges
_U1_TRAIN: Tuple[Node, ...] = tuple(_u1_train)

_j = 0
_u1_holdout: list = []
_edges, _j = _bridge_edges("u1h_real", "REL_A", "REL_B", "U1H_REAL_BRIDGE", 25, 15, _j)
_u1_holdout += _edges
_edges, _j = _flat_edges("u1h_bgab_a", "REL_A", 30, _j)
_u1_holdout += _edges
_edges, _j = _flat_edges("u1h_bgab_b", "REL_B", 30, _j)
_u1_holdout += _edges
# DECOY_TRAIN_ONLY's relations appear in holdout ONLY as background
# distractors -- no REL_F/REL_G bridge exists here at all.
_edges, _j = _flat_edges("u1h_bgfg_a", "REL_F", 30, _j)
_u1_holdout += _edges
_edges, _j = _flat_edges("u1h_bgfg_b", "REL_G", 30, _j)
_u1_holdout += _edges
_U1_HOLDOUT: Tuple[Node, ...] = tuple(_u1_holdout)

_U1_CANDIDATES: Tuple[LockedCandidate, ...] = (
    LockedCandidate("REAL_MOTIF", (("REL_A", "FORWARD"), ("REL_B", "FORWARD"))),
    LockedCandidate("DECOY_SUB_SEUIL", (("REL_C", "FORWARD"), ("REL_D", "FORWARD"))),
    LockedCandidate("DECOY_DEPTH1", (("REL_E", "FORWARD"),)),
    LockedCandidate("DECOY_TRAIN_ONLY", (("REL_F", "FORWARD"), ("REL_G", "FORWARD"))),
)


# =============================================================================
# U2 -- train-only regularity, standalone (Sec. 14).
# =============================================================================

_k = 0
_u2_train: list = []
_edges, _k = _bridge_edges("u2t_real", "REL_H", "REL_I", "U2T_BRIDGE", 8, 8, _k)
_u2_train += _edges
_edges, _k = _flat_edges("u2t_bg_a", "REL_H", 60, _k)
_u2_train += _edges
_edges, _k = _flat_edges("u2t_bg_b", "REL_I", 60, _k)
_u2_train += _edges
_U2_TRAIN: Tuple[Node, ...] = tuple(_u2_train)

_l = 0
_u2_holdout: list = []
# No REL_H/REL_I bridge at all in holdout -- the regularity does not repeat.
_edges, _l = _flat_edges("u2h_bg_a", "REL_H", 30, _l)
_u2_holdout += _edges
_edges, _l = _flat_edges("u2h_bg_b", "REL_I", 30, _l)
_u2_holdout += _edges
_U2_HOLDOUT: Tuple[Node, ...] = tuple(_u2_holdout)

_U2_CANDIDATES: Tuple[LockedCandidate, ...] = (
    LockedCandidate("REAL_MOTIF", (("REL_H", "FORWARD"), ("REL_I", "FORWARD"))),
)


# =============================================================================
# U3 -- pure null control (Sec. 14).
# =============================================================================

_u3_base: list = []
for _n in range(40):
    _u3_base.append(_obs(f"u3base_j{_n}", "REL_J", f"u3base_JS{_n}", f"u3base_M{_n}"))
    _u3_base.append(_obs(f"u3base_k{_n}", "REL_K", f"u3base_M{_n}", f"u3base_KT{_n}"))
_U3_TRAIN: Tuple[Node, ...] = null_generator(tuple(_u3_base), seed=0)
_U3_HOLDOUT: Tuple[Node, ...] = ()  # Gate C is never reached for U3 -- nothing should clear Gate B

_U3_CANDIDATES: Tuple[LockedCandidate, ...] = (
    LockedCandidate("NULL_CANDIDATE_FORWARD", (("REL_J", "FORWARD"), ("REL_K", "FORWARD"))),
    LockedCandidate("NULL_CANDIDATE_REVERSE", (("REL_K", "REVERSE"), ("REL_J", "REVERSE"))),
)


LOCKED_CASES: Tuple[LockedCaseU1, ...] = (
    LockedCaseU1("U1", _U1_TRAIN, _U1_HOLDOUT, _U1_CANDIDATES),
    LockedCaseU1("U2", _U2_TRAIN, _U2_HOLDOUT, _U2_CANDIDATES),
    LockedCaseU1("U3", _U3_TRAIN, _U3_HOLDOUT, _U3_CANDIDATES),
)


__all__ = ["LockedCandidate", "LockedCaseU1", "LOCKED_CASES", "GATE_PARAMS"]
