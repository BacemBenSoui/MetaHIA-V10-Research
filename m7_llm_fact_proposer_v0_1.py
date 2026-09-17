"""MetaHIA M7 -- Empirical LLM Loop v0.1 (fact-proposer scope).

Roadmap architecture: "Le LLM reste une branche d'observation/production ;
il n'est pas le fondement du raisonnement structurel." M7 v0.1 keeps that
contract literally: the LLM never decides truth, never bypasses M4's
evidence-acquisition machinery, and its output is classified as the
WEAKEST of M4's three provenance tiers -- GROUNDED_ANALOGY, never
GROUNDED_DIRECT (that stays reserved for genuine structural replay against
real facts) and never UNGROUNDED_HUMAN (the LLM is not a human source).

Scope chosen explicitly before implementation (2026-09-17): the LLM acts as
an independent witness over the EXISTING structured corpus, exactly the same
role `family_tree_verification_claims_v0_1.json` plays for M6's
non-degenerate mechanism -- not a free-text-to-structure parser (that
remains a separately deferred roadmap item). Given a structural prediction
already produced by real kernel replay (`predicted_object`), the LLM is
asked, independently, what it thinks the relation's target is; agreement or
disagreement with the real prediction becomes SUPPORT or CHALLENGE evidence,
fed through the exact same `acquire_cold_start()` machinery M4/M6 already
use. An LLM response that cannot be parsed into the closed, already-observed
relation vocabulary is treated as no evidence at all -- excluded,
transparently, never fabricated into a proposal it didn't actually make.

Backend: local Ollama (`http://localhost:11434`), chosen explicitly to avoid
reopening the zero-coupling boundary with MetaHIA-Consolidated-Repo (which
has its own, separate `llm/ollama_backend.py`) and to avoid managing an API
key/cost in this research repo. No credentials are read, stored, or
required.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from m4_cold_start_evidence_v0_1 import (
    CHALLENGE,
    EXTERNAL,
    SUPPORT,
    EvidenceRecord,
    build_evidence,
)

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:latest"


class OllamaUnavailable(Exception):
    """Raised when the local Ollama server cannot be reached at all --
    distinct from a reachable server giving an unusable response (which is
    "no proposal", not an error)."""


def ollama_generate_json(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    host: str = OLLAMA_HOST,
    timeout: float = 30.0,
) -> Optional[dict]:
    """Real call to a local Ollama instance, JSON-constrained output.

    Returns the parsed JSON object, or None if the server responded but the
    output was not valid JSON (a genuine "no usable proposal", not an
    error). Raises OllamaUnavailable if the server cannot be reached at all
    -- callers decide whether that should skip this evidence source or
    propagate.
    """
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode("utf-8")
    request = urllib.request.Request(
        f"{host}/api/generate", data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read())
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise OllamaUnavailable(f"could not reach Ollama at {host}: {exc}") from exc

    raw = body.get("response", "")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


@dataclass(frozen=True)
class LLMProposal:
    relation: str
    subject: str
    object: str
    model: str
    raw_response: str


GenerateFn = Callable[[str], Optional[dict]]


def _build_prompt(known_facts: Sequence[Tuple[str, str, str]], subject: str, relation: str) -> str:
    facts_block = "\n".join(f"{rel}({subj}, {obj})" for rel, subj, obj in known_facts)
    return (
        "You are given family facts as triples RELATION(subject, object):\n"
        f"{facts_block}\n\n"
        f'By analogy with the patterns above, determine the single most plausible value for '
        f'the object in {relation}("{subject}", ?) -- i.e. who is the target of the '
        f'"{relation}" relation for subject "{subject}".\n\n'
        'Answer with ONLY a JSON object like {"object": "SomeName"} and nothing else. Do not '
        "explain your reasoning."
    )


def propose_relation_llm(
    *,
    known_facts: Sequence[Tuple[str, str, str]],
    subject: str,
    relation: str,
    model: str = DEFAULT_MODEL,
    generate_fn: Optional[GenerateFn] = None,
) -> Optional[LLMProposal]:
    """Asks the LLM to independently predict the object of `relation(subject, ?)`.

    `subject` and `relation` are supplied by the caller (already known from
    the structural context being tested) -- only `object` is genuinely
    elicited from the LLM, and the real predicted value is NEVER included in
    the prompt; leaking it would make agreement trivial rather than a
    genuine independent check (found and fixed 2026-09-17 after a first live
    run against corpus v0.2 returned 16/16 SUPPORTED -- the original prompt
    had put the real predicted object directly in both the instruction and
    the JSON answer example, so the model was echoing it back rather than
    inferring it).

    Fails closed: any response that is not valid JSON, missing a required
    key, or not a non-empty string is treated as no proposal at all, never
    fabricated into one.
    """
    prompt = _build_prompt(known_facts, subject, relation)
    generate = generate_fn or (lambda p: ollama_generate_json(p, model=model))
    raw = generate(prompt)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    proposed_object = raw.get("object")
    if not isinstance(proposed_object, str) or not proposed_object.strip():
        return None
    return LLMProposal(
        relation=relation,
        subject=subject,
        object=proposed_object.strip(),
        model=model,
        raw_response=json.dumps(raw),
    )


def llm_evidence_for_prediction(
    proposal: LLMProposal,
    *,
    candidate_id: str,
    predicted_object: str,
    evidence_index: int,
) -> EvidenceRecord:
    """Classifies an LLM proposal against a real structural prediction.

    Always GROUNDED_ANALOGY (kind=EXTERNAL, analogy=True) -- an LLM
    proposal is never GROUNDED_DIRECT (that is reserved for genuine
    structural replay against real facts) and never UNGROUNDED_HUMAN (the
    LLM is not a human source). Agreement with the real prediction is
    SUPPORT; disagreement is CHALLENGE -- the LLM never gets to declare
    CONTRADICTED/SUPPORTED itself, only supply evidence for the same
    evaluator M4/M6 already use.
    """
    agrees = proposal.object == predicted_object
    return build_evidence(
        evidence_id=f"EV-LLM-{candidate_id}-{evidence_index}",
        candidate_id=candidate_id,
        relation=proposal.relation,
        polarity=SUPPORT if agrees else CHALLENGE,
        source_id=f"llm::{proposal.model}",
        kind=EXTERNAL,
        direct=False,
        analogy=True,
    )


__all__ = [
    "OLLAMA_HOST",
    "DEFAULT_MODEL",
    "OllamaUnavailable",
    "ollama_generate_json",
    "LLMProposal",
    "GenerateFn",
    "propose_relation_llm",
    "llm_evidence_for_prediction",
]
