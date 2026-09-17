"""MetaHIA M6 -- real corpus builder from genuine M4/M5 execution v0.1.

Builds `StructuralOutcomeRecord`s for M6 by actually running the pipeline
end to end, rather than hand-constructing records for a single invariant:

    fact corpus (corpus/family_tree_facts_v0_1.json)
        -> kernel2.build_structural_graph / discover_paths          (real)
        -> kernel2.generalize_path_pattern                          (real, E20-D.12)
        -> e20d_cognitive_control_v0_1.build_candidate/score        (real, E20-D.19)
        -> m4_cold_start_evidence_v0_1.acquire_cold_start           (real, M4)
        -> m6_structural_learning_v0_1.StructuralOutcomeRecord

Independence of evidence (M6 design decision 4 -- no gold from derivation):
`discovery_facts` are the ONLY facts used to discover and generalize a
pattern. `evidence_facts` are a disjoint set, never used for discovery, and
are the ONLY source `acquire_cold_start()` is allowed to draw on. A pattern's
outcome therefore always comes from checking it against facts it was never
built from -- structurally the same holdout-generalization discipline
E20-D/M3 already use, reused here as M4's actual evidence source rather than
as a standalone test assertion.

Honesty note (found by running this, not assumed in advance): for a pattern
of length L, `replay_path_pattern_holdout` can only ever return REPLAYED
(and, since the replay graph is built directly from the real evidence facts,
a REPLAYED result is automatically a correct structural match -- there is no
way for this mechanism to replay to an observed-but-wrong endpoint) or
NOT_FOUND/AMBIGUOUS (no usable evidence at that attempt). On a small,
internally-consistent family-tree corpus this means genuine SUPPORTED
outcomes are directly reachable, but genuine CONTRADICTED outcomes are not,
by construction, not by omission -- see `demo_contradicted_case()` below for
a separately-labeled, deliberately-conflicting-fact check that the
CONTRADICTED path through the same real machinery still behaves correctly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from kernel2 import (
    Node,
    NodeRef,
    OBSERVATION,
    PATH_REPLAYED,
    build_structural_graph,
    discover_paths,
    generalize_path_pattern,
    node_ref,
)
from e20d_cognitive_control_v0_1 import build_candidate, score_candidate
from m4_cold_start_evidence_v0_1 import (
    CHALLENGE,
    CONTRADICTED,
    OBSERVATION as EVIDENCE_KIND_OBSERVATION,
    SUPPORT,
    SUPPORTED,
    UNKNOWN,
    AcquisitionRequest,
    LEVEL_A,
    acquire_cold_start,
    build_evidence,
)
from m6_structural_learning_v0_1 import StructuralOutcomeRecord

DEFAULT_CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "family_tree_facts_v0_1.json"
CORPUS_PATH_V0_2 = Path(__file__).resolve().parent / "corpus" / "family_tree_facts_v0_2.json"


def _facts_to_nodes(facts: List[list]) -> List[Node]:
    return [
        Node(fact_id, OBSERVATION, (node_ref(rel), node_ref(subj), node_ref(obj)), provenance=(fact_id,))
        for fact_id, rel, subj, obj in facts
    ]


@dataclass(frozen=True)
class RealCorpusBuildReport:
    """Transparent accounting of what happened -- nothing is silently dropped."""

    records: Tuple[StructuralOutcomeRecord, ...]
    candidate_patterns_considered: int
    excluded_no_evidence: Tuple[str, ...]


def _skeleton_key(path) -> tuple:
    return tuple((step.operator, step.direction) for step in path.steps)


def _replay_evidence_for_pattern(pattern, evidence_facts: List[Node], evidence_graph_nodes) -> Tuple[list, float]:
    """Real M4 backoff_provider: attempts replay from every node that appears
    as a source in the evidence facts, using ONLY evidence_facts (never the
    discovery facts the pattern came from)."""
    from kernel2 import replay_path_pattern_holdout

    evidence = []
    starts = {node_ref(fact[2]) for fact in evidence_graph_nodes}  # subj of each raw evidence fact
    for i, start in enumerate(sorted(starts, key=lambda r: r.ref_id)):
        result = replay_path_pattern_holdout(pattern, evidence_facts, start)
        if result.status != PATH_REPLAYED:
            continue
        # A REPLAYED result against a graph built purely from evidence_facts
        # is, by construction, a real structural match -- direct, non-analogy,
        # non-human evidence.
        evidence.append(
            build_evidence(
                evidence_id=f"EV-{pattern.pattern_id}-{i}",
                candidate_id=pattern.pattern_id,
                relation=result.predicted_end,
                polarity=SUPPORT,
                source_id=f"holdout_replay::{start.ref_id}",
                kind=EVIDENCE_KIND_OBSERVATION,
                direct=True,
            )
        )
    return evidence, 0.0


def _support_only_evaluator(candidate_id: str, accepted_evidence) -> str:
    if any(e.polarity == CHALLENGE for e in accepted_evidence):
        return CONTRADICTED
    if any(e.polarity == SUPPORT for e in accepted_evidence):
        return SUPPORTED
    return UNKNOWN


def build_real_corpus(corpus_path: Path = DEFAULT_CORPUS_PATH) -> RealCorpusBuildReport:
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    discovery_facts = _facts_to_nodes(data["discovery_facts"])
    evidence_facts = _facts_to_nodes(data["evidence_facts"])

    graph = build_structural_graph(discovery_facts)
    all_paths = discover_paths(graph, max_depth=2, max_paths=10000)

    by_skeleton: Dict[tuple, list] = {}
    for path in all_paths:
        by_skeleton.setdefault(_skeleton_key(path), []).append(path)

    known_paths: list = []
    records: List[StructuralOutcomeRecord] = []
    excluded: List[str] = []
    considered = 0

    for skeleton, group in sorted(by_skeleton.items(), key=lambda kv: repr(kv[0])):
        if len(group) < 2:
            continue  # generalize_path_pattern itself requires >= 2 -- no rule to test
        pattern = generalize_path_pattern(group, pattern_id=f"pattern::{skeleton!r}")
        if pattern is None:
            continue
        considered += 1

        representative = group[0]
        candidate = build_candidate(
            representative,
            expected_gain=1.0,  # neutral placeholder -- see module docstring; not a claim of a gain model
            structural_novelty=1.0,  # first time this skeleton is scored in this corpus pass
            known_paths=known_paths,
        )
        known_paths.append(representative)
        score = score_candidate(candidate)

        evidence, cost = _replay_evidence_for_pattern(pattern, evidence_facts, data["evidence_facts"])
        request = AcquisitionRequest(candidate_id=pattern.pattern_id, query_ref=pattern.pattern_id, max_level=LEVEL_A)
        result = acquire_cold_start(
            request,
            backoff_provider=lambda req, ev=evidence, c=cost: (ev, c),
            evaluator=_support_only_evaluator,
        )

        if not result.evidence:
            excluded.append(f"{pattern.pattern_id}: no admissible evidence from holdout replay")
            continue

        provenance = result.evidence[0].provenance
        records.append(
            StructuralOutcomeRecord(
                record_id=f"real::{pattern.pattern_id}",
                rule=pattern,
                novelty=score.novelty,
                redundancy=score.redundancy,
                depth=pattern.length,
                provenance=provenance,
                outcome=result.final_state,
            )
        )

    return RealCorpusBuildReport(
        records=tuple(records),
        candidate_patterns_considered=considered,
        excluded_no_evidence=tuple(excluded),
    )


def demo_contradicted_case() -> StructuralOutcomeRecord:
    """Deliberately-conflicting-fact check (NOT part of the real corpus
    statistics): confirms the CONTRADICTED path through the same real
    acquire_cold_start()/evaluator machinery behaves correctly, since the
    family-tree corpus is internally consistent and can never produce a
    genuine conflict on its own (see module docstring)."""
    discovery = _facts_to_nodes([["D1", "MERE_DE", "Zoe", "Tom"], ["D2", "MERE_DE", "Zoe", "Ana"]])
    graph = build_structural_graph(discovery)
    paths = discover_paths(graph, max_depth=1, max_paths=100)
    by_skeleton: Dict[tuple, list] = {}
    for p in paths:
        by_skeleton.setdefault(_skeleton_key(p), []).append(p)
    forward_paths = next(group for group in by_skeleton.values() if group[0].steps[0].direction == "FORWARD")
    pattern = generalize_path_pattern(forward_paths)
    assert pattern is not None

    # A conflicting independent fact: same subject/relation, DIFFERENT object
    # than what any structural match would otherwise confirm.
    conflicting_evidence = [
        build_evidence(
            evidence_id="EV-CONFLICT-1",
            candidate_id=pattern.pattern_id,
            relation=NodeRef("Someone_Else"),
            polarity=CHALLENGE,
            source_id="deliberate_conflict_check",
            kind=EVIDENCE_KIND_OBSERVATION,
            direct=True,
        )
    ]
    request = AcquisitionRequest(candidate_id=pattern.pattern_id, query_ref=pattern.pattern_id, max_level=LEVEL_A)
    result = acquire_cold_start(
        request,
        backoff_provider=lambda req: (conflicting_evidence, 0.0),
        evaluator=_support_only_evaluator,
    )
    assert result.final_state == CONTRADICTED
    return StructuralOutcomeRecord(
        record_id="demo::contradicted",
        rule=pattern,
        novelty=1.0,
        redundancy=0.0,
        depth=pattern.length,
        provenance=result.evidence[0].provenance,
        outcome=result.final_state,
    )


__all__ = [
    "RealCorpusBuildReport",
    "build_real_corpus",
    "demo_contradicted_case",
    "DEFAULT_CORPUS_PATH",
    "CORPUS_PATH_V0_2",
]
