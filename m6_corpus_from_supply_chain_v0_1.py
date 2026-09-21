"""MetaHIA M6 -- independent third-domain corpus (supply chain) v0.1.

Mirrors `m6_corpus_from_organization_v0_1.py`'s already-validated, non-
degenerate mechanism exactly (separate STRUCTURAL PREDICTION from
INDEPENDENT VERIFICATION, via `corpus/supply_chain_verification_claims_v0_1.json`).
No change to the mechanism itself -- only the corpus files and the
`record_id` prefix change, to keep this a genuinely independent third domain
(industrial supply chain: workers/workshops/factories/markets/parts) rather
than a variant of the mechanism itself.

The discovery-side topology is deliberately NOT an isomorphic renaming of
the organization corpus: branching is asymmetric (3 workers under
Atelier_A vs 2 under Atelier_B; 3 factories under Atelier_A vs 1 under
Atelier_B; all 4 parts manufactured by Atelier_A, none by Atelier_B) -- see
corpus/supply_chain_facts_v0_1.json's own docstring field.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from kernel2 import (
    Node,
    OBSERVATION,
    PATH_REPLAYED,
    build_structural_graph,
    discover_paths,
    generalize_path_pattern,
    node_ref,
    replay_path_pattern_holdout,
)
from m4_cold_start_evidence_v0_1 import (
    CHALLENGE,
    CONTRADICTED,
    EXTERNAL,
    SUPPORT,
    SUPPORTED,
    UNKNOWN,
    AcquisitionRequest,
    LEVEL_A,
    acquire_cold_start,
    build_evidence,
)
from m6_structural_learning_v0_1 import StructuralOutcomeRecord

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "supply_chain_facts_v0_1.json"
CLAIMS_PATH = Path(__file__).resolve().parent / "corpus" / "supply_chain_verification_claims_v0_1.json"


def _facts_to_nodes(facts: List[list]) -> List[Node]:
    return [
        Node(fact_id, OBSERVATION, (node_ref(rel), node_ref(subj), node_ref(obj)), provenance=(fact_id,))
        for fact_id, rel, subj, obj in facts
    ]


def _load_claims(claims_path: Path) -> Dict[Tuple[str, tuple], dict]:
    data = json.loads(claims_path.read_text(encoding="utf-8"))
    index: Dict[Tuple[str, tuple], dict] = {}
    for claim in data["claims"]:
        skeleton = tuple((step[0], step[1]) for step in claim["skeleton"])
        index[(claim["subject"], skeleton)] = claim
    return index


@dataclass(frozen=True)
class SupplyChainCorpusReport:
    records: Tuple[StructuralOutcomeRecord, ...]
    candidate_patterns_considered: int
    excluded_no_verification_claim: Tuple[str, ...]


def _skeleton_key(path) -> tuple:
    return tuple((step.operator, step.direction) for step in path.steps)


def _support_or_challenge_evaluator(candidate_id: str, accepted_evidence) -> str:
    if any(e.polarity == CHALLENGE for e in accepted_evidence):
        return CONTRADICTED
    if any(e.polarity == SUPPORT for e in accepted_evidence):
        return SUPPORTED
    return UNKNOWN


def build_supply_chain_corpus(
    corpus_path: Path = CORPUS_PATH,
    claims_path: Path = CLAIMS_PATH,
) -> SupplyChainCorpusReport:
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    discovery_facts = _facts_to_nodes(data["discovery_facts"])
    evidence_facts = _facts_to_nodes(data["evidence_facts"])
    claims = _load_claims(claims_path)

    graph = build_structural_graph(discovery_facts)
    all_paths = discover_paths(graph, max_depth=2, max_paths=10000)

    by_skeleton: Dict[tuple, list] = {}
    for path in all_paths:
        by_skeleton.setdefault(_skeleton_key(path), []).append(path)

    records: List[StructuralOutcomeRecord] = []
    excluded_no_claim: List[str] = []
    considered = 0

    for skeleton, group in sorted(by_skeleton.items(), key=lambda kv: repr(kv[0])):
        if len(group) < 2:
            continue
        pattern = generalize_path_pattern(group, pattern_id=f"pattern::{skeleton!r}")
        if pattern is None:
            continue
        considered += 1

        skeleton_key = tuple((op.ref_id, direction) for op, direction in skeleton)

        starts = sorted({node_ref(f[2]) for f in data["evidence_facts"]}, key=lambda r: r.ref_id)
        found_any = False
        for start in starts:
            result = replay_path_pattern_holdout(pattern, evidence_facts, start)
            if result.status != PATH_REPLAYED:
                continue
            claim = claims.get((start.ref_id, skeleton_key))
            if claim is None:
                continue
            found_any = True

            agrees = claim["claimed_object"] == result.predicted_end.ref_id
            evidence = build_evidence(
                evidence_id=f"EV-{pattern.pattern_id}-{start.ref_id}",
                candidate_id=pattern.pattern_id,
                relation=result.predicted_end,
                polarity=SUPPORT if agrees else CHALLENGE,
                source_id=claim["source_id"],
                kind=EXTERNAL,
                direct=True,
            )
            request = AcquisitionRequest(candidate_id=pattern.pattern_id, query_ref=pattern.pattern_id, max_level=LEVEL_A)
            acquisition_result = acquire_cold_start(
                request,
                backoff_provider=lambda req, ev=evidence: ((ev,), 0.0),
                evaluator=_support_or_challenge_evaluator,
            )
            if not acquisition_result.evidence:
                continue

            records.append(
                StructuralOutcomeRecord(
                    record_id=f"supplyv1::{pattern.pattern_id}::{start.ref_id}",
                    rule=pattern,
                    novelty=1.0,
                    redundancy=0.0,
                    depth=pattern.length,
                    provenance=acquisition_result.evidence[0].provenance,
                    outcome=acquisition_result.final_state,
                )
            )

        if not found_any:
            excluded_no_claim.append(f"{pattern.pattern_id}: no matching verification claim for any evidence-graph start")

    return SupplyChainCorpusReport(
        records=tuple(records),
        candidate_patterns_considered=considered,
        excluded_no_verification_claim=tuple(excluded_no_claim),
    )


__all__ = ["SupplyChainCorpusReport", "build_supply_chain_corpus", "CORPUS_PATH", "CLAIMS_PATH"]
