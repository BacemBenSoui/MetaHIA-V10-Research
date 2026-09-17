"""MetaHIA M7 -- real corpus builder using the LLM as an independent witness v0.1.

Mirrors `m6_corpus_from_m4_m5_v0_2.py`'s structure exactly, replacing the
authored verification-claims corpus with a live, independent LLM as the
evidence source. Structural prediction (kernel2 replay against
`evidence_facts`, disjoint from `discovery_facts`) is unchanged; only the
verification step differs -- an LLM proposal in place of an authored claim.

Governance: the LLM never decides SUPPORTED/CONTRADICTED itself, only
supplies GROUNDED_ANALOGY evidence through the same
`acquire_cold_start()`/evaluator machinery M4/M6 already use (see
`m7_llm_fact_proposer_v0_1.py`'s module docstring for the full contract).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    SUPPORT,
    SUPPORTED,
    UNKNOWN,
    AcquisitionRequest,
    LEVEL_A,
    acquire_cold_start,
)
from m6_structural_learning_v0_1 import StructuralOutcomeRecord
from m7_llm_fact_proposer_v0_1 import GenerateFn, llm_evidence_for_prediction, propose_relation_llm

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "family_tree_facts_v0_2.json"


def _facts_to_nodes(facts: List[list]) -> List[Node]:
    return [
        Node(fact_id, OBSERVATION, (node_ref(rel), node_ref(subj), node_ref(obj)), provenance=(fact_id,))
        for fact_id, rel, subj, obj in facts
    ]


def _skeleton_key(path) -> tuple:
    return tuple((step.operator, step.direction) for step in path.steps)


def _evaluator(candidate_id: str, accepted_evidence) -> str:
    if any(e.polarity == CHALLENGE for e in accepted_evidence):
        return CONTRADICTED
    if any(e.polarity == SUPPORT for e in accepted_evidence):
        return SUPPORTED
    return UNKNOWN


@dataclass(frozen=True)
class LLMCorpusReport:
    records: Tuple[StructuralOutcomeRecord, ...]
    candidate_patterns_considered: int
    excluded_no_llm_proposal: Tuple[str, ...]


def build_llm_witnessed_corpus(
    corpus_path: Path = CORPUS_PATH,
    *,
    generate_fn: Optional[GenerateFn] = None,
    model: str = "llama3.2:latest",
) -> LLMCorpusReport:
    """Only length-1 patterns: the LLM is asked about a single relation, not
    a multi-hop derived composite -- same scoping reasoning as M6 v0.2's
    initial length-1-only step, not yet extended here."""
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    discovery_facts = _facts_to_nodes(data["discovery_facts"])
    evidence_facts = _facts_to_nodes(data["evidence_facts"])
    known_facts_plain = [(rel, subj, obj) for _fid, rel, subj, obj in data["discovery_facts"]]

    graph = build_structural_graph(discovery_facts)
    all_paths = discover_paths(graph, max_depth=2, max_paths=10000)

    by_skeleton: Dict[tuple, list] = {}
    for path in all_paths:
        by_skeleton.setdefault(_skeleton_key(path), []).append(path)

    records: List[StructuralOutcomeRecord] = []
    excluded: List[str] = []
    considered = 0

    starts = sorted({node_ref(f[2]) for f in data["evidence_facts"]}, key=lambda r: r.ref_id)

    for skeleton, group in sorted(by_skeleton.items(), key=lambda kv: repr(kv[0])):
        if len(group) < 2 or len(skeleton) != 1:
            continue
        pattern = generalize_path_pattern(group, pattern_id=f"pattern::{skeleton!r}")
        if pattern is None:
            continue
        considered += 1
        operator_ref_id = skeleton[0][0].ref_id

        found_any = False
        for i, start in enumerate(starts):
            result = replay_path_pattern_holdout(pattern, evidence_facts, start)
            if result.status != PATH_REPLAYED:
                continue

            proposal = propose_relation_llm(
                known_facts=known_facts_plain,
                subject=start.ref_id,
                relation=operator_ref_id,
                model=model,
                generate_fn=generate_fn,
            )
            if proposal is None:
                continue
            found_any = True

            evidence = llm_evidence_for_prediction(
                proposal,
                candidate_id=pattern.pattern_id,
                predicted_object=result.predicted_end.ref_id,
                evidence_index=i,
            )
            request = AcquisitionRequest(candidate_id=pattern.pattern_id, query_ref=pattern.pattern_id, max_level=LEVEL_A)
            acquisition_result = acquire_cold_start(
                request,
                backoff_provider=lambda req, ev=evidence: ((ev,), 0.0),
                evaluator=_evaluator,
            )
            if not acquisition_result.evidence:
                continue

            records.append(
                StructuralOutcomeRecord(
                    record_id=f"llmv1::{pattern.pattern_id}::{start.ref_id}",
                    rule=pattern,
                    novelty=1.0,
                    redundancy=0.0,
                    depth=pattern.length,
                    provenance=acquisition_result.evidence[0].provenance,
                    outcome=acquisition_result.final_state,
                )
            )

        if not found_any:
            excluded.append(f"{pattern.pattern_id}: no usable LLM proposal for any evidence-graph start")

    return LLMCorpusReport(
        records=tuple(records),
        candidate_patterns_considered=considered,
        excluded_no_llm_proposal=tuple(excluded),
    )


__all__ = ["LLMCorpusReport", "build_llm_witnessed_corpus", "CORPUS_PATH"]
