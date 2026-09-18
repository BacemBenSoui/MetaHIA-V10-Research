"""MetaHIA M1-M6 Minimal Interface v0.1.

Purpose
-------
Define the smallest auditable transport contract needed to compose M1..M6
without making M7/LLM output a dependency. The interface is intentionally
structural and provenance-aware; it does not introduce semantic dictionaries,
new epistemic states, or hidden domain mappings.

The repository currently implements M1/K3, M3, M4, M5 and M6 as separate
modules; M2 remains a protocol-level epistemic contract. This module therefore
normalizes the inter-module data rather than pretending to be a new reasoning
engine.

Design invariants
-----------------
- M1 carries opaque structural objects; no external payload is dereferenced.
- DERIVED structure, EVIDENCE, and epistemic outcome remain distinct fields.
- M4 owns evidence provenance; M5 owns exploration/control metadata; M6 owns
  learning records and calibration.
- A packet can be serialized for audit, but no packet contains an LLM/M7 field.
- Interfaces are additive: existing module APIs are not replaced or mutated.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Optional, Tuple

from kernel2 import Node, PathPattern
from m4_cold_start_evidence_v0_1 import (
    GROUNDED_ANALOGY,
    GROUNDED_DIRECT,
    UNGROUNDED_HUMAN,
    SUPPORTED,
    CONTRADICTED,
    UNKNOWN,
)

M4_PROVENANCE = frozenset({GROUNDED_DIRECT, GROUNDED_ANALOGY, UNGROUNDED_HUMAN})
M6_OUTCOMES = frozenset({SUPPORTED, CONTRADICTED, UNKNOWN})


@dataclass(frozen=True)
class M1StructuralPacket:
    """Structural output entering the normalized M1-M6 transport."""

    packet_id: str
    structure: Any
    depth: int = 0
    novelty: float = 1.0
    redundancy: float = 0.0
    provenance: Tuple[str, ...] = ()
    derived: bool = True

    def validate(self) -> None:
        if not self.packet_id:
            raise ValueError("packet_id is required")
        if not isinstance(self.structure, (Node, PathPattern)):
            raise ValueError(
                "structure must be a kernel Node or PathPattern -- checked here so a "
                "malformed packet fails at the interface boundary with a clear message, "
                "not deep inside StructuralOutcomeRecord construction"
            )
        if self.depth < 0:
            raise ValueError("depth must be >= 0")
        if not 0.0 <= float(self.novelty) <= 1.0:
            raise ValueError("novelty must be within [0,1]")
        if not 0.0 <= float(self.redundancy) <= 1.0:
            raise ValueError("redundancy must be within [0,1]")
        if not isinstance(self.derived, bool):
            raise ValueError("derived must be boolean")


@dataclass(frozen=True)
class M2EpistemicPacket:
    """M2-level epistemic resolution, kept separate from structural derivation."""

    packet_id: str
    structural: M1StructuralPacket
    outcome: str
    evidence_ids: Tuple[str, ...] = ()

    def validate(self) -> None:
        self.structural.validate()
        if self.outcome not in M6_OUTCOMES:
            raise ValueError(f"invalid epistemic outcome: {self.outcome!r}")


@dataclass(frozen=True)
class M4EvidencePacket:
    """Evidence contract crossing M4 into the normalized pipeline."""

    packet_id: str
    epistemic: M2EpistemicPacket
    provenance: str
    independent_evidence_count: int = 0
    evidence_ids: Tuple[str, ...] = ()

    def validate(self) -> None:
        self.epistemic.validate()
        if self.provenance not in M4_PROVENANCE:
            raise ValueError(f"invalid M4 provenance: {self.provenance!r}")
        if self.independent_evidence_count < 0:
            raise ValueError("independent_evidence_count must be >= 0")


@dataclass(frozen=True)
class M5ControlPacket:
    """M5 control metadata associated with one structural/evidence item."""

    packet_id: str
    evidence: M4EvidencePacket
    expected_gain: float = 0.0
    actual_cost: float = 0.0
    useful: bool = True
    decision: Optional[str] = None

    def validate(self) -> None:
        self.evidence.validate()
        if float(self.expected_gain) < 0:
            raise ValueError("expected_gain must be >= 0")
        if float(self.actual_cost) < 0:
            raise ValueError("actual_cost must be >= 0")
        if not isinstance(self.useful, bool):
            raise ValueError("useful must be boolean")


@dataclass(frozen=True)
class M6LearningPacket:
    """Final normalized contract consumed by M6 learning."""

    packet_id: str
    rule: Any
    novelty: float
    redundancy: float
    depth: int
    provenance: str
    outcome: str
    source_chain: Tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.packet_id:
            raise ValueError("packet_id is required")
        if self.depth < 0:
            raise ValueError("depth must be >= 0")
        if not 0.0 <= float(self.novelty) <= 1.0:
            raise ValueError("novelty must be within [0,1]")
        if not 0.0 <= float(self.redundancy) <= 1.0:
            raise ValueError("redundancy must be within [0,1]")
        if self.provenance not in M4_PROVENANCE:
            raise ValueError(f"invalid M4 provenance: {self.provenance!r}")
        if self.outcome not in M6_OUTCOMES:
            raise ValueError(f"invalid M6 outcome: {self.outcome!r}")

    def as_record_kwargs(self) -> Mapping[str, Any]:
        """Return exactly the fields needed by StructuralOutcomeRecord."""
        self.validate()
        return {
            "record_id": self.packet_id,
            "rule": self.rule,
            "novelty": self.novelty,
            "redundancy": self.redundancy,
            "depth": self.depth,
            "provenance": self.provenance,
            "outcome": self.outcome,
        }


def compose_m1_to_m6(
    *,
    structural: M1StructuralPacket,
    outcome: str,
    provenance: str,
    evidence_ids: Tuple[str, ...] = (),
    independent_evidence_count: int = 0,
    expected_gain: float = 0.0,
    actual_cost: float = 0.0,
    useful: bool = True,
    decision: Optional[str] = None,
) -> M6LearningPacket:
    """Compose one auditable M1→M2→M4→M5→M6 packet.

    M3 can feed the `structure` and `depth` fields before this function is
    called; it is deliberately not encoded as a special semantic type. This
    keeps the transport contract generic and lets existing M3 traces remain
    authoritative.
    """
    m2 = M2EpistemicPacket(
        packet_id=f"m2::{structural.packet_id}",
        structural=structural,
        outcome=outcome,
        evidence_ids=tuple(evidence_ids),
    )
    m4 = M4EvidencePacket(
        packet_id=f"m4::{structural.packet_id}",
        epistemic=m2,
        provenance=provenance,
        independent_evidence_count=independent_evidence_count,
        evidence_ids=tuple(evidence_ids),
    )
    m5 = M5ControlPacket(
        packet_id=f"m5::{structural.packet_id}",
        evidence=m4,
        expected_gain=expected_gain,
        actual_cost=actual_cost,
        useful=useful,
        decision=decision,
    )
    m5.validate()
    packet = M6LearningPacket(
        packet_id=structural.packet_id,
        rule=structural.structure,
        novelty=structural.novelty,
        redundancy=structural.redundancy,
        depth=structural.depth,
        provenance=provenance,
        outcome=outcome,
        source_chain=(structural.packet_id, m2.packet_id, m4.packet_id, m5.packet_id),
    )
    packet.validate()
    return packet


def interface_manifest() -> Mapping[str, Any]:
    """Machine-readable contract summary for tests/documentation."""
    return {
        "version": "0.1",
        "modules": ("M1", "M2", "M3", "M4", "M5", "M6"),
        "excluded_dependency": "M7",
        "m1_output": "M1StructuralPacket",
        "m2_output": "M2EpistemicPacket",
        "m4_output": "M4EvidencePacket",
        "m5_output": "M5ControlPacket",
        "m6_input": "M6LearningPacket",
        "epistemic_outcomes": tuple(sorted(M6_OUTCOMES)),
        "m4_provenance": tuple(sorted(M4_PROVENANCE)),
    }


__all__ = [
    
    "M6_OUTCOMES",
    "M1StructuralPacket",
    "M2EpistemicPacket",
    "M4EvidencePacket",
    "M5ControlPacket",
    "M6LearningPacket",
    "compose_m1_to_m6",
    "interface_manifest",
]
