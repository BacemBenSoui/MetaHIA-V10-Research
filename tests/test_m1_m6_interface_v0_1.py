"""Minimal M1-M6 interface contract tests v0.1."""
from __future__ import annotations

import pytest

from kernel2 import Node, OBSERVATION, node_ref
from m1_m6_interface_v0_1 import (
    M1StructuralPacket,
    M6LearningPacket,
    compose_m1_to_m6,
    interface_manifest,
)


def test_manifest_excludes_m7_and_declares_only_minimal_transport_contract():
    manifest = interface_manifest()
    assert manifest["modules"] == ("M1", "M2", "M3", "M4", "M5", "M6")
    assert manifest["excluded_dependency"] == "M7"
    assert "M7" not in manifest["modules"]


def test_m1_to_m6_composition_preserves_derivation_evidence_and_epistemic_separation():
    rule = Node("R1", "PATTERN", ())
    structural = M1StructuralPacket(
        packet_id="org-test-01",
        structure=rule,
        depth=2,
        novelty=1.0,
        redundancy=0.0,
        provenance=("M3",),
        derived=True,
    )
    packet = compose_m1_to_m6(
        structural=structural,
        outcome="SUPPORTED",
        provenance="GROUNDED_DIRECT",
        evidence_ids=("EV-1",),
        independent_evidence_count=1,
        expected_gain=1.0,
        actual_cost=1.0,
        useful=True,
        decision="CONTINUE",
    )
    assert packet.rule is rule
    assert packet.depth == 2
    assert packet.outcome == "SUPPORTED"
    assert packet.provenance == "GROUNDED_DIRECT"
    assert packet.source_chain == ("org-test-01", "m2::org-test-01", "m4::org-test-01", "m5::org-test-01")
    assert packet.as_record_kwargs()["record_id"] == "org-test-01"


# ---------------------------------------------------------------------------
# Fail-closed validation: malformed packets are rejected with a clear error
# at the interface boundary, never silently accepted or deferred to a
# confusing failure deep inside M6 internals.
# ---------------------------------------------------------------------------

def _valid_structural(**overrides):
    defaults = dict(packet_id="pkt-01", structure=Node("R1", "PATTERN", ()), depth=1, novelty=1.0, redundancy=0.0)
    defaults.update(overrides)
    return M1StructuralPacket(**defaults)


def test_missing_packet_id_is_rejected():
    with pytest.raises(ValueError, match="packet_id"):
        _valid_structural(packet_id="").validate()


def test_non_kernel_structure_is_rejected_at_the_interface_boundary_not_deep_in_m6():
    """Regression guard: before this check existed, a wrong-typed `structure`
    would pass M1StructuralPacket.validate() silently and only fail later,
    with a confusing error, inside StructuralOutcomeRecord's own
    constructor -- fixed to fail fast and clearly at the packet boundary."""
    with pytest.raises(ValueError, match="Node or PathPattern"):
        _valid_structural(structure="not-a-kernel-object").validate()


def test_negative_depth_is_rejected():
    with pytest.raises(ValueError, match="depth"):
        _valid_structural(depth=-1).validate()


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_novelty_outside_unit_interval_is_rejected(value):
    with pytest.raises(ValueError, match="novelty"):
        _valid_structural(novelty=value).validate()


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_redundancy_outside_unit_interval_is_rejected(value):
    with pytest.raises(ValueError, match="redundancy"):
        _valid_structural(redundancy=value).validate()


def test_compose_rejects_unknown_epistemic_outcome():
    with pytest.raises(ValueError, match="epistemic outcome"):
        compose_m1_to_m6(structural=_valid_structural(), outcome="MAYBE", provenance="GROUNDED_DIRECT")


def test_compose_rejects_unknown_m4_provenance():
    with pytest.raises(ValueError, match="M4 provenance"):
        compose_m1_to_m6(structural=_valid_structural(), outcome="SUPPORTED", provenance="RUMOR")


def test_compose_rejects_negative_expected_gain_or_actual_cost():
    with pytest.raises(ValueError, match="expected_gain"):
        compose_m1_to_m6(structural=_valid_structural(), outcome="SUPPORTED", provenance="GROUNDED_DIRECT", expected_gain=-1.0)
    with pytest.raises(ValueError, match="actual_cost"):
        compose_m1_to_m6(structural=_valid_structural(), outcome="SUPPORTED", provenance="GROUNDED_DIRECT", actual_cost=-1.0)


def test_as_record_kwargs_produces_a_real_structural_outcome_record():
    """End-to-end check: the composed packet must actually build a real,
    valid StructuralOutcomeRecord -- not just look plausible in isolation."""
    from m6_structural_learning_v0_1 import StructuralOutcomeRecord

    rule = Node("R1", "PATTERN", ())
    structural = M1StructuralPacket(packet_id="pkt-02", structure=rule, depth=1, novelty=0.5, redundancy=0.5)
    packet = compose_m1_to_m6(structural=structural, outcome="CONTRADICTED", provenance="GROUNDED_ANALOGY")
    record = StructuralOutcomeRecord(**packet.as_record_kwargs())
    assert record.rule is rule
    assert record.outcome == "CONTRADICTED"
    assert record.provenance == "GROUNDED_ANALOGY"
