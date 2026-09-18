"""MetaHIA M7 -- real corpus builder using the free-text claim parser v0.1.

Mirrors `m7_corpus_from_llm_v0_1.py`'s structure: structural prediction
(kernel2 replay against `evidence_facts`, disjoint from `discovery_facts`) is
unchanged; the difference is the verification step now goes through
`m7_text_claim_parser_v0_1.parse_claim_from_text()` on an independently
authored French sentence (`corpus/family_tree_text_claims_v0_1.json`) instead
of asking a closed question about a known subject/relation.

Three distinct, honestly separate exclusion reasons (never merged into one
generic "no evidence" bucket, and never silently dropped):

1. `excluded_no_matching_text_claim` -- no sentence in the corpus is even
   ABOUT this (subject, relation) candidate at all.
2. `excluded_no_parse` -- a matching sentence exists, but the LLM's
   extraction was rejected by `parse_claim_from_text`'s fail-closed contract
   (malformed JSON, missing field, or a relation outside the closed
   vocabulary).
3. `excluded_parsing_mismatch` -- the LLM DID extract a well-formed claim,
   but its subject/relation do not match what this sentence is independently
   known to be about (a genuine parsing-fidelity failure, distinct from a
   disagreement about the OBJECT, which becomes CHALLENGE evidence exactly
   as in the closed-question mechanism, never excluded).

Only length-1 patterns, same scoping precedent as `m7_corpus_from_llm_v0_1.py`.
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
from m7_llm_fact_proposer_v0_1 import GenerateFn, LLMProposal, llm_evidence_for_prediction
from m7_text_claim_parser_v0_1 import parse_claim_from_text

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "family_tree_facts_v0_2.json"
TEXT_CLAIMS_PATH = Path(__file__).resolve().parent / "corpus" / "family_tree_text_claims_v0_1.json"


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


def _load_text_claims(claims_path: Path) -> Dict[Tuple[str, str], dict]:
    data = json.loads(claims_path.read_text(encoding="utf-8"))
    return {(claim["subject"], claim["relation"]): claim for claim in data["claims"]}


@dataclass(frozen=True)
class TextClaimCorpusReport:
    records: Tuple[StructuralOutcomeRecord, ...]
    candidate_patterns_considered: int
    excluded_no_matching_text_claim: Tuple[str, ...]
    excluded_no_parse: Tuple[str, ...]
    excluded_parsing_mismatch: Tuple[str, ...]


def build_text_claim_corpus(
    corpus_path: Path = CORPUS_PATH,
    claims_path: Path = TEXT_CLAIMS_PATH,
    *,
    generate_fn: Optional[GenerateFn] = None,
    model: str = "llama3.2:latest",
) -> TextClaimCorpusReport:
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    discovery_facts = _facts_to_nodes(data["discovery_facts"])
    evidence_facts = _facts_to_nodes(data["evidence_facts"])
    allowed_relations = sorted({rel for _fid, rel, _s, _o in data["discovery_facts"]})
    claims = _load_text_claims(claims_path)

    graph = build_structural_graph(discovery_facts)
    all_paths = discover_paths(graph, max_depth=2, max_paths=10000)

    by_skeleton: Dict[tuple, list] = {}
    for path in all_paths:
        by_skeleton.setdefault(_skeleton_key(path), []).append(path)

    records: List[StructuralOutcomeRecord] = []
    excluded_no_claim: List[str] = []
    excluded_no_parse: List[str] = []
    excluded_mismatch: List[str] = []
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

            claim = claims.get((start.ref_id, operator_ref_id))
            if claim is None:
                excluded_no_claim.append(f"{pattern.pattern_id}::{start.ref_id}: no matching text claim")
                continue
            found_any = True

            parsed = parse_claim_from_text(
                claim["text"], allowed_relations=allowed_relations, model=model, generate_fn=generate_fn
            )
            if parsed is None:
                excluded_no_parse.append(f"{pattern.pattern_id}::{start.ref_id}: LLM extraction rejected (fail-closed)")
                continue
            if parsed.subject != claim["subject"] or parsed.relation != claim["relation"]:
                excluded_mismatch.append(
                    f"{pattern.pattern_id}::{start.ref_id}: parsed ({parsed.subject}, {parsed.relation}) "
                    f"!= declared ({claim['subject']}, {claim['relation']})"
                )
                continue

            proposal = LLMProposal(
                relation=parsed.relation, subject=parsed.subject, object=parsed.object,
                model=parsed.model, raw_response=parsed.raw_response,
            )
            evidence = llm_evidence_for_prediction(
                proposal, candidate_id=pattern.pattern_id, predicted_object=result.predicted_end.ref_id, evidence_index=i
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
                    record_id=f"textclaimv1::{pattern.pattern_id}::{start.ref_id}",
                    rule=pattern,
                    novelty=1.0,
                    redundancy=0.0,
                    depth=pattern.length,
                    provenance=acquisition_result.evidence[0].provenance,
                    outcome=acquisition_result.final_state,
                )
            )

        if not found_any:
            excluded_no_claim.append(f"{pattern.pattern_id}: no matching text claim for any evidence-graph start")

    return TextClaimCorpusReport(
        records=tuple(records),
        candidate_patterns_considered=considered,
        excluded_no_matching_text_claim=tuple(excluded_no_claim),
        excluded_no_parse=tuple(excluded_no_parse),
        excluded_parsing_mismatch=tuple(excluded_mismatch),
    )


__all__ = ["TextClaimCorpusReport", "build_text_claim_corpus", "CORPUS_PATH", "TEXT_CLAIMS_PATH"]
