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
