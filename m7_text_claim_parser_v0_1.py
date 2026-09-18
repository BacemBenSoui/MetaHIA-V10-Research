"""MetaHIA M7 -- free-text claim parser v0.1.

Architectural role chosen explicitly before implementation (2026-09-18, over
the alternative of having the LLM author new graph facts directly): the LLM
extracts a single (subject, relation, object) claim from one free-text
sentence, and that claim is fed through the EXACT SAME evidence machinery
`m7_llm_fact_proposer_v0_1.py` already uses -- compared against a real
structural prediction from kernel replay, producing GROUNDED_ANALOGY
SUPPORT/CHALLENGE evidence via `acquire_cold_start()`. The LLM never
authors a new fact directly into the structural graph; it only ever
produces evidence about a prediction the kernel already made independently.
This keeps M2's founding invariant intact ("a derivation cannot be its own
evidence") without needing a new, weaker provenance tier or an
unverified-facts staging area -- both of which were considered and set
aside as unnecessary for this scope.

This is a small, deliberate extension of the existing fact-proposer: instead
of asking a closed question ("what is the object of RELATION(subject, ?)")
and eliciting only the object, the model is given an independently-authored
sentence and must extract the FULL triple itself. This introduces a new
failure mode `propose_relation_llm` didn't have -- the model can extract a
triple that doesn't match what the sentence is actually about (a subject or
relation belonging to a different candidate than the one under test). Fail
closed: any such mismatch is excluded, never silently paired with the wrong
prediction (see `m7_corpus_from_text_claims_v0_1.py`).

Also fail-closed on vocabulary: the model is given the CLOSED set of
relations already known from the structured corpus and instructed to answer
using exactly one of them, or an empty object if the sentence expresses none
of them. A response naming a relation outside that set is rejected as no
claim at all, never coerced into the closest-looking known relation.

Reuses `m7_llm_fact_proposer_v0_1.py`'s Ollama plumbing (local primary + LAN
sandbox fallback) unchanged -- no new network code, no new backend.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, Sequence

from m7_llm_fact_proposer_v0_1 import DEFAULT_MODEL, GenerateFn, ollama_generate_json_with_fallback


@dataclass(frozen=True)
class ParsedClaim:
    subject: str
    relation: str
    object: str
    model: str
    raw_response: str


def _build_extraction_prompt(text: str, allowed_relations: Sequence[str]) -> str:
    relations_block = ", ".join(sorted(allowed_relations))
    return (
        "Tu reçois une phrase en français qui décrit éventuellement une relation "
        "familiale entre deux personnes.\n\n"
        f'Phrase : "{text}"\n\n'
        f"Les seules relations connues sont : {relations_block}.\n\n"
        "Si la phrase affirme clairement une de ces relations entre un sujet et un "
        "objet, réponds avec UNIQUEMENT un objet JSON de la forme "
        '{"subject": "NomDuSujet", "relation": "UNE_DES_RELATIONS_CI-DESSUS", '
        '"object": "NomDeLObjet"}, en reprenant les noms propres exactement comme '
        "ils apparaissent dans la phrase et en choisissant la relation EXACTEMENT "
        "parmi celles listées ci-dessus (jamais une autre chaîne). Si la phrase "
        "n'exprime clairement aucune de ces relations, réponds par {}. Ne fournis "
        "aucune explication."
    )


def parse_claim_from_text(
    text: str,
    *,
    allowed_relations: Sequence[str],
    model: str = DEFAULT_MODEL,
    generate_fn: Optional[GenerateFn] = None,
) -> Optional[ParsedClaim]:
    """Extracts a (subject, relation, object) claim from one free-text
    sentence. Fails closed: any response that is not valid JSON, missing a
    required key, not a non-empty string, or naming a relation outside
    `allowed_relations` is treated as no claim at all, never fabricated or
    coerced into a nearby known relation.
    """
    allowed = set(allowed_relations)
    prompt = _build_extraction_prompt(text, allowed_relations)
    if generate_fn is not None:
        raw = generate_fn(prompt)
        model_used = model
    else:
        raw, model_used = ollama_generate_json_with_fallback(prompt, primary_model=model)

    if raw is None or not isinstance(raw, dict):
        return None

    subject = raw.get("subject")
    relation = raw.get("relation")
    obj = raw.get("object")
    if not isinstance(subject, str) or not subject.strip():
        return None
    if not isinstance(relation, str) or relation.strip() not in allowed:
        return None
    if not isinstance(obj, str) or not obj.strip():
        return None

    return ParsedClaim(
        subject=subject.strip(),
        relation=relation.strip(),
        object=obj.strip(),
        model=model_used,
        raw_response=json.dumps(raw),
    )


__all__ = ["ParsedClaim", "parse_claim_from_text"]
