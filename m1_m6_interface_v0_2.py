"""MetaHIA M1-M6 stable transport envelope v0.2.

The v0.2 contract freezes the experimental v0.1 learning payload while adding
versioned audit metadata for multi-domain regression.  M1 structural objects
remain opaque runtime objects: the wire/audit form deliberately carries only
a deterministic structural digest, never an attempted JSON reconstruction of
an M1/K3 object.

This avoids silently changing the meaning of an opaque structural object while
still making the transport auditable and versioned.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Mapping, Optional

from m1_m6_interface_v0_1 import M6LearningPacket
from m6_structural_learning_v0_1 import _rule_signature

INTERFACE_VERSION = "0.2"
SUPPORTED_STAGES = ("M1", "M2", "M3", "M4", "M5", "M6")
EXCLUDED_DEPENDENCY = "M7"


def opaque_rule_digest(rule: object) -> str:
    """Stable-in-process audit digest of the structural M6 rule signature."""
    canonical = repr(_rule_signature(rule)).encode("utf-8")
    return sha256(canonical).hexdigest()


@dataclass(frozen=True)
class M1M6StableEnvelope:
    """Versioned audit envelope around the existing v0.1 M6 packet."""

    corpus_id: str
    domain_id: str
    packet: M6LearningPacket
    contract_version: str = INTERFACE_VERSION

    def validate(self) -> None:
        if self.contract_version != INTERFACE_VERSION:
            raise ValueError(
                f"unsupported contract_version={self.contract_version!r}; expected {INTERFACE_VERSION!r}"
            )
        if not self.corpus_id:
            raise ValueError("corpus_id is required")
        if not self.domain_id:
            raise ValueError("domain_id is required")
        self.packet.validate()

    @property
    def packet_id(self) -> str:
        return self.packet.packet_id

    @property
    def rule_digest(self) -> str:
        return opaque_rule_digest(self.packet.rule)

    def as_record_kwargs(self) -> Mapping[str, Any]:
        """Project exactly the seven fields consumed by M6."""
        self.validate()
        return self.packet.as_record_kwargs()

    def to_dict(self) -> dict[str, Any]:
        """Return the stable wire/audit form.

        The M1 rule object is opaque and therefore represented only by its
        type and structural digest.  The live packet remains the authoritative
        in-process object.
        """
        self.validate()
        return {
            "contract_version": self.contract_version,
            "corpus_id": self.corpus_id,
            "domain_id": self.domain_id,
            "packet": {
                "packet_id": self.packet.packet_id,
                "rule": {
                    "opaque": True,
                    "runtime_type": type(self.packet.rule).__name__,
                    "structural_digest": self.rule_digest,
                },
                "novelty": self.packet.novelty,
                "redundancy": self.packet.redundancy,
                "depth": self.packet.depth,
                "provenance": self.packet.provenance,
                "outcome": self.packet.outcome,
                "source_chain": list(self.packet.source_chain),
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        rule_resolver: Optional[Callable[[str, Mapping[str, Any]], object]] = None,
    ) -> "M1M6StableEnvelope":
        """Rehydrate an envelope only with an explicit runtime rule resolver.

        No opaque M1 object is guessed from JSON.  The resolver receives the
        packet id and opaque descriptor and must return the original runtime
        object.  This keeps object identity/semantics under the owning runtime.
        """
        if not isinstance(payload, Mapping):
            raise ValueError("envelope payload must be a mapping")
        packet_data = payload.get("packet")
        if not isinstance(packet_data, Mapping):
            raise ValueError("packet object is required")
        rule_wire = packet_data.get("rule")
        if not isinstance(rule_wire, Mapping) or rule_wire.get("opaque") is not True:
            raise ValueError("rule must use the opaque wire descriptor")
        if rule_resolver is None:
            raise ValueError("rule_resolver is required to rehydrate an opaque M1 rule")
        rule = rule_resolver(str(packet_data["packet_id"]), rule_wire)
        if opaque_rule_digest(rule) != str(rule_wire["structural_digest"]):
            raise ValueError("resolved rule does not match its structural digest")
        packet = M6LearningPacket(
            packet_id=str(packet_data["packet_id"]),
            rule=rule,
            novelty=float(packet_data["novelty"]),
            redundancy=float(packet_data["redundancy"]),
            depth=int(packet_data["depth"]),
            provenance=str(packet_data["provenance"]),
            outcome=str(packet_data["outcome"]),
            source_chain=tuple(packet_data.get("source_chain", ())),
        )
        envelope = cls(
            corpus_id=str(payload["corpus_id"]),
            domain_id=str(payload["domain_id"]),
            contract_version=str(payload.get("contract_version", "")),
            packet=packet,
        )
        envelope.validate()
        return envelope

    @classmethod
    def from_json(
        cls,
        raw: str,
        *,
        rule_resolver: Optional[Callable[[str, Mapping[str, Any]], object]] = None,
    ) -> "M1M6StableEnvelope":
        return cls.from_dict(json.loads(raw), rule_resolver=rule_resolver)


def stabilize_packet(packet: M6LearningPacket, *, corpus_id: str, domain_id: str) -> M1M6StableEnvelope:
    envelope = M1M6StableEnvelope(corpus_id=corpus_id, domain_id=domain_id, packet=packet)
    envelope.validate()
    return envelope


def interface_manifest_v0_2() -> Mapping[str, Any]:
    return {
        "version": INTERFACE_VERSION,
        "modules": SUPPORTED_STAGES,
        "excluded_dependency": EXCLUDED_DEPENDENCY,
        "audit_metadata": ("corpus_id", "domain_id"),
        "learning_payload": "M6LearningPacket.as_record_kwargs()",
        "learning_payload_fields": (
            "record_id", "rule", "novelty", "redundancy", "depth", "provenance", "outcome"
        ),
        "rule_wire_form": "opaque structural digest; runtime resolver required",
        "domain_metadata_reaches_m6": False,
    }


__all__ = [
    "EXCLUDED_DEPENDENCY",
    "INTERFACE_VERSION",
    "M1M6StableEnvelope",
    "SUPPORTED_STAGES",
    "interface_manifest_v0_2",
    "opaque_rule_digest",
    "stabilize_packet",
]
