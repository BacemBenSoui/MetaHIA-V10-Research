"""Permanent invariant tests for M7 -- multi-hop LLM witness v0.1.

Uses an injected fake `generate_fn` throughout -- no network call. The
live-Ollama demonstration is a separate, explicitly-skippable test file
(test_m7_corpus_from_llm_multihop_live_demo_v0_1.py).
"""
from __future__ import annotations

from m7_llm_fact_proposer_multihop_v0_1 import _render_chain, propose_relation_llm_multihop

KNOWN_FACTS = [("MERE_DE", "Amanda", "David"), ("MERE_DE", "Amanda", "Alice")]
SKELETON = (("MERE_DE", "FORWARD"), ("MERE_DE", "FORWARD"))


def test_chain_rendering_produces_the_expected_relation_sequence():
    desc, final_var = _render_chain(SKELETON)
    assert desc == "MERE_DE(X0, X1); MERE_DE(X1, X2)"
    assert final_var == "X2"


def test_chain_rendering_handles_reverse_direction():
    desc, final_var = _render_chain((("PERE_DE", "REVERSE"), ("MERE_DE", "FORWARD")))
    assert desc == "PERE_DE(X1, X0); MERE_DE(X1, X2)"
    assert final_var == "X2"


def test_none_response_is_no_proposal():
    result = propose_relation_llm_multihop(
        known_facts=KNOWN_FACTS, subject="Duc", skeleton=SKELETON, generate_fn=lambda p: None
    )
    assert result is None


def test_malformed_responses_are_never_fabricated():
    for raw in ["not a dict", {}, {"object": 42}, {"object": "   "}]:
        result = propose_relation_llm_multihop(
            known_facts=KNOWN_FACTS, subject="Duc", skeleton=SKELETON, generate_fn=lambda p, r=raw: r
        )
        assert result is None


def test_well_formed_proposal_is_accepted_with_a_joined_relation_label():
    result = propose_relation_llm_multihop(
        known_facts=KNOWN_FACTS, subject="Duc", skeleton=SKELETON, generate_fn=lambda p: {"object": "Hoang"}
    )
    assert result.object == "Hoang"
    assert result.subject == "Duc"
    assert result.relation == "MERE_DE:FORWARD+MERE_DE:FORWARD"


def test_prompt_describes_the_chain_and_the_subject_never_the_answer():
    captured = {}

    def capturing(prompt):
        captured["prompt"] = prompt
        return {"object": "Hoang"}

    propose_relation_llm_multihop(known_facts=KNOWN_FACTS, subject="Duc", skeleton=SKELETON, generate_fn=capturing)
    assert "Duc" in captured["prompt"]
    assert "MERE_DE(X0, X1)" in captured["prompt"]
    assert "MERE_DE(X1, X2)" in captured["prompt"]
    assert "Hoang" not in captured["prompt"]  # the real answer must never appear in what the LLM is shown
