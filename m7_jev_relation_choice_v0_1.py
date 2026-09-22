"""MetaHIA M7 -- JEV/Kev relation-choice v0.1 (P8).

STATUS: real HTTP client implemented (2026-09-22), wired to the VERIFIED
`jaredpalmer/kev` API contract -- not the earlier skeleton's guess. See
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 3bis for the
full correction trail: the original plan assumed Kev would be "hosted via
Ollama" on the LAN sandbox; reading `jaredpalmer/kev`'s actual README and
`kev/serve.py` source (2026-09-22) shows this is WRONG -- Kev is a
standalone FastAPI/uvicorn server (`python -m kev.serve`), never an Ollama
model, and its `main()` hardcodes `uvicorn.run(app, host="127.0.0.1", ...)`
with no `--host` flag, so it will not be reachable on the LAN without an
explicit override (see the doc for the exact command). This module still
makes no assumption about whether that server is actually reachable right
now -- every call fails closed to `None` on any connection problem,
exactly like `m7_llm_fact_proposer_v0_1.py`'s own Ollama client.

Three semantic conditions, never mixed silently (governance rule,
`SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md` Sec. 5) -- implemented here via
Kev's own real mechanism for this, not simulated in prompt text: a
`choice` question's `criteria` is a mapping of option name -> description-
or-`None` ("you choose the id; the model never sees it" -- but it DOES
see every criteria key and its description, per Kev's own README). This
maps exactly onto the three conditions:

  STRICT  -- `criteria` keys are opaque symbols (R1..Rn, from
             `build_strict_symbol_map`), every description is `None`, and
             `state` is prefixed with worked examples using the SAME
             symbols -- an opaque symbol carries no information on its
             own; structural repetition across examples is the only
             channel. The only condition that actually tests this
             project's structural-abstraction hypothesis for an LLM/Kev
             consumer.
  LABELED -- `criteria` keys are the real, human-readable relation names
             (EPOUX_DE, MERE_DE, ...), every description is `None`. This
             is what the already-measured Jev benchmark
             (`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`
             Sec. 2, 22/22 cases against jev-1.13.0) actually tested.
  GLOSSED -- `criteria` keys are the real names, each with an explicit
             MetaHIA-authored description.

Non-negotiable guardrails, carried over unchanged from the measured
benchmark (P8 doc Sec. 2) and from `m7_llm_fact_proposer_v0_1.py`'s own
established precedent:

  - subject == object is always rejected (the measured T05/T08/T09
    self-loop bug: 3/16 positive cases predicted object = subject).
  - a chosen label outside the closed vocabulary is always rejected,
    never coerced to the nearest-looking known relation (the measured
    A05 failure: "conjoint" coerced into EPOUX_DE at 0.98 confidence).
  - evidence produced here is always GROUNDED_ANALOGY (kind=EXTERNAL,
    analogy=True), never GROUNDED_DIRECT -- JEV/Kev never decides truth
    itself, it only supplies evidence for the same evaluator M4/M6
    already use, exactly like `m7_llm_fact_proposer_v0_1.py`.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
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
    """The only network-shaped contract this module depends on. Mirrors
    Kev/Jev's real `POST /v1/systemone` `choice`-question shape: a `state`
    (the text to evaluate), free-text `instructions`, and `criteria` (a
    mapping of option name to an optional description -- `None` means no
    description is given for that option, which is exactly what makes
    STRICT/LABELED possible without inventing a separate API). Returns
    `(chosen_option, probability_of_chosen_option)`, or `None` if the call
    could not be completed at all -- distinct from a reachable call that
    legitimately returns an out-of-vocabulary option, which
    `propose_relation_jev` itself rejects below.
    """

    def decide(
        self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]
    ) -> Optional[Tuple[str, float]]:
        ...


class JevKevSystemOneClient:
    """Real HTTP client for a Kev/Jev-compatible `POST /v1/systemone`
    server, verified against `jaredpalmer/kev`'s actual README and source
    (2026-09-22, commit read directly via the GitHub API, not assumed
    from a description). No API key by default -- Kev's own server has no
    authentication (its README says so explicitly: "Keep it local unless
    you add authentication yourself"); nothing is hardcoded here beyond
    the caller-supplied `base_url`.
    """

    def __init__(self, base_url: str, *, model: str = "kev-latest", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def decide(
        self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]
    ) -> Optional[Tuple[str, float]]:
        payload = json.dumps(
            {
                "state": state,
                "model": self.model,
                "questions": {
                    "relation": {"type": "choice", "instructions": instructions, "criteria": dict(criteria)}
                },
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/systemone", data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
            return None
        answers = body.get("answers")
        if not isinstance(answers, dict):
            return None
        answer = answers.get("relation")
        if not isinstance(answer, dict):
            return None
        choice = answer.get("choice")
        probabilities = answer.get("probabilities")
        if not isinstance(choice, str) or not isinstance(probabilities, dict):
            return None
        positive_prob = probabilities.get(choice)
        if not isinstance(positive_prob, (int, float)):
            return None
        return choice, float(positive_prob)

    def reachable(self) -> bool:
        """Lightweight reachability probe (`GET /v1/models`), mirroring
        this project's own established pattern for Ollama (a full
        `/v1/systemone` call needs a loaded checkpoint and real compute;
        this only needs the server process to answer)."""
        request = urllib.request.Request(f"{self.base_url}/v1/models")
        try:
            with urllib.request.urlopen(request, timeout=5.0) as response:
                return response.status == 200
        except (urllib.error.URLError, OSError, TimeoutError):
            return False


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
    endpoint. Fails closed exactly like every other M7 mechanism in this
    repo: an unreachable/unusable/out-of-vocabulary/self-referential
    response is `None`, never fabricated into a proposal.
    """
    if semantic_condition not in _VALID_MODES:
        raise ValueError(f"semantic_condition must be one of {_VALID_MODES}, got {semantic_condition!r}")
    if subject == obj:
        # Measured self-loop bug (T05/T08/T09) -- refused unconditionally,
        # before any call is even made.
        return None

    if semantic_condition == RELATION_VOCABULARY_MODE_STRICT:
        if not worked_examples:
            raise ValueError(
                "STRICT mode requires at least one worked example -- an opaque "
                "symbol carries no information on its own; requiring examples "
                "here (rather than silently falling back to an unlabeled "
                "request) is deliberate, not an oversight"
            )
        symbol_map = build_strict_symbol_map(all_relations)
        inverse_map = {symbol: real for real, symbol in symbol_map.items()}
        examples_block = "\n".join(f'"{ex.text}" -> {symbol_map[ex.relation]}' for ex in worked_examples)
        state = f'Examples:\n{examples_block}\n\nNew case: "{text}"'
        instructions = "Given the same pattern as the examples, which label applies to the new case?"
        criteria: Dict[str, Optional[str]] = {symbol: None for symbol in symbol_map.values()}
    elif semantic_condition == RELATION_VOCABULARY_MODE_LABELED:
        inverse_map = {r: r for r in all_relations}
        state = f'"{text}"'
        instructions = "Which relation applies to this sentence?"
        criteria = {r: None for r in all_relations}
    else:
        missing = set(all_relations) - set(glosses)
        if missing:
            raise ValueError(f"GLOSSED mode requires a gloss for every relation, missing: {sorted(missing)}")
        inverse_map = {r: r for r in all_relations}
        state = f'"{text}"'
        instructions = "Which relation applies to this sentence?"
        criteria = dict(glosses)

    result = client.decide(state=state, instructions=instructions, criteria=criteria)
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
        positive_prob=float(positive_prob),
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
    SUPPORT; disagreement is CHALLENGE -- JEV/Kev never gets to declare
    CONTRADICTED/SUPPORTED itself.

    `confidence` uses `proposal.positive_prob` directly (unlike the
    Ollama-based proposer, which has no genuinely calibrated probability
    to offer and leaves the default of 1.0) -- Kev's whole rationale for
    selection over Jev/OpenJev/LocalJev (P8 doc Sec. 3) is that its
    probabilities are read from logits, not self-reported.

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
    "JevKevSystemOneClient",
    "JevProposal",
    "WorkedExample",
    "build_strict_symbol_map",
    "propose_relation_jev",
    "jev_evidence_for_prediction",
]
