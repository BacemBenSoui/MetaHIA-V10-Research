"""P4-T -- Structural Transformation Induction, Gates A-G.

Verifies, by direct execution (never by narrative), the claims made in the
external review that proposed replacing P4-R with this approach: that
`e20d_protocol.py`'s existing permutation/recursive-permutation discovery
is real and non-circular, and that the genuinely new capability added here
(arity-changing selection mappings: projection, duplication, composition)
extends the same fail-closed safety discipline rather than weakening it.
"""
from __future__ import annotations

import dataclasses

from kernel2 import Node, NodeRef, OBSERVATION
import p4t_structural_transformation_induction_v0_1 as p4t


def _row(row_id, op, source, target, out=None):
    children = (NodeRef(op), source, target) if out is None else (NodeRef(op), source, target, NodeRef(out))
    return Node(row_id, OBSERVATION, children)


# ---------------------------------------------------------------------------
# Gate A + reuse: REFERENCE_EQUALITY / PERMUTATION / RECURSIVE_PERMUTATION
# ---------------------------------------------------------------------------


def test_discover_reuses_e20d_protocol_for_permutation_family():
    rows = [
        Node("R1", OBSERVATION, (NodeRef("a"), NodeRef("b"))),
        Node("R2", OBSERVATION, (NodeRef("b"), NodeRef("a"))),
        Node("R3", OBSERVATION, (NodeRef("c"), NodeRef("c"))),
    ]
    candidate = p4t.discover(rows, source_position=0, target_position=1)
    assert candidate.family == p4t.FAMILY_PERMUTATION
    assert candidate.outcome == p4t.OUTCOME_CANDIDATE
    assert candidate.cross_slot is not None
    assert candidate.selection is None


def test_discover_reuses_e20d_protocol_for_recursive_permutation_and_replays_blind_on_fresh_entities():
    """Mirrors tests/test_e20d_v03_recursive_transform.py's own non-circular
    replay discipline, but through the new unified Gate A-D pipeline."""
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("z")))
        tgt = Node(f"tgt{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("z")))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt, out="out"))

    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.family == p4t.FAMILY_RECURSIVE_PERMUTATION
    assert candidate.outcome == p4t.OUTCOME_CANDIDATE

    frozen = p4t.freeze(candidate, frozen_id="RECURSIVE_FROZEN")

    # Entirely fresh entities never seen at discovery time; target slot is a
    # placeholder the mechanism never reads.
    fresh = [
        Node(f"fresh_src{i}", OBSERVATION, ("O", NodeRef(f"f{i}x"), NodeRef(f"f{i}y"), NodeRef("z")))
        for i in range(1, 4)
    ]
    predictions = p4t.blind_replay(frozen, fresh)
    assert len(predictions) == 3
    ground_truth = [
        Node(f"truth{i}", OBSERVATION, ("O", NodeRef(f"f{i}y"), NodeRef(f"f{i}x"), NodeRef("z")))
        for i in range(1, 4)
    ]
    results = [p4t.verify(p, t) for p, t in zip(predictions, ground_truth)]
    assert all(r.match for r in results)


# ---------------------------------------------------------------------------
# Gate F: the genuinely new family -- arity-changing selection mappings
# ---------------------------------------------------------------------------


def test_projection_is_discovered_and_replays_blind_on_fresh_entities():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))

    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.family == p4t.FAMILY_SELECTION_MAPPING
    assert candidate.outcome == p4t.OUTCOME_CANDIDATE
    assert candidate.selection.sigma == (0,)
    assert p4t.classify_selection_mapping(candidate.selection) == "PROJECTION"

    frozen = p4t.freeze(candidate, frozen_id="PROJECTION_FROZEN")
    fresh = [Node("fresh1", OBSERVATION, (NodeRef("z_a"), NodeRef("z_b"), NodeRef("z_c")))]
    predictions = p4t.blind_replay(frozen, fresh)
    truth = [Node("truth1", OBSERVATION, (NodeRef("z_a"),))]
    assert p4t.verify(predictions[0], truth[0]).match


def test_duplication_is_discovered_and_replays_blind_on_fresh_entities():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}a"), NodeRef(f"{i}b")))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))

    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.family == p4t.FAMILY_SELECTION_MAPPING
    assert candidate.selection.sigma == (0, 0, 1)
    assert p4t.classify_selection_mapping(candidate.selection) == "DUPLICATION"

    frozen = p4t.freeze(candidate, frozen_id="DUPLICATION_FROZEN")
    fresh = [Node("fresh1", OBSERVATION, (NodeRef("z_x"), NodeRef("z_y")))]
    predictions = p4t.blind_replay(frozen, fresh)
    truth = [Node("truth1", OBSERVATION, (NodeRef("z_x"), NodeRef("z_x"), NodeRef("z_y")))]
    assert p4t.verify(predictions[0], truth[0]).match


def test_two_independently_discovered_mappings_compose_and_replay_blind():
    """Gate F composition: chains two SEPARATELY frozen transformations end
    to end (not a re-run of discovery on pre-composed data)."""
    inner_rows = []
    for i in range(1, 4):
        src = Node(f"isrc{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"itgt{i}", OBSERVATION, (NodeRef(f"{i}c"), NodeRef(f"{i}a")))
        inner_rows.append(_row(f"irow{i}", f"iop{i}", src, tgt))
    inner_candidate = p4t.discover(inner_rows, source_position=1, target_position=2)
    frozen_inner = p4t.freeze(inner_candidate, frozen_id="INNER")

    outer_rows = []
    for i in range(1, 4):
        src = Node(f"osrc{i}", OBSERVATION, (NodeRef(f"{i}m0"), NodeRef(f"{i}m1")))
        tgt = Node(f"otgt{i}", OBSERVATION, (NodeRef(f"{i}m1"),))
        outer_rows.append(_row(f"orow{i}", f"oop{i}", src, tgt))
    outer_candidate = p4t.discover(outer_rows, source_position=1, target_position=2)
    frozen_outer = p4t.freeze(outer_candidate, frozen_id="OUTER")

    frozen_composed = p4t.compose_frozen(frozen_outer, frozen_inner, frozen_id="COMPOSED")
    assert frozen_composed.source_arity == 3
    assert frozen_composed.target_arity == 1
    # inner picks (pos2, pos0); outer then picks mid-position 1 (== inner's pos0) -> source pos0.
    assert frozen_composed.sigma == (0,)

    fresh = [Node("fresh1", OBSERVATION, (NodeRef("A"), NodeRef("B"), NodeRef("C")))]
    predictions = p4t.blind_replay(frozen_composed, fresh)
    truth = [Node("truth1", OBSERVATION, (NodeRef("A"),))]
    assert p4t.verify(predictions[0], truth[0]).match


# ---------------------------------------------------------------------------
# Gate E: anti-cheating properties, verified adversarially
# ---------------------------------------------------------------------------


def test_selection_mapping_exposes_ambiguity_instead_of_guessing():
    shared = [NodeRef(f"s{i}") for i in range(3)]
    rows = []
    for i in range(3):
        src = Node(f"src{i}", OBSERVATION, (shared[i], shared[i], NodeRef(f"c{i}")))
        tgt = Node(f"tgt{i}", OBSERVATION, (shared[i],))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.outcome == p4t.OUTCOME_AMBIGUOUS


def test_selection_mapping_rejects_a_contradictory_mapping_rather_than_forcing_one():
    rows = []
    for i in range(3):
        a, b, c = NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")
        src = Node(f"src{i}", OBSERVATION, (a, b, c))
        tgt_value = a if i < 2 else c  # inconsistent across rows -- no single source position fits.
        tgt = Node(f"tgt{i}", OBSERVATION, (tgt_value,))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.outcome == p4t.OUTCOME_REJECTED


def test_selection_mapping_rejects_a_constant_target_not_derived_from_source():
    rows = []
    for i in range(3):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef("CONST"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.outcome == p4t.OUTCOME_REJECTED


def test_selection_mapping_rejects_a_per_row_varying_but_structurally_unrelated_target():
    """A target that changes every row but is never reference-equal to any
    source slot in any row is not identifiable in this vocabulary -- it
    must be rejected, not hallucinated as some semantic function."""
    rows = []
    for i in range(3):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"derived_{i}"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.outcome == p4t.OUTCOME_REJECTED


# ---------------------------------------------------------------------------
# Gate B: freeze must not leak training-time identities
# ---------------------------------------------------------------------------


def test_frozen_transformation_does_not_leak_training_node_refs():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    frozen = p4t.freeze(candidate, frozen_id="LEAK_CHECK")
    # structural_digest is a one-way SHA-256 hash: excluded here deliberately,
    # since a 64-hex-char digest can coincidentally contain any short
    # substring without that being a real leak of the hashed input.
    non_digest_fields = {f.name: getattr(frozen, f.name) for f in dataclasses.fields(frozen) if f.name != "structural_digest"}
    non_digest_repr = repr(non_digest_fields)
    for training_id in ("1a", "2a", "3a", "1b", "2b", "3b", "1c", "2c", "3c"):
        assert training_id not in non_digest_repr
    # sigma is positions only -- never the original NodeRef objects.
    assert all(isinstance(s, int) for s in frozen.sigma)


def test_frozen_recursive_transformation_does_not_leak_training_row_ids():
    """Regression guard for a real bug found 2026-09-21 (external review,
    confirmed by direct execution before fixing): freeze() used to store
    the raw CrossSlotCandidate for the PERMUTATION/RECURSIVE families,
    whose own `evidence_rows`/`source_target_provenance` fields -- and even
    e20d_protocol.py's own PATTERN Node `node_id`/`provenance` strings --
    embed the training row ids (e.g. "row1", "row2", "row3") directly.
    freeze() now rebuilds an anonymized pattern instead."""
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("z")))
        tgt = Node(f"tgt{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("z")))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt, out="out"))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.family == p4t.FAMILY_RECURSIVE_PERMUTATION
    frozen = p4t.freeze(candidate, frozen_id="RECURSIVE_LEAK_CHECK")
    non_digest_fields = {f.name: getattr(frozen, f.name) for f in dataclasses.fields(frozen) if f.name != "structural_digest"}
    non_digest_repr = repr(non_digest_fields)
    for training_id in ("row1", "row2", "row3", "src1", "src2", "src3", "tgt1", "tgt2", "tgt3"):
        assert training_id not in non_digest_repr


def test_structural_digest_distinguishes_two_different_permutations_of_the_same_family():
    """Regression guard for a real bug found 2026-09-21 (external review,
    confirmed by direct execution before fixing): the digest used to hash
    only (family, relation_kind), which is constant for an entire family --
    two structurally different permutations got the identical digest. It
    now fingerprints the actual mapping via kernel2.structural_signature()."""
    rows_swap = []
    for i in range(1, 4):
        src = Node(f"s1_{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("z")))
        tgt = Node(f"t1_{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("z")))
        rows_swap.append(_row(f"rowA{i}", f"opA{i}", src, tgt, out="out"))
    candidate_swap = p4t.discover(rows_swap, source_position=1, target_position=2)
    frozen_swap = p4t.freeze(candidate_swap, frozen_id="DIGEST_A")

    rows_rotate = []
    for i in range(1, 4):
        src = Node(f"s2_{i}", OBSERVATION, ("O", NodeRef(f"{i}p"), NodeRef(f"{i}q"), NodeRef(f"{i}r")))
        tgt = Node(f"t2_{i}", OBSERVATION, ("O", NodeRef(f"{i}r"), NodeRef(f"{i}p"), NodeRef(f"{i}q")))
        rows_rotate.append(_row(f"rowB{i}", f"opB{i}", src, tgt, out="out"))
    candidate_rotate = p4t.discover(rows_rotate, source_position=1, target_position=2)
    frozen_rotate = p4t.freeze(candidate_rotate, frozen_id="DIGEST_B")

    assert frozen_swap.family == frozen_rotate.family == p4t.FAMILY_RECURSIVE_PERMUTATION
    assert frozen_swap.structural_digest != frozen_rotate.structural_digest


def test_frozen_pattern_does_not_leak_a_literal_constraint_node_ref():
    """Regression guard for a real bug found 2026-09-22 (external review,
    confirmed by direct execution before fixing): _anonymize_pattern()
    anonymized a Node's own node_id/provenance but copied
    PatternSlot.literal_constraint through completely unchanged in every
    branch. A slot that kernel2.compare() validly discovers as "this
    position is always exactly this one training entity" (a recursive
    pattern's constant trailing slot) therefore kept the real training
    NodeRef verbatim inside the supposedly opaque frozen pattern --
    confirmed before the fix: repr(frozen) contained the literal training
    NodeRef id. Fixed by anonymizing literal_constraint too, via the new
    _anonymize_literal() helper."""
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("TRAIN_Z")))
        tgt = Node(f"tgt{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("TRAIN_Z")))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt, out="out"))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.family == p4t.FAMILY_RECURSIVE_PERMUTATION
    frozen = p4t.freeze(candidate, frozen_id="LITERAL_LEAK_CHECK")
    non_digest_fields = {f.name: getattr(frozen, f.name) for f in dataclasses.fields(frozen) if f.name != "structural_digest"}
    non_digest_repr = repr(non_digest_fields)
    assert "TRAIN_Z" not in non_digest_repr
    # blind_replay on a genuinely fresh holdout entity must still reflect
    # THAT entity, not the anonymized training literal -- the anonymization
    # must be display-only, never a substitution that corrupts replay.
    holdout = [
        Node(f"hold{i}", OBSERVATION, ("O", NodeRef(f"h{i}p"), NodeRef(f"h{i}q"), NodeRef("FRESH_Z")))
        for i in range(1, 4)
    ]
    predictions = p4t.blind_replay(frozen, holdout)
    assert all(p is not None for p in predictions)
    for prediction in predictions:
        assert NodeRef("FRESH_Z") in prediction.children
        assert NodeRef("TRAIN_Z") not in prediction.children


def test_structural_digest_is_invariant_to_which_entities_trained_it():
    """Regression guard for a real bug found 2026-09-22 (external review,
    confirmed by direct execution before fixing): freeze() computed the
    digest from structural_signature(cs.transformation) -- the RAW,
    pre-anonymization pattern. kernel2.structural_signature() deliberately
    preserves NodeRef identity, so two independently-discovered
    transformations of the exact same shape, differing only in which
    training entities happened to produce them, got two DIFFERENT digests
    (confirmed by direct construction of such a pair before the fix,
    values 1c2a503b... vs 725c72ca...). Fixed by hashing
    structural_signature(anonymized_ref) instead -- the already-anonymized
    object being stored, not the raw training-time structure. Covers both
    the plain recursive-permutation case and the literal-constraint case
    (same shape, same literal VALUE across both trainings, different
    literal IDENTITY) since both must still collapse to one digest."""
    rows_a = []
    for i in range(1, 4):
        src = Node(f"a_s{i}", OBSERVATION, ("O", NodeRef(f"A{i}x"), NodeRef(f"A{i}y"), NodeRef("A_Z")))
        tgt = Node(f"a_t{i}", OBSERVATION, ("O", NodeRef(f"A{i}y"), NodeRef(f"A{i}x"), NodeRef("A_Z")))
        rows_a.append(_row(f"rowA{i}", f"opA{i}", src, tgt, out="out"))
    candidate_a = p4t.discover(rows_a, source_position=1, target_position=2)
    frozen_a = p4t.freeze(candidate_a, frozen_id="INVARIANCE_A")

    rows_b = []
    for i in range(1, 4):
        src = Node(f"b_s{i}", OBSERVATION, ("O", NodeRef(f"B{i}x"), NodeRef(f"B{i}y"), NodeRef("B_Z")))
        tgt = Node(f"b_t{i}", OBSERVATION, ("O", NodeRef(f"B{i}y"), NodeRef(f"B{i}x"), NodeRef("B_Z")))
        rows_b.append(_row(f"rowB{i}", f"opB{i}", src, tgt, out="out"))
    candidate_b = p4t.discover(rows_b, source_position=1, target_position=2)
    frozen_b = p4t.freeze(candidate_b, frozen_id="INVARIANCE_B")

    assert frozen_a.family == frozen_b.family == p4t.FAMILY_RECURSIVE_PERMUTATION
    assert frozen_a.structural_digest == frozen_b.structural_digest
    # still not a trivial always-equal digest: a genuinely different shape
    # (rotation instead of swap) must keep a different digest.
    rows_rotate = []
    for i in range(1, 4):
        src = Node(f"r_s{i}", OBSERVATION, ("O", NodeRef(f"R{i}p"), NodeRef(f"R{i}q"), NodeRef(f"R{i}r")))
        tgt = Node(f"r_t{i}", OBSERVATION, ("O", NodeRef(f"R{i}r"), NodeRef(f"R{i}p"), NodeRef(f"R{i}q")))
        rows_rotate.append(_row(f"rowR{i}", f"opR{i}", src, tgt, out="out"))
    candidate_rotate = p4t.discover(rows_rotate, source_position=1, target_position=2)
    frozen_rotate = p4t.freeze(candidate_rotate, frozen_id="INVARIANCE_ROTATE")
    assert frozen_rotate.structural_digest != frozen_a.structural_digest


def test_freeze_refuses_a_non_candidate_outcome():
    rows = []
    for i in range(3):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef("CONST"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    candidate = p4t.discover(rows, source_position=1, target_position=2)
    assert candidate.outcome == p4t.OUTCOME_REJECTED
    try:
        p4t.freeze(candidate, frozen_id="SHOULD_FAIL")
        assert False, "freeze() must refuse a REJECTED outcome"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Gate G: cost measurement, real and non-negative
# ---------------------------------------------------------------------------


def test_costed_pipeline_reports_real_non_negative_measurements():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))

    holdout_src = [Node("h1", OBSERVATION, (NodeRef("h1a"), NodeRef("h1b"), NodeRef("h1c")))]
    holdout_truth = [Node("t1", OBSERVATION, (NodeRef("h1a"),))]

    candidate, frozen, verifications, report = p4t.run_costed_pipeline(
        rows, holdout_src, holdout_truth,
        source_position=1, target_position=2, frozen_id="COSTED",
    )
    assert candidate.outcome == p4t.OUTCOME_CANDIDATE
    assert frozen is not None
    assert len(verifications) == 1
    assert verifications[0].match
    assert report.discovery_seconds >= 0.0
    assert report.replay_seconds >= 0.0
    assert report.verify_seconds >= 0.0
    assert report.discovery_row_count == 3
    assert report.replay_row_count == 1
    assert report.discovery_position_pairs_tried > 0


def test_costed_pipeline_produces_no_verifications_when_discovery_is_rejected():
    rows = []
    for i in range(3):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef("CONST"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    holdout_src = [Node("h1", OBSERVATION, (NodeRef("h1a"), NodeRef("h1b")))]
    holdout_truth = [Node("t1", OBSERVATION, (NodeRef("CONST"),))]

    candidate, frozen, verifications, report = p4t.run_costed_pipeline(
        rows, holdout_src, holdout_truth,
        source_position=1, target_position=2, frozen_id="REJECTED_COSTED",
    )
    assert candidate.outcome == p4t.OUTCOME_REJECTED
    assert frozen is None
    assert verifications == ()


# ---------------------------------------------------------------------------
# Gate A.3 (P4-T.3): hypothesis selection among multiple candidates
# ---------------------------------------------------------------------------


def test_discover_all_hypotheses_reports_a_symmetric_reference_equality_pair_both_ways():
    """Reference equality is genuinely undirected: if column i always
    equals column j by reference, (i, j) and (j, i) are both structurally
    valid hypotheses. This is confirmed real behaviour, not a bug to hide."""
    rows = []
    for i in range(1, 4):
        eq = NodeRef(f"{i}eq")
        rows.append(Node(f"row{i}", OBSERVATION, (eq, eq, NodeRef(f"{i}y"), NodeRef(f"{i}y"))))
    hyps = p4t.discover_all_hypotheses(rows)
    pairs = {(h.source_position, h.target_position) for h in hyps}
    assert (0, 1) in pairs and (1, 0) in pairs
    assert (2, 3) in pairs and (3, 2) in pairs
    assert all(h.complexity_rank == 0 for h in hyps)


def test_select_hypothesis_exposes_ambiguity_for_symmetric_tied_families():
    rows = []
    for i in range(1, 4):
        eq = NodeRef(f"{i}eq")
        rows.append(Node(f"row{i}", OBSERVATION, (eq, eq, NodeRef(f"{i}y"), NodeRef(f"{i}y"))))
    hyps = p4t.discover_all_hypotheses(rows)
    result = p4t.select_hypothesis(hyps)
    assert result.outcome == p4t.OUTCOME_AMBIGUOUS_SELECTION
    assert result.retained is None


def test_select_hypothesis_retains_a_unique_lowest_rank_hypothesis():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(Node(f"row{i}", OBSERVATION, (NodeRef(f"op{i}"), src, tgt)))
    hyps = p4t.discover_all_hypotheses(rows)
    result = p4t.select_hypothesis(hyps)
    assert result.outcome == p4t.OUTCOME_RETAINED
    assert (result.retained.source_position, result.retained.target_position) == (1, 2)
    assert result.retained.candidate.family == p4t.FAMILY_SELECTION_MAPPING


def test_select_hypothesis_prefers_lower_rank_over_a_coexisting_higher_rank_alternative():
    """A rank-2 SELECTION_MAPPING hypothesis and a rank-3 (tied, symmetric)
    RECURSIVE_PERMUTATION hypothesis are both discoverable in the same
    observation set. Only the lower-rank one is retained -- the tie at
    rank 3 never even enters the decision, because selection only compares
    hypotheses at the single best rank present."""
    rows = []
    for i in range(1, 4):
        rsrc = Node(f"rsrc{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("z")))
        rtgt = Node(f"rtgt{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("z")))
        psrc = Node(f"psrc{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        ptgt = Node(f"ptgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(Node(f"row{i}", OBSERVATION, (rsrc, rtgt, psrc, ptgt)))
    hyps = p4t.discover_all_hypotheses(rows)
    ranks_present = {h.complexity_rank for h in hyps}
    assert ranks_present == {2, 3}
    result = p4t.select_hypothesis(hyps)
    assert result.outcome == p4t.OUTCOME_RETAINED
    assert (result.retained.source_position, result.retained.target_position) == (2, 3)
    assert result.retained.candidate.family == p4t.FAMILY_SELECTION_MAPPING


def test_select_hypothesis_returns_no_hypotheses_when_nothing_is_discoverable():
    rows = []
    for i in range(3):
        rows.append(Node(f"row{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"))))
    hyps = p4t.discover_all_hypotheses(rows)
    result = p4t.select_hypothesis(hyps)
    assert result.outcome == p4t.OUTCOME_NO_HYPOTHESES
    assert result.retained is None
    assert result.all_hypotheses == ()


# ---------------------------------------------------------------------------
# Gate A.3: optional E20-D.6 rationalization hook
# ---------------------------------------------------------------------------


def _recursive_candidate(prefix: str):
    rows = []
    for i in range(1, 4):
        src = Node(f"{prefix}src{i}", OBSERVATION, ("O", NodeRef(f"{prefix}{i}x"), NodeRef(f"{prefix}{i}y"), NodeRef("z")))
        tgt = Node(f"{prefix}tgt{i}", OBSERVATION, ("O", NodeRef(f"{prefix}{i}y"), NodeRef(f"{prefix}{i}x"), NodeRef("z")))
        rows.append(_row(f"{prefix}row{i}", f"{prefix}op{i}", src, tgt, out="out"))
    return p4t.discover(rows, source_position=1, target_position=2)


def test_rationalize_retained_hypothesis_finds_exact_historical_match():
    """Two independently-discovered recursive permutations built from
    entirely different NodeRef labels are the SAME transformation
    structurally -- E20-D.6's own similarity mechanism (reused unchanged)
    must find them exactly similar via the anonymized pattern, not by
    coincidence of shared training identifiers (there are none shared)."""
    frozen_a = p4t.freeze(_recursive_candidate("a"), frozen_id="HIST_A")
    frozen_b = p4t.freeze(_recursive_candidate("b"), frozen_id="NEW_B")
    result = p4t.rationalize_retained_hypothesis(frozen_b, [frozen_a])
    assert result is not None
    assert result.status == "SUPPORTED_HISTORICAL"
    assert result.similarity == 1.0


def test_rationalize_retained_hypothesis_returns_none_for_selection_mapping_family():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    selection_candidate = p4t.discover(rows, source_position=1, target_position=2)
    frozen_selection = p4t.freeze(selection_candidate, frozen_id="SEL_SCOPE_CHECK")
    frozen_historical = p4t.freeze(_recursive_candidate("h"), frozen_id="HIST_H")
    assert p4t.rationalize_retained_hypothesis(frozen_selection, [frozen_historical]) is None


def test_rationalize_retained_hypothesis_returns_none_without_historical_candidates():
    frozen_a = p4t.freeze(_recursive_candidate("a"), frozen_id="NO_HIST")
    assert p4t.rationalize_retained_hypothesis(frozen_a, []) is None


# ---------------------------------------------------------------------------
# Gate F (P4-T.4): a genuinely new family -- multi-source selection mapping
# ---------------------------------------------------------------------------


def _multi_source_rows():
    rows = []
    for i in range(1, 4):
        a = Node(f"a{i}", OBSERVATION, (NodeRef(f"{i}a0"), NodeRef(f"{i}a1")))
        b = Node(f"b{i}", OBSERVATION, (NodeRef(f"{i}b0"), NodeRef(f"{i}b1")))
        t = Node(f"t{i}", OBSERVATION, (NodeRef(f"{i}a1"), NodeRef(f"{i}b0")))
        rows.append(Node(f"row{i}", OBSERVATION, (a, b, t)))
    return rows


def test_multi_source_selection_mapping_is_discovered_and_replays_blind_on_fresh_entities():
    """Target assembled from parts of TWO independent source structures --
    neither kernel2.compare() (single pairwise, equal arity) nor
    discover_selection_mapping (single source) can express this."""
    rows = _multi_source_rows()
    candidate = p4t.discover_multi_source(rows, source_positions=(0, 1), target_position=2)
    assert candidate.family == p4t.FAMILY_MULTI_SOURCE_SELECTION_MAPPING
    assert candidate.outcome == p4t.OUTCOME_CANDIDATE
    assert candidate.multi_selection.sigma == ((0, 1), (1, 0))

    frozen = p4t.freeze(candidate, frozen_id="MULTI_FROZEN")
    fresh_a = [Node(f"fa{i}", OBSERVATION, (NodeRef(f"fa0_{i}"), NodeRef(f"fa1_{i}"))) for i in range(3)]
    fresh_b = [Node(f"fb{i}", OBSERVATION, (NodeRef(f"fb0_{i}"), NodeRef(f"fb1_{i}"))) for i in range(3)]
    predictions = p4t.blind_replay_multi_source(frozen, [fresh_a, fresh_b])
    assert len(predictions) == 3
    for i, predicted in enumerate(predictions):
        assert predicted.children == (NodeRef(f"fa1_{i}"), NodeRef(f"fb0_{i}"))


def test_multi_source_selection_mapping_exposes_ambiguity_instead_of_guessing():
    rows = []
    for i in range(1, 4):
        shared = NodeRef(f"{i}s")
        a = Node(f"a{i}", OBSERVATION, (shared, NodeRef(f"{i}a1")))
        b = Node(f"b{i}", OBSERVATION, (shared, NodeRef(f"{i}b1")))
        t = Node(f"t{i}", OBSERVATION, (shared,))
        rows.append(Node(f"row{i}", OBSERVATION, (a, b, t)))
    candidate = p4t.discover_multi_source(rows, source_positions=(0, 1), target_position=2)
    assert candidate.outcome == p4t.OUTCOME_AMBIGUOUS


def test_multi_source_selection_mapping_rejects_a_constant_target():
    rows = []
    for i in range(1, 4):
        a = Node(f"a{i}", OBSERVATION, (NodeRef(f"{i}a0"),))
        b = Node(f"b{i}", OBSERVATION, (NodeRef(f"{i}b0"),))
        t = Node(f"t{i}", OBSERVATION, (NodeRef("CONST"),))
        rows.append(Node(f"row{i}", OBSERVATION, (a, b, t)))
    candidate = p4t.discover_multi_source(rows, source_positions=(0, 1), target_position=2)
    assert candidate.outcome == p4t.OUTCOME_REJECTED


def test_multi_source_frozen_transformation_does_not_leak_training_identities():
    rows = _multi_source_rows()
    candidate = p4t.discover_multi_source(rows, source_positions=(0, 1), target_position=2)
    frozen = p4t.freeze(candidate, frozen_id="MULTI_LEAK_CHECK")
    non_digest_fields = {f.name: getattr(frozen, f.name) for f in dataclasses.fields(frozen) if f.name != "structural_digest"}
    non_digest_repr = repr(non_digest_fields)
    for training_id in ("1a0", "1a1", "1b0", "1b1", "2a0", "2a1", "2b0", "2b1", "3a0", "3a1", "3b0", "3b1"):
        assert training_id not in non_digest_repr
    # multi_sigma is (slot_index, child_index) integer pairs only.
    assert all(isinstance(s, int) and isinstance(c, int) for s, c in frozen.multi_sigma)


def test_discover_multi_source_requires_at_least_two_sources():
    rows = _multi_source_rows()
    try:
        p4t.discover_multi_source(rows, source_positions=(0,), target_position=2)
        assert False, "must reject a single source_position -- use discover() instead"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Gate G -> E20-D.19 ROI adapter (P4-T.6)
# ---------------------------------------------------------------------------


def _projection_hypothesis_and_frozen():
    rows = []
    for i in range(1, 4):
        src = Node(f"src{i}", OBSERVATION, (NodeRef(f"{i}a"), NodeRef(f"{i}b"), NodeRef(f"{i}c")))
        tgt = Node(f"tgt{i}", OBSERVATION, (NodeRef(f"{i}a"),))
        rows.append(_row(f"row{i}", f"op{i}", src, tgt))
    hyps = p4t.discover_all_hypotheses(rows)
    selection = p4t.select_hypothesis(hyps)
    assert selection.outcome == p4t.OUTCOME_RETAINED
    frozen = p4t.freeze(selection.retained.candidate, frozen_id="ROI_FROZEN")
    return selection.retained, frozen


def test_score_hypothesis_roi_reuses_e20d19_decision_constants_unchanged():
    from e20d_cognitive_control_v0_1 import DECISION_EXPLORE, DECISION_DEFER, DECISION_STOP

    retained, frozen = _projection_hypothesis_and_frozen()
    cost_report = p4t.P4TCostReport(
        discovery_seconds=0.0, discovery_row_count=3, discovery_position_pairs_tried=6,
        replay_seconds=0.0, replay_row_count=1, verify_seconds=0.0,
    )
    score = p4t.score_hypothesis_roi(retained, frozen, cost_report, expected_gain=10.0)
    assert score.decision in (DECISION_EXPLORE, DECISION_DEFER, DECISION_STOP)
    assert p4t.DECISION_EXPLORE == DECISION_EXPLORE  # imported unchanged, not redefined


def test_score_hypothesis_roi_cost_is_real_and_never_zero():
    retained, frozen = _projection_hypothesis_and_frozen()
    cost_report = p4t.P4TCostReport(
        discovery_seconds=0.0, discovery_row_count=3, discovery_position_pairs_tried=6,
        replay_seconds=0.0, replay_row_count=1, verify_seconds=0.0,
    )
    score = p4t.score_hypothesis_roi(retained, frozen, cost_report, expected_gain=1.0)
    assert score.cost == 7.0  # 6 position pairs tried + 1 holdout row, exactly as measured
    assert score.cost > 0.0


def test_score_hypothesis_roi_is_novel_without_a_historical_match():
    retained, frozen = _projection_hypothesis_and_frozen()
    cost_report = p4t.P4TCostReport(
        discovery_seconds=0.0, discovery_row_count=3, discovery_position_pairs_tried=6,
        replay_seconds=0.0, replay_row_count=1, verify_seconds=0.0,
    )
    score = p4t.score_hypothesis_roi(retained, frozen, cost_report, expected_gain=10.0, historical_frozen=[])
    assert score.novelty == 1.0
    assert score.roi > 0.0


def test_score_hypothesis_roi_drops_to_zero_for_a_genuine_historical_match():
    """Reuses P4-T.3's own rationalization hook: a hypothesis whose frozen
    pattern exactly matches a previously-frozen transformation is treated
    as not novel, collapsing its ROI to zero regardless of expected_gain."""
    frozen_hist = p4t.freeze(_recursive_candidate("h"), frozen_id="ROI_HIST")
    candidate_new = _recursive_candidate("n")
    frozen_new = p4t.freeze(candidate_new, frozen_id="ROI_NEW")
    hyp = p4t.Hypothesis(source_position=1, target_position=2, candidate=candidate_new, complexity_rank=3)
    cost_report = p4t.P4TCostReport(
        discovery_seconds=0.0, discovery_row_count=3, discovery_position_pairs_tried=6,
        replay_seconds=0.0, replay_row_count=1, verify_seconds=0.0,
    )
    score = p4t.score_hypothesis_roi(hyp, frozen_new, cost_report, expected_gain=10.0, historical_frozen=[frozen_hist])
    assert score.novelty == 0.0
    assert score.roi == 0.0
    assert score.decision == p4t.DECISION_STOP


def test_score_hypothesis_roi_zero_gain_yields_stop():
    retained, frozen = _projection_hypothesis_and_frozen()
    cost_report = p4t.P4TCostReport(
        discovery_seconds=0.0, discovery_row_count=3, discovery_position_pairs_tried=6,
        replay_seconds=0.0, replay_row_count=1, verify_seconds=0.0,
    )
    score = p4t.score_hypothesis_roi(retained, frozen, cost_report, expected_gain=0.0)
    assert score.roi == 0.0
    assert score.decision == p4t.DECISION_STOP
