"""MetaHIA M7 -- real corpus builder using cross-mechanism consensus v0.1.

Mirrors `m7_corpus_from_text_claims_v0_1.py`'s iteration structure (same
candidate universe: length-1 patterns with a matching authored text claim),
replacing the single-mechanism parser step with
`evaluate_cross_mechanism_consensus` (witness + parser must agree).
Structural prediction (kernel2 replay against `evidence_facts`) is
unchanged.

Five honestly distinct exclusion reasons (`excluded_no_matching_text_claim`
plus the four non-AGREED reasons from `m7_cross_mechanism_consensus_v0_1.py`,
`WITNESS_FAILED`/`PARSER_FAILED` folded together as `excluded_mechanism_failed`
since both represent "one side had nothing to contribute", kept distinct
from `excluded_parsing_mismatch` and `excluded_disagreement`, which are
substantively different failure modes) -- never merged into one generic
bucket, never silently dropped.
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
    SUPPORT,
    SUPPORTED,
    UNKNOWN,
    AcquisitionRequest,
    LEVEL_A,
    acquire_cold_start,
)
from m6_structural_learning_v0_1 import StructuralOutcomeRecord
from m7_cross_mechanism_consensus_v0_1 import (
    REASON_AGREED,
    REASON_DISAGREEMENT,
    REASON_PARSER_MISMATCH,
    evaluate_cross_mechanism_consensus,
)
from m7_llm_fact_proposer_v0_1 import LLMProposal, llm_evidence_for_prediction

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
class CrossMechanismCorpusReport:
    records: Tuple[StructuralOutcomeRecord, ...]
    candidate_patterns_considered: int
    excluded_no_matching_text_claim: Tuple[str, ...]
    excluded_mechanism_failed: Tuple[str, ...]
    excluded_disagreement: Tuple[str, ...]
    excluded_parsing_mismatch: Tuple[str, ...]


def build_cross_mechanism_corpus(
    corpus_path: Path = CORPUS_PATH,
    claims_path: Path = TEXT_CLAIMS_PATH,
    *,
    witness_generate_fn=None,
    parser_generate_fn=None,
    model: str = "llama3.2:latest",
) -> CrossMechanismCorpusReport:
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    discovery_facts = _facts_to_nodes(data["discovery_facts"])
    evidence_facts = _facts_to_nodes(data["evidence_facts"])
    allowed_relations = sorted({rel for _fid, rel, _s, _o in data["discovery_facts"]})
    known_facts_plain = [(rel, subj, obj) for _fid, rel, subj, obj in data["discovery_facts"]]
    claims = _load_text_claims(claims_path)

    graph = build_structural_graph(discovery_facts)
    all_paths = discover_paths(graph, max_depth=2, max_paths=10000)

    by_skeleton: Dict[tuple, list] = {}
    for path in all_paths:
        by_skeleton.setdefault(_skeleton_key(path), []).append(path)

    records: List[StructuralOutcomeRecord] = []
    excluded_no_claim: List[str] = []
    excluded_mechanism_failed: List[str] = []
    excluded_disagreement: List[str] = []
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

            consensus = evaluate_cross_mechanism_consensus(
                known_facts=known_facts_plain, subject=start.ref_id, relation=operator_ref_id,
                text=claim["text"], allowed_relations=allowed_relations,
                witness_model=model, parser_model=model,
                witness_generate_fn=witness_generate_fn, parser_generate_fn=parser_generate_fn,
            )
            if consensus.reason != REASON_AGREED:
                if consensus.reason == REASON_DISAGREEMENT:
                    excluded_disagreement.append(f"{pattern.pattern_id}::{start.ref_id}: mechanisms disagreed")
                elif consensus.reason == REASON_PARSER_MISMATCH:
                    excluded_mismatch.append(f"{pattern.pattern_id}::{start.ref_id}: parser mismatch")
                else:
                    excluded_mechanism_failed.append(f"{pattern.pattern_id}::{start.ref_id}: {consensus.reason}")
                continue
            agreed = consensus.claim

            proposal = LLMProposal(
                relation=agreed.relation, subject=agreed.subject, object=agreed.object,
                model=f"crossconsensus::{agreed.witness_model}+{agreed.parser_model}",
                raw_response=json.dumps({"witness_model": agreed.witness_model, "parser_model": agreed.parser_model}),
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
                    record_id=f"crossconsensusv1::{pattern.pattern_id}::{start.ref_id}",
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

    return CrossMechanismCorpusReport(
        records=tuple(records),
        candidate_patterns_considered=considered,
        excluded_no_matching_text_claim=tuple(excluded_no_claim),
        excluded_mechanism_failed=tuple(excluded_mechanism_failed),
        excluded_disagreement=tuple(excluded_disagreement),
        excluded_parsing_mismatch=tuple(excluded_mismatch),
    )


__all__ = ["CrossMechanismCorpusReport", "build_cross_mechanism_corpus", "CORPUS_PATH", "TEXT_CLAIMS_PATH"]
