"""MetaHIA M7 -- free-text claim parser, multi-model consensus v0.1.

Motivated directly by the 2026-09-18 mixed-corpus finding: the text-claim
parser's UNFILTERED evidence (single model, `llama3.2:latest`) degraded
holdout calibration enough to block promotion, despite showing genuine
outcome diversity (see `MetaHIA_M7_TextClaimParser_V0_1.md` Sec.10). This
tests whether requiring two INDEPENDENT models to agree exactly on the
extracted (subject, relation, object) triple -- rather than trusting a
single model's answer -- filters out the unreliable extractions and yields
a smaller but more reliable evidence set.

Design choice made explicitly before code (2026-09-18, over the two other
options presented): consensus among multiple MODELS on the SAME mechanism
(the text-claim parser specifically, chosen because it is the mechanism
whose unfiltered evidence just degraded calibration -- the most directly
motivated test), not consensus BETWEEN the two different M7 mechanisms
(witness vs. parser), and not both combined -- kept to a single new axis of
variation so a clean result is interpretable.

Two independent voters, ALWAYS BOTH contacted (this is NOT the
primary/fallback pattern from `ollama_generate_json_with_fallback`, which
only contacts the second host on unreachability of the first):

    voter A: local Ollama  (LOCAL_HOST, LOCAL_MODEL)
    voter B: LAN sandbox Ollama (LAN_FALLBACK_HOST, LAN_FALLBACK_MODEL)

Consensus rule: EXACT agreement on (subject, relation, object) required.
Never resolved by arbitrarily picking one voter, never fabricated: any of
the following yields "no consensus" --
    - either voter fails its OWN fail-closed contract
      (`parse_claim_from_text`'s malformed-output / closed-vocabulary
      rejection, unchanged and reused as-is);
    - both voters answer usably but disagree on any field.

Reuses `m7_text_claim_parser_v0_1.py`'s `parse_claim_from_text()` unchanged
(frozen -- its hash is pinned by
`MetaHIA_ThirdParty_Validation_Protocol_M7_TextClaimParser_V0_1.md`) as the
per-voter extraction step; this module only adds the agreement check on top.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from m7_llm_fact_proposer_v0_1 import (
    LAN_FALLBACK_HOST,
    LAN_FALLBACK_MODEL,
    LOCAL_HOST,
    LOCAL_MODEL,
    GenerateFn,
    ollama_generate_json,
)
from m7_text_claim_parser_v0_1 import parse_claim_from_text


@dataclass(frozen=True)
class ConsensusClaim:
    subject: str
    relation: str
    object: str
    models: Tuple[str, str]


REASON_AGREED = "AGREED"
REASON_VOTER_A_FAILED = "VOTER_A_FAILED"
REASON_VOTER_B_FAILED = "VOTER_B_FAILED"
REASON_BOTH_VOTERS_FAILED = "BOTH_VOTERS_FAILED"
REASON_DISAGREEMENT = "DISAGREEMENT"


@dataclass(frozen=True)
class ConsensusResult:
    """Always returned, whether or not consensus was reached -- so a caller
    can distinguish WHY no evidence resulted (a voter's own fail-closed
    rejection vs. a genuine disagreement between two usable answers) without
    any extra network calls, never by re-querying to diagnose after the
    fact."""

    claim: Optional[ConsensusClaim]
    reason: str


def _generate_via_host(host: str, model: str, timeout: float) -> GenerateFn:
    return lambda prompt: ollama_generate_json(prompt, model=model, host=host, timeout=timeout)


def parse_claim_from_text_with_consensus(
    text: str,
    *,
    allowed_relations: Sequence[str],
    voter_a_host: str = LOCAL_HOST,
    voter_a_model: str = LOCAL_MODEL,
    voter_b_host: str = LAN_FALLBACK_HOST,
    voter_b_model: str = LAN_FALLBACK_MODEL,
    voter_a_timeout: float = 30.0,
    voter_b_timeout: float = 90.0,
    generate_fn_a: Optional[GenerateFn] = None,
    generate_fn_b: Optional[GenerateFn] = None,
) -> ConsensusResult:
    """Calls two independent models on the IDENTICAL prompt and requires
    exact agreement before accepting. By default both voters make real
    network calls (never the primary/fallback pattern) -- `generate_fn_a`/
    `generate_fn_b` let tests inject deterministic voters exactly like
    every other M7 mechanism.
    """
    fn_a = generate_fn_a if generate_fn_a is not None else _generate_via_host(voter_a_host, voter_a_model, voter_a_timeout)
    fn_b = generate_fn_b if generate_fn_b is not None else _generate_via_host(voter_b_host, voter_b_model, voter_b_timeout)

    claim_a = parse_claim_from_text(text, allowed_relations=allowed_relations, model=voter_a_model, generate_fn=fn_a)
    claim_b = parse_claim_from_text(text, allowed_relations=allowed_relations, model=voter_b_model, generate_fn=fn_b)

    if claim_a is None and claim_b is None:
        return ConsensusResult(claim=None, reason=REASON_BOTH_VOTERS_FAILED)
    if claim_a is None:
        return ConsensusResult(claim=None, reason=REASON_VOTER_A_FAILED)
    if claim_b is None:
        return ConsensusResult(claim=None, reason=REASON_VOTER_B_FAILED)
    if (claim_a.subject, claim_a.relation, claim_a.object) != (claim_b.subject, claim_b.relation, claim_b.object):
        return ConsensusResult(claim=None, reason=REASON_DISAGREEMENT)
    return ConsensusResult(
        claim=ConsensusClaim(
            subject=claim_a.subject, relation=claim_a.relation, object=claim_a.object,
            models=(claim_a.model, claim_b.model),
        ),
        reason=REASON_AGREED,
    )


__all__ = [
    "ConsensusClaim",
    "ConsensusResult",
    "REASON_AGREED",
    "REASON_VOTER_A_FAILED",
    "REASON_VOTER_B_FAILED",
    "REASON_BOTH_VOTERS_FAILED",
    "REASON_DISAGREEMENT",
    "parse_claim_from_text_with_consensus",
]
