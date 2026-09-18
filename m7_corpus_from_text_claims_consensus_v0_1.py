"""MetaHIA M7 -- real corpus builder using the consensus text-claim parser v0.1.

Mirrors `m7_corpus_from_text_claims_v0_1.py`'s structure exactly, replacing
the single-model extraction step with `parse_claim_from_text_with_consensus`
(`m7_text_claim_parser_consensus_v0_1.py`) -- structural prediction (kernel2
replay against `evidence_facts`) is unchanged.

Four honestly distinct exclusion reasons (never merged, never silently
dropped), one more than the single-model mechanism because consensus adds a
genuinely new failure mode:

1. `excluded_no_matching_text_claim` -- no sentence in the corpus is about
   this candidate at all (unchanged from the single-model mechanism).
2. `excluded_voter_failed` -- at least one of the two voters rejected the
   sentence under its own fail-closed contract (malformed output or a
   relation outside the closed vocabulary).
3. `excluded_disagreement` -- both voters answered usably, but did not agree
   exactly on (subject, relation, object). This is the mechanism's whole
   point: a single model might have answered confidently but wrongly, and
   consensus catches that by requiring a second, independent model to
   reach the identical conclusion.
4. `excluded_parsing_mismatch` -- both voters agreed with EACH OTHER, but
   their agreed answer does not match what the sentence is independently
   known to be about (the same fidelity check as the single-model
   mechanism, now applied to the consensus result).
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
from m7_text_claim_parser_consensus_v0_1 import (
    REASON_AGREED,
    REASON_DISAGREEMENT,
    parse_claim_from_text_with_consensus,
)

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
class ConsensusTextClaimCorpusReport:
    records: Tuple[StructuralOutcomeRecord, ...]
    candidate_patterns_considered: int
    excluded_no_matching_text_claim: Tuple[str, ...]
    excluded_voter_failed: Tuple[str, ...]
    excluded_disagreement: Tuple[str, ...]
    excluded_parsing_mismatch: Tuple[str, ...]


def build_consensus_text_claim_corpus(
    corpus_path: Path = CORPUS_PATH,
    claims_path: Path = TEXT_CLAIMS_PATH,
    *,
    generate_fn_a: Optional[GenerateFn] = None,
    generate_fn_b: Optional[GenerateFn] = None,
) -> ConsensusTextClaimCorpusReport:
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
    excluded_voter_failed: List[str] = []
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

            consensus = parse_claim_from_text_with_consensus(
                claim["text"], allowed_relations=allowed_relations,
                generate_fn_a=generate_fn_a, generate_fn_b=generate_fn_b,
            )
            if consensus.reason != REASON_AGREED:
                if consensus.reason == REASON_DISAGREEMENT:
                    excluded_disagreement.append(f"{pattern.pattern_id}::{start.ref_id}: voters disagreed")
                else:
                    excluded_voter_failed.append(f"{pattern.pattern_id}::{start.ref_id}: {consensus.reason}")
                continue
            parsed = consensus.claim
            if parsed.subject != claim["subject"] or parsed.relation != claim["relation"]:
                excluded_mismatch.append(
                    f"{pattern.pattern_id}::{start.ref_id}: consensus ({parsed.subject}, {parsed.relation}) "
                    f"!= declared ({claim['subject']}, {claim['relation']})"
                )
                continue

            proposal = LLMProposal(
                relation=parsed.relation, subject=parsed.subject, object=parsed.object,
                model=f"consensus::{parsed.models[0]}+{parsed.models[1]}", raw_response=json.dumps(parsed.models),
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
                    record_id=f"textconsensusv1::{pattern.pattern_id}::{start.ref_id}",
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

    return ConsensusTextClaimCorpusReport(
        records=tuple(records),
        candidate_patterns_considered=considered,
        excluded_no_matching_text_claim=tuple(excluded_no_claim),
        excluded_voter_failed=tuple(excluded_voter_failed),
        excluded_disagreement=tuple(excluded_disagreement),
        excluded_parsing_mismatch=tuple(excluded_mismatch),
    )


__all__ = ["ConsensusTextClaimCorpusReport", "build_consensus_text_claim_corpus", "CORPUS_PATH", "TEXT_CLAIMS_PATH"]
