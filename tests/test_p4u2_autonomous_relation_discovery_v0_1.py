"""Tests for `p4u2_autonomous_relation_discovery_v0_1.py`.

Each test corresponds to a result already established by the disposable
calibration campaigns C1-C7 (documentation/P4U2_Calibration_Experiment_2026-09-23.md
through documentation/P4U2_Calibration_Campaign7_VoletC_RealCorpus_2026-09-24.md)
and Gate H's freeze (documentation/P4U2_Gate_H_V1_0_Frozen_2026-09-24.md),
now promoted into permanent regression tests -- same discipline as the
wedge exclusion (P4-U.1) and the leak fixes (P4-T.1/P4-T.1bis).
"""
from __future__ import annotations

import inspect
import random

import p4u2_autonomous_relation_discovery_v0_1 as p4u2
from kernel2 import Node, NodeRef, OBSERVATION


def mk_obs(idx: int, src: str, tgt: str) -> Node:
    op = NodeRef(f"OP#{idx:05d}")
    return Node(f"obs::{idx}", OBSERVATION, (op, NodeRef(src), NodeRef(tgt)), provenance=(f"obs::{idx}",))


# ---------------------------------------------------------------------------
# 1. Signature reference values
# ---------------------------------------------------------------------------

def test_signature_matches_disposable_calibration_reference():
    """A->B->C->D chain plus a dead-end X->Y: exact values already
    confirmed by direct execution against the disposable calibration
    scripts before this module existed."""
    observations = [mk_obs(0, "A", "B"), mk_obs(1, "B", "C"), mk_obs(2, "C", "D"), mk_obs(3, "X", "Y")]
    graph, sigs = p4u2.compute_signatures(observations)

    assert sigs[0] == p4u2.Signature(1, 1, 1, frozenset({("FORWARD",), ("FORWARD", "FORWARD"), ("FORWARD", "FORWARD", "FORWARD")}))
    assert sigs[1] == p4u2.Signature(1, 1, 0, frozenset({("FORWARD",), ("FORWARD", "FORWARD")}))
    assert sigs[2] == p4u2.Signature(1, 0, 0, frozenset({("FORWARD",)}))
    assert sigs[3] == p4u2.Signature(1, 0, 0, frozenset({("FORWARD",)}))
    # The dead-end edge (obs::3) and the chain's last edge (obs::2) share
    # an identical signature despite being structurally unrelated --
    # exactly the coincidence group_by_signature must tolerate and Gate I
    # must be able to reject when it is not a real regularity.
    assert sigs[2] == sigs[3]


# ---------------------------------------------------------------------------
# 2. Gate I must not declare significance on a rigorously homogeneous
#    corpus (TWIN, campaign 5) -- the decisive finding that eliminated
#    the topology-only null model.
# ---------------------------------------------------------------------------

def _corpus_twin():
    """4 disjoint directed 20-cycles: by construction every edge has an
    identical signature -- no subset should be distinguishable from any
    other under a correctly-specified null."""
    observations = []
    group = []
    for c in range(4):
        nodes = [f"c{c}n{i}" for i in range(20)]
        cycle_indices = []
        for i in range(20):
            idx = len(observations)
            observations.append(mk_obs(idx, nodes[i], nodes[(i + 1) % 20]))
            cycle_indices.append(idx)
        if c == 0:
            group = cycle_indices
    return observations, tuple(group)


def test_gate_i_null_gives_zero_z_on_homogeneous_corpus():
    observations, group = _corpus_twin()
    graph, sigs = p4u2.compute_signatures(observations)
    candidate = [sigs[i] for i in group]

    result = p4u2.evaluate_gate_i(candidate, list(sigs), percentile_threshold=95.0, n_null=300, seed_base=2000)

    assert result.status == p4u2.GATE_I_FAIL
    assert result.percentile == 50.0  # exact tie with the null -- no distinction exists, none should be claimed


# ---------------------------------------------------------------------------
# 3. Gate I's group-level statistic must detect the partial-overlap signal
#    that a naive per-observation equality check would have missed
#    (identifiability experiment, z=3.79) -- guards against ever
#    regressing to that disproven verification method.
# ---------------------------------------------------------------------------

def _corpus_partial_overlap(group_size: int = 40):
    """80%/20% split, mirrored background -- exact structural
    reproduction of the identifiability experiment's Corpus 3 /
    campaign 1's Corpus PARTIAL, scaled to group_size=40 (campaign 3's
    own proposed minimum size to keep this case away from the power
    boundary)."""
    n_cont = round(group_size * 0.8)
    n_dead = group_size - n_cont
    observations = []
    group = []
    for i in range(n_cont):
        group.append(len(observations)); observations.append(mk_obs(len(observations), f"pgA{i}", f"pgB{i}"))
        observations.append(mk_obs(len(observations), f"pgB{i}", f"pgC{i}"))
    for i in range(n_dead):
        group.append(len(observations)); observations.append(mk_obs(len(observations), f"pgD{i}", f"pgE{i}"))
    for i in range(n_dead):
        observations.append(mk_obs(len(observations), f"bgA{i}", f"bgB{i}"))
        observations.append(mk_obs(len(observations), f"bgB{i}", f"bgC{i}"))
    for i in range(n_cont):
        observations.append(mk_obs(len(observations), f"bgD{i}", f"bgE{i}"))
    return observations, tuple(group)


def test_gate_i_naive_equality_would_be_wrong_but_group_statistic_is_right():
    observations, group = _corpus_partial_overlap()
    graph, sigs = p4u2.compute_signatures(observations)
    candidate = [sigs[i] for i in group]

    # What a naive per-observation equality check would have seen: two
    # distinct signature classes present in the candidate group, exactly
    # the situation the identifiability experiment proved insufficient
    # to distinguish "no signal" from "real but noisy signal" -- Gate I
    # must not rely on this.
    assert len(set(candidate)) == 2

    result = p4u2.evaluate_gate_i(candidate, list(sigs), percentile_threshold=95.0, n_null=300, seed_base=4100)

    assert result.status == p4u2.GATE_I_PASS
    assert result.percentile >= 95.0


# ---------------------------------------------------------------------------
# 4. Multiple-comparisons correction (campaign 4 Part 3 / campaign 5/6):
#    1 true signal group + 9 signal-free candidates -- the max-statistic
#    correction must give zero false positives on this fixed dataset.
# ---------------------------------------------------------------------------

def _build_multi_candidate_corpus(seed: int = 777):
    rng = random.Random(seed)
    observations = []
    true_group = []
    for i in range(18):  # 90% of 20 = 18
        true_group.append(len(observations)); observations.append(mk_obs(len(observations), f"mcT{i}A", f"mcT{i}B"))
        observations.append(mk_obs(len(observations), f"mcT{i}B", f"mcT{i}C"))
    for i in range(2):
        true_group.append(len(observations)); observations.append(mk_obs(len(observations), f"mcTd{i}A", f"mcTd{i}B"))

    nodes = [f"mcbg{i}" for i in range(300)]
    used = set()
    bg_start = len(observations)
    while len(observations) - bg_start < 200:
        s, t = rng.choice(nodes), rng.choice(nodes)
        if s == t or (s, t) in used:
            continue
        used.add((s, t))
        observations.append(mk_obs(len(observations), s, t))
    bg_end = len(observations)

    pool = list(range(bg_start, bg_end))
    rng.shuffle(pool)
    null_groups = [tuple(sorted(pool[k * 20:(k + 1) * 20])) for k in range(9)]
    return observations, tuple(true_group), null_groups


def test_multi_comparisons_correction_rejects_null_candidates():
    observations, true_group, null_groups = _build_multi_candidate_corpus()
    all_groups = [true_group] + null_groups
    graph, sigs = p4u2.compute_signatures(observations)
    group_size = len(true_group)

    observed = [p4u2.cohesion_b_mean_distance([sigs[i] for i in g]) for g in all_groups]
    threshold = p4u2.gate_i_family_threshold(list(sigs), group_size, len(all_groups), n_null=300, percentile=95.0, seed_base=9000)

    true_signal_observed, null_observed = observed[0], observed[1:]
    assert true_signal_observed > threshold  # the real signal must still be detected

    false_positives = sum(1 for value in null_observed if value > threshold)
    assert false_positives == 0


# ---------------------------------------------------------------------------
# 5. Gate H must fail SAFE (CALIBRATION_INSUFFICIENT) outside its frozen
#    envelope -- never PASS, never FAIL, on a configuration calibration
#    never validated (campaigns 4-7).
# ---------------------------------------------------------------------------

def _corpus_manifest_mix(group_size: int, minority_fraction: float, tag: str):
    observations = []
    group = []
    n_minority = round(minority_fraction * group_size)
    n_majority = group_size - n_minority
    for i in range(n_majority):
        group.append(len(observations)); observations.append(mk_obs(len(observations), f"{tag}maj{i}A", f"{tag}maj{i}B"))
        observations.append(mk_obs(len(observations), f"{tag}maj{i}B", f"{tag}maj{i}C"))
    for i in range(n_minority):
        group.append(len(observations)); observations.append(mk_obs(len(observations), f"{tag}min{i}A", f"{tag}min{i}B"))
        observations.append(mk_obs(len(observations), f"{tag}min{i}B", f"{tag}min{i}C"))
        observations.append(mk_obs(len(observations), f"{tag}min{i}C", f"{tag}min{i}D"))
    return observations, tuple(group)


def _build_background_pool():
    """Same three-class, non-dominant-composition pool validated across
    campaigns 5 and 6 (Part B): 80 dead-end / 150 one-hop / 40 two-hop."""
    observations = []
    for i in range(80):
        observations.append(mk_obs(len(observations), f"de{i}A", f"de{i}B"))
    for i in range(150):
        observations.append(mk_obs(len(observations), f"h1{i}A", f"h1{i}B"))
        observations.append(mk_obs(len(observations), f"h1{i}B", f"h1{i}C"))
    for i in range(40):
        observations.append(mk_obs(len(observations), f"h2{i}A", f"h2{i}B"))
        observations.append(mk_obs(len(observations), f"h2{i}B", f"h2{i}C"))
        observations.append(mk_obs(len(observations), f"h2{i}C", f"h2{i}D"))
    return observations


def test_gate_h_below_envelope_returns_calibration_insufficient():
    pool_observations = _build_background_pool()
    _, pool_sigs = p4u2.compute_signatures(pool_observations)

    # group_size=10 is below the frozen envelope's minimum of 20.
    observations, group = _corpus_manifest_mix(10, 0.5, tag="small_")
    _, sigs = p4u2.compute_signatures(observations)
    candidate = [sigs[i] for i in group]

    result = p4u2.evaluate_gate_h(candidate, list(pool_sigs), n_null=200, seed_base=1)

    assert result.status == p4u2.GATE_H_CALIBRATION_INSUFFICIENT
    assert result.envelope_ok is False


# ---------------------------------------------------------------------------
# 6. Gate H must distinguish manifest heterogeneity (a real second class)
#    from natural noise once inside the calibrated envelope (campaigns 4
#    Part A / 5 / 6): same order of magnitude of disagreement, different
#    verdicts.
# ---------------------------------------------------------------------------

def _corpus_natural_noise(group_size: int, p_fail: float, seed: int, tag: str):
    rng = random.Random(seed)
    observations = []
    group = []
    for i in range(group_size):
        idx = len(observations); group.append(idx)
        src, tgt = f"{tag}m{i}A", f"{tag}m{i}B"
        observations.append(mk_obs(idx, src, tgt))
        if rng.random() >= p_fail:
            observations.append(mk_obs(len(observations), tgt, f"{tag}m{i}C"))
            continue
        choice = rng.random()
        if choice < 0.4:
            pass  # a plain missing continuation
        elif choice < 0.7:
            hub = f"{tag}hub{rng.randint(0, 4)}"
            observations.append(mk_obs(len(observations), tgt, hub))
            if rng.random() < 0.5:
                observations.append(mk_obs(len(observations), hub, f"{tag}hubout{rng.randint(0, 999)}"))
        else:
            observations.append(mk_obs(len(observations), tgt, f"{tag}m{i}Cx"))
            observations.append(mk_obs(len(observations), f"{tag}m{i}Cx", f"{tag}m{i}Dx"))
    return observations, tuple(group)


def test_gate_h_distinguishes_noise_from_manifest_heterogeneity():
    pool_observations = _build_background_pool()
    _, pool_sigs = p4u2.compute_signatures(pool_observations)

    # Heterogeneity: a real, internally uniform second class (k~9 at
    # group_size=40, inside the frozen envelope).
    het_observations, het_group = _corpus_manifest_mix(40, 0.225, tag="het_")
    _, het_sigs = p4u2.compute_signatures(het_observations)
    het_candidate = [het_sigs[i] for i in het_group]
    het_result = p4u2.evaluate_gate_h(het_candidate, list(pool_sigs), n_null=300, seed_base=2)

    assert het_result.envelope_ok is True
    assert het_result.status == p4u2.GATE_H_PASS

    # Natural noise at a comparable contamination level and the same
    # group size -- a fixed seed confirmed (by direct execution) to fall
    # inside the envelope and to be correctly rejected.
    noise_observations, noise_group = _corpus_natural_noise(40, 0.225, seed=5001, tag="noise_")
    _, noise_sigs = p4u2.compute_signatures(noise_observations)
    noise_candidate = [noise_sigs[i] for i in noise_group]
    noise_result = p4u2.evaluate_gate_h(noise_candidate, list(pool_sigs), n_null=200, seed_base=6000)

    assert noise_result.envelope_ok is True
    assert noise_result.status != p4u2.GATE_H_PASS
    assert noise_result.status == p4u2.GATE_H_FAIL


# ---------------------------------------------------------------------------
# 7. No function in this module ever accepts or uses ground truth (the
#    hidden relation label) before a discovery decision is made -- same
#    static discipline already applied to P4-T/P4-U.1.
# ---------------------------------------------------------------------------

def test_group_by_signature_never_uses_ground_truth():
    forbidden_terms = ("ground_truth", "expected_relation", "witness", "REL_A", "REL_B")
    source = inspect.getsource(p4u2)
    lowered = source.lower()
    for term in forbidden_terms:
        assert term.lower() not in lowered, f"module source unexpectedly references {term!r}"

    # group_by_signature takes only the signatures themselves -- no
    # optional label/witness/ground-truth parameter exists to smuggle
    # in extra information before Gate I/Gate H run.
    signature = inspect.signature(p4u2.group_by_signature)
    assert list(signature.parameters) == ["sigs"]
