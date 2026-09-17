"""MetaHIA E20-D.4 — operator-relation discovery v0.1.

Experimental layer: discover the relation between the operators already present
inside paired structures, rather than supplying that relation as an input fact.

Scope:
  * extract operator references from OBSERVATION structures;
  * infer an observed operator mapping O1 -> O2 across paired observations;
  * fail closed on contradictory mappings;
  * keep operator identity reference-based;
  * optionally feed the discovered relation into the existing operator-space
    constructor to build/identify a higher-order operator object.

No semantic interpretation of operator names is performed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from kernel2 import Node, NodeRef, RefObject, OBSERVATION, reference_equal
from operator_space_v0_1 import (
    operator_relation_fact,
    compose_existing_operator_profile,
)

OPERATOR_MAPPING = "OPERATOR_MAPPING"


@dataclass(frozen=True)
class OperatorMappingCandidate:
    source_operator: NodeRef
    target_operator: NodeRef
    evidence_rows: Tuple[str, ...]


@dataclass(frozen=True)
class OperatorRelationDiscovery:
    candidates: Tuple[OperatorMappingCandidate, ...]
    contradictions: Tuple[Tuple[str, str, str], ...]
    source_domains: Tuple[str, ...]


def _extract_pair(src: Node, dst: Node) -> Tuple[NodeRef, NodeRef]:
    if src.kind != OBSERVATION or dst.kind != OBSERVATION:
        raise ValueError("E20-D.4 requires OBSERVATION pairs")
    if not src.children or not dst.children:
        raise ValueError("observations must contain an operator position")
    a, b = src.children[0], dst.children[0]
    if not isinstance(a, NodeRef) or not isinstance(b, NodeRef):
        raise ValueError("operator position must be a NodeRef")
    return a, b


def discover_operator_relation(
    pairs: Sequence[Tuple[Node, Node]], *, min_evidence: int = 3
) -> OperatorRelationDiscovery:
    """Discover a deterministic observed operator relation from paired structures.

    For each source operator reference, all observed target operator references
    must agree. Repeated identical mappings are collapsed. Contradictory source
    mappings are reported rather than guessed through.
    """
    if len(pairs) < min_evidence:
        raise ValueError(f"E20-D.4 requires at least {min_evidence} paired observations")

    mapping: Dict[str, NodeRef] = {}
    rows: Dict[str, list[str]] = {}
    contradictions: list[Tuple[str, str, str]] = []

    for src, dst in pairs:
        s, t = _extract_pair(src, dst)
        key = s.ref_id
        rows.setdefault(key, []).append(src.node_id + "->" + dst.node_id)
        previous = mapping.get(key)
        if previous is None:
            mapping[key] = t
        elif not reference_equal(previous, t):
            contradictions.append((src.node_id, key, f"{previous.ref_id}!={t.ref_id}"))

    candidates = tuple(
        OperatorMappingCandidate(
            source_operator=NodeRef(k),
            target_operator=mapping[k],
            evidence_rows=tuple(rows[k]),
        )
        for k in sorted(mapping)
    )
    domains = tuple(sorted(mapping))
    return OperatorRelationDiscovery(candidates, tuple(contradictions), domains)


def mapping_relation_fact(candidate: OperatorMappingCandidate) -> Node:
    return operator_relation_fact(
        candidate.source_operator,
        candidate.target_operator,
        OPERATOR_MAPPING,
    )


def build_operator_from_discovered_relation(
    candidate: OperatorMappingCandidate,
    source_profile: Node,
    target_profile: Node,
    *,
    existing: Sequence[RefObject] = (),
    new_ref_id: Optional[str] = None,
) -> Tuple[str, RefObject]:
    """Turn a discovered O1->O2 relation into the existing operator-space step."""
    fact = mapping_relation_fact(candidate)
    return compose_existing_operator_profile(
        source_profile,
        target_profile,
        existing=existing,
        relation_facts=(fact,),
        new_ref_id=new_ref_id,
    )
