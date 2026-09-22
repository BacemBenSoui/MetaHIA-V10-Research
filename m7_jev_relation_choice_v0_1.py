"""MetaHIA M7 -- JEV/Kev relation-choice skeleton v0.1 (P8).

STATUS: SKELETON ONLY. No real network call is made anywhere in this
file -- prepared ahead of infrastructure (2026-09-22, user provisioning a
Kev host on the LAN sandbox `192.168.1.11`) so the semantic-condition
plumbing exists and is tested before the first real client is wired in.
See `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 4-5bis
and `documentation/SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md` Sec. 8ter for
the full rationale. This file does not lift the infrastructure block
stated there.

Three semantic conditions, never mixed silently (governance rule,
`SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md` Sec. 5) -- every `JevProposal`
and every `EvidenceRecord` produced here carries which one was used:

  STRICT  -- the model sees only opaque symbols (R1..Rn) for the closed
             relation vocabulary, plus a handful of worked examples using
             the SAME symbols. Structural analogy is the only channel by
             which the model could get this right -- the only condition
             that actually tests this project's structural-abstraction
             hypothesis for an LLM consumer, and the priority target once
             infrastructure exists.
  LABELED -- the model sees the real, human-readable relation names
             (EPOUX_DE, MERE_DE, ...), no MetaHIA-authored definition.
             This is what the already-measured Jev benchmark
             (`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`
             Sec. 2, 22/22 cases against jev-1.13.0) actually tested --
             reclassified as this tier, not STRICT.
  GLOSSED -- LABELED plus an explicit MetaHIA-authored definition per
             relation.

Non-negotiable guardrails, carried over unchanged from the measured
benchmark (P8 doc Sec. 2) and from `m7_llm_fact_proposer_v0_1.py`'s own
established precedent:

  - subject == object is always rejected (the measured T05/T08/T09
    self-loop bug: 3/16 positive cases predicted object = subject).
  - a chosen label outside the closed vocabulary is always rejected,
    never coerced to the nearest-looking known relation (the measured
    A05 failure: "conjoint" coerced into EPOUX_DE at 0.98 confidence).
  - evidence produced here is always GROUNDED_ANALOGY (kind=EXTERNAL,
    analogy=True), never GROUNDED_DIRECT -- JEV never decides truth
    itself, it only supplies evidence for the same evaluator M4/M6
    already use, exactly like `m7_llm_fact_proposer_v0_1.py`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Protocol, Sequence, Tuple

from m4_cold_start_evidence_v0_1 import (
    CHALLENGE,
    EXTERNAL,
    SUPPORT,
    EvidenceRecord,
    build_evidence,
)

RELATION_VOCABULARY_MODE_STRICT = "STRICT"
RELATION_VOCABULARY_MODE_LABELED = "LABELED"
RELATION_VOCABULARY_MODE_GLOSSED = "GLOSSED"
_VALID_MODES = (
    RELATION_VOCABULARY_MODE_STRICT,
    RELATION_VOCABULARY_MODE_LABELED,
    RELATION_VOCABULARY_MODE_GLOSSED,
)


class JevDecideClient(Protocol):
    """The only network-shaped contract this module depends on -- never
    implemented here, always injected by the caller. Mirrors the
    already-measured Jev API's own Choice-call shape (`POST
    /v1/systemone`, `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`
    Sec. 3): given a context string and a closed set of choice labels,
    return (chosen_label, positive_prob), or None if the call could not
    be completed at all (unreachable, malformed response) -- distinct
    from a reachable call that legitimately returns an out-of-vocabulary
    label, which `propose_relation_jev` itself rejects below."""

    def decide(self, *, context: str, choices: Sequence[str]) -> Optional[Tuple[str, float]]:
        ...


@dataclass(frozen=True)
class WorkedExample:
    """One resolved (text, relation) pair, presented to the model in
    STRICT mode using the SAME opaque symbol as the case under test.
    Structural repetition across examples is the only way a genuinely
    opaque symbol can carry any information at all -- never its own
    name, which by construction (`build_strict_symbol_map`) never
    resembles the real relation it stands for."""

    text: str
    relation: str


@dataclass(frozen=True)
class JevProposal:
    subject: str
    relation: str
    object: str
    positive_prob: float
    model: str
    semantic_condition: str
    raw_response: str


def build_strict_symbol_map(vocabulary: Sequence[str]) -> Dict[str, str]:
    """Deterministic, order-independent bijection from the REAL closed
    vocabulary to opaque symbols (R1..Rn). Sorted alphabetically first so
    the mapping never depends on caller-supplied ordering (which could
    itself leak information, e.g. grouping semantic opposites together) --
    the only information content of the mapping is "there are N distinct
    relations", nothing about what any of them mean or how they relate to
    each other.
    """
    if not vocabulary:
        raise ValueError("relation vocabulary must not be empty")
    if len(set(vocabulary)) != len(vocabulary):
        raise ValueError("relation vocabulary must not contain duplicates")
    ordered = sorted(vocabulary)
    return {real: f"R{i + 1}" for i, real in enumerate(ordered)}


def _build_context_strict(
    text: str, symbol_map: Mapping[str, str], worked_examples: Sequence[WorkedExample]
) -> str:
    if not worked_examples:
        raise ValueError(
            "STRICT mode requires at least one worked example -- an opaque "
            "symbol carries no information on its own; requiring examples "
            "here (rather than silently falling back to an unlabeled "
            "request) is deliberate, not an oversight"
        )
    examples_block = "\n".join(f'"{ex.text}" -> {symbol_map[ex.relation]}' for ex in worked_examples)
    return f'Examples:\n{examples_block}\n\nGiven the same pattern, which label applies to: "{text}"?'


def _build_context_labeled(text: str) -> str:
    return f'Sentence: "{text}"\n\nWhich relation applies?'


def _build_context_glossed(text: str, glosses: Mapping[str, str]) -> str:
    glosses_block = "\n".join(f"{rel} = {definition}" for rel, definition in sorted(glosses.items()))
    return f'Relation definitions:\n{glosses_block}\n\nSentence: "{text}"\n\nWhich relation applies?'


def propose_relation_jev(
    *,
    text: str,
    subject: str,
    obj: str,
    all_relations: Sequence[str],
    semantic_condition: str,
    client: JevDecideClient,
    model_name: str = "jev",
    worked_examples: Sequence[WorkedExample] = (),
    glosses: Mapping[str, str] = {},
) -> Optional[JevProposal]:
    """Calls the injected `client.decide(...)` -- never a hardcoded
    endpoint, never a real network request from this module itself.
    Fails closed exactly like every other M7 mechanism in this repo: an
    unreachable/unusable/out-of-vocabulary/self-referential response is
    `None`, never fabricated into a proposal.
    """
    if semantic_condition not in _VALID_MODES:
        raise ValueError(f"semantic_condition must be one of {_VALID_MODES}, got {semantic_condition!r}")
    if subject == obj:
        # Measured self-loop bug (T05/T08/T09) -- refused unconditionally,
        # before any call is even made.
        return None

    if semantic_condition == RELATION_VOCABULARY_MODE_STRICT:
        symbol_map = build_strict_symbol_map(all_relations)
        inverse_map = {symbol: real for real, symbol in symbol_map.items()}
        context = _build_context_strict(text, symbol_map, worked_examples)
        choices = tuple(symbol_map[r] for r in sorted(all_relations))
    elif semantic_condition == RELATION_VOCABULARY_MODE_LABELED:
        inverse_map = {r: r for r in all_relations}
        context = _build_context_labeled(text)
        choices = tuple(sorted(all_relations))
    else:
        missing = set(all_relations) - set(glosses)
        if missing:
            raise ValueError(f"GLOSSED mode requires a gloss for every relation, missing: {sorted(missing)}")
        inverse_map = {r: r for r in all_relations}
        context = _build_context_glossed(text, glosses)
        choices = tuple(sorted(all_relations))

    result = client.decide(context=context, choices=choices)
    if result is None:
        return None
    chosen, positive_prob = result
    if chosen not in inverse_map:
        # Closed-vocabulary violation (measured A04/A05 failure mode) --
        # never coerced to the nearest-looking known relation.
        return None
    if not isinstance(positive_prob, (int, float)) or not 0.0 <= float(positive_prob) <= 1.0:
        # A malformed probability from the client is a malformed
        # response, not a usable proposal -- fails closed here rather
        # than crashing later inside EvidenceRecord.validate().
        return None
    real_relation = inverse_map[chosen]

    return JevProposal(
        subject=subject,
        relation=real_relation,
        object=obj,
        positive_prob=positive_prob,
        model=model_name,
        semantic_condition=semantic_condition,
        raw_response=json.dumps({"chosen": chosen, "positive_prob": positive_prob}),
    )


def jev_evidence_for_prediction(
    proposal: JevProposal,
    *,
    candidate_id: str,
    predicted_relation: str,
    evidence_index: int,
) -> EvidenceRecord:
    """Mirrors `m7_llm_fact_proposer_v0_1.llm_evidence_for_prediction`
    exactly: always GROUNDED_ANALOGY (kind=EXTERNAL, analogy=True), never
    GROUNDED_DIRECT. Agreement with the real structural prediction is
    SUPPORT; disagreement is CHALLENGE -- JEV never gets to declare
    CONTRADICTED/SUPPORTED itself.

    `confidence` uses `proposal.positive_prob` directly (unlike the
    Ollama-based proposer, which has no genuinely calibrated probability
    to offer and leaves the default of 1.0) -- Kev's whole rationale for
    selection over Jev/OpenJev/LocalJev (P8 doc Sec. 3) is that its
    probabilities are read from logits, not self-reported, so this is the
    first M7 evidence source in this project able to supply a real
    confidence value here.

    `metadata["semantic_condition"]` is the field the governance rule
    (`SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md` Sec. 5) requires on every
    evidence record produced by an external model -- carried through
    `EvidenceRecord`'s own existing `metadata` field, no change to
    `m4_cold_start_evidence_v0_1.py` needed.
    """
    agrees = proposal.relation == predicted_relation
    return build_evidence(
        evidence_id=f"EV-JEV-{candidate_id}-{evidence_index}",
        candidate_id=candidate_id,
        relation=proposal.relation,
        polarity=SUPPORT if agrees else CHALLENGE,
        source_id=f"jev::{proposal.model}",
        kind=EXTERNAL,
        confidence=proposal.positive_prob,
        direct=False,
        analogy=True,
        metadata={"semantic_condition": proposal.semantic_condition},
    )


__all__ = [
    "RELATION_VOCABULARY_MODE_STRICT",
    "RELATION_VOCABULARY_MODE_LABELED",
    "RELATION_VOCABULARY_MODE_GLOSSED",
    "JevDecideClient",
    "JevProposal",
    "WorkedExample",
    "build_strict_symbol_map",
    "propose_relation_jev",
    "jev_evidence_for_prediction",
]
