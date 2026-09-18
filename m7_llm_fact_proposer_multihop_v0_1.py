"""MetaHIA M7 -- LLM fact proposer, multi-hop extension v0.1.

Extends the closed-question witness (`m7_llm_fact_proposer_v0_1.py`, frozen
-- its hash is pinned by `MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md`,
not touched here) to patterns of length > 1, mirroring the design M6 v0.2
already solved for its adversarial corpus (`m6_corpus_from_m4_m5_v0_2.py`):
a candidate is no longer a single relation but a SKELETON -- an ordered
chain of (operator, direction) steps starting from `subject` -- and the LLM
is asked to determine the final value at the end of that chain, never told
the real predicted value.

Reuses the frozen module's `LLMProposal` dataclass and
`ollama_generate_json_with_fallback` (local primary, LAN sandbox fallback)
unchanged -- this file only adds a new prompt shape and a new elicitation
function for the multi-hop case; it does not duplicate any network logic.

Chain description example (skeleton = ((MERE_DE, FORWARD), (MERE_DE,
FORWARD)), subject = "Duc"): the LLM is told "starting from X0 = Duc:
MERE_DE(X0, X1); MERE_DE(X1, X2). Determine X2." -- structurally identical
to what `kernel2.replay_path_pattern_holdout` computes by real graph
traversal, described in prose instead of leaked as an answer.
"""
from __future__ import annotations

import json
from typing import Optional, Sequence, Tuple

from m7_llm_fact_proposer_v0_1 import DEFAULT_MODEL, GenerateFn, LLMProposal, ollama_generate_json_with_fallback

Skeleton = Sequence[Tuple[str, str]]  # ((operator_ref_id, "FORWARD"|"REVERSE"), ...)


def _render_chain(skeleton: Skeleton) -> Tuple[str, str]:
    """Returns (chain description, final variable name)."""
    steps = []
    var = "X0"
    for i, (operator, direction) in enumerate(skeleton):
        next_var = f"X{i + 1}"
        if direction == "FORWARD":
            steps.append(f"{operator}({var}, {next_var})")
        else:
            steps.append(f"{operator}({next_var}, {var})")
        var = next_var
    return "; ".join(steps), var


def _build_multihop_prompt(known_facts: Sequence[Tuple[str, str, str]], subject: str, skeleton: Skeleton) -> str:
    facts_block = "\n".join(f"{rel}({subj}, {obj})" for rel, subj, obj in known_facts)
    chain_desc, final_var = _render_chain(skeleton)
    return (
        "You are given family facts as triples RELATION(subject, object):\n"
        f"{facts_block}\n\n"
        f'By analogy with the patterns above, consider the following chain of relations, '
        f'starting from X0 = "{subject}":\n{chain_desc}.\n\n'
        f'Determine the single most plausible value of {final_var} at the end of this chain.\n\n'
        'Answer with ONLY a JSON object like {"object": "SomeName"} and nothing else. Do not '
        "explain your reasoning."
    )


def propose_relation_llm_multihop(
    *,
    known_facts: Sequence[Tuple[str, str, str]],
    subject: str,
    skeleton: Skeleton,
    model: str = DEFAULT_MODEL,
    generate_fn: Optional[GenerateFn] = None,
) -> Optional[LLMProposal]:
    """Multi-hop counterpart of `propose_relation_llm` -- same fail-closed
    contract (any non-JSON, missing-key, non-string, or empty response is
    "no proposal", never fabricated), same non-leakage guarantee (the real
    predicted value is never included in the prompt), same default backend
    (local Ollama with LAN sandbox fallback). `LLMProposal.relation` is set
    to a joined representation of the skeleton (e.g. "MERE_DE+MERE_DE") for
    traceability -- it is documentation only, never parsed back.
    """
    prompt = _build_multihop_prompt(known_facts, subject, skeleton)
    if generate_fn is not None:
        raw = generate_fn(prompt)
        model_used = model
    else:
        raw, model_used = ollama_generate_json_with_fallback(prompt, primary_model=model)

    if raw is None or not isinstance(raw, dict):
        return None
    proposed_object = raw.get("object")
    if not isinstance(proposed_object, str) or not proposed_object.strip():
        return None

    relation_label = "+".join(f"{op}:{direction}" for op, direction in skeleton)
    return LLMProposal(
        relation=relation_label,
        subject=subject,
        object=proposed_object.strip(),
        model=model_used,
        raw_response=json.dumps(raw),
    )


__all__ = ["Skeleton", "propose_relation_llm_multihop"]
