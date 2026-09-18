"""MetaHIA M7 -- cross-mechanism consensus (closed-question witness + free-
text claim parser) v0.1.

Chosen explicitly (2026-09-18) as the remaining, untested consensus axis
after same-mechanism consensus (two models on the SAME question) was tested
and refuted -- it made calibration worse, not better (see
`m7_text_claim_parser_consensus_v0_1.py` and
`MetaHIA_M7_TextClaimParser_V0_1.md` Sec.11). This tests a structurally
different kind of agreement: not two models answering the identical closed
question, but two DIFFERENT mechanisms (a closed-question witness and a
free-text sentence parser) independently reaching the same conclusion about
the same candidate -- via different information (the witness sees only the
subject/relation, disclosed in `known_facts` context; the parser sees an
independently-authored sentence, never told the subject/relation in
advance) and different elicitation formats.

Each mechanism's own real default backend is reused unchanged (local Ollama
primary, LAN sandbox fallback only on genuine unreachability) -- this is
NOT the same-mechanism consensus's "always contact both hosts" pattern; in
the normal case (local reachable) both calls stay local, a materially
different resource profile worth measuring (see
scripts/print_cross_mechanism_consensus_results_v0_1.py).

Six honestly distinct outcomes, mirroring the granularity already
established for same-mechanism consensus:

    AGREED             -- both mechanisms produced a well-formed answer,
                           the parser's answer matches what the sentence is
                           independently known to be about, and both
                           mechanisms named the SAME object.
    WITNESS_FAILED      -- the witness produced no usable proposal.
    PARSER_FAILED       -- the parser produced no usable extraction.
    BOTH_FAILED         -- neither produced anything usable.
    PARSER_MISMATCH     -- the parser extracted a well-formed claim, but not
                           about the subject/relation this sentence is
                           independently known to be about (same fidelity
                           check as the single-mechanism parser).
    DISAGREEMENT        -- both mechanisms answered usably (and the parser's
                           extraction was faithful to its sentence), but
                           they named DIFFERENT objects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from m7_llm_fact_proposer_v0_1 import DEFAULT_MODEL, GenerateFn, propose_relation_llm
from m7_text_claim_parser_v0_1 import parse_claim_from_text

REASON_AGREED = "AGREED"
REASON_WITNESS_FAILED = "WITNESS_FAILED"
REASON_PARSER_FAILED = "PARSER_FAILED"
REASON_BOTH_FAILED = "BOTH_FAILED"
REASON_PARSER_MISMATCH = "PARSER_MISMATCH"
REASON_DISAGREEMENT = "DISAGREEMENT"


@dataclass(frozen=True)
class CrossMechanismClaim:
    subject: str
    relation: str
    object: str
    witness_model: str
    parser_model: str


@dataclass(frozen=True)
class CrossMechanismResult:
    claim: Optional[CrossMechanismClaim]
    reason: str


def evaluate_cross_mechanism_consensus(
    *,
    known_facts: Sequence[Tuple[str, str, str]],
    subject: str,
    relation: str,
    text: str,
    allowed_relations: Sequence[str],
    witness_model: str = DEFAULT_MODEL,
    parser_model: str = DEFAULT_MODEL,
    witness_generate_fn: Optional[GenerateFn] = None,
    parser_generate_fn: Optional[GenerateFn] = None,
) -> CrossMechanismResult:
    """Runs the witness (closed question about `subject`/`relation`) and the
    parser (free extraction from `text`) independently and requires exact
    agreement on the object. Never resolved by arbitrarily trusting one
    mechanism over the other."""
    witness = propose_relation_llm(
        known_facts=known_facts, subject=subject, relation=relation,
        model=witness_model, generate_fn=witness_generate_fn,
    )
    parsed = parse_claim_from_text(
        text, allowed_relations=allowed_relations, model=parser_model, generate_fn=parser_generate_fn,
    )

    if witness is None and parsed is None:
        return CrossMechanismResult(claim=None, reason=REASON_BOTH_FAILED)
    if witness is None:
        return CrossMechanismResult(claim=None, reason=REASON_WITNESS_FAILED)
    if parsed is None:
        return CrossMechanismResult(claim=None, reason=REASON_PARSER_FAILED)
    if parsed.subject != subject or parsed.relation != relation:
        return CrossMechanismResult(claim=None, reason=REASON_PARSER_MISMATCH)
    if witness.object != parsed.object:
        return CrossMechanismResult(claim=None, reason=REASON_DISAGREEMENT)

    return CrossMechanismResult(
        claim=CrossMechanismClaim(
            subject=subject, relation=relation, object=witness.object,
            witness_model=witness.model, parser_model=parsed.model,
        ),
        reason=REASON_AGREED,
    )


__all__ = [
    "CrossMechanismClaim",
    "CrossMechanismResult",
    "REASON_AGREED",
    "REASON_WITNESS_FAILED",
    "REASON_PARSER_FAILED",
    "REASON_BOTH_FAILED",
    "REASON_PARSER_MISMATCH",
    "REASON_DISAGREEMENT",
    "evaluate_cross_mechanism_consensus",
]
