"""Permanent invariant tests for M7 -- LLM Fact Proposer v0.1.

Uses an injected fake `generate_fn` throughout -- no network call, no
dependency on a running Ollama instance, so these run deterministically in
any environment (including a genuinely external reviewer's, who will almost
certainly not have this machine's local Ollama server). The live-Ollama
demonstration is a separate, explicitly-skippable test file
(test_m7_live_ollama_demo_v0_1.py).
"""
from __future__ import annotations

from m4_cold_start_evidence_v0_1 import CHALLENGE, GROUNDED_ANALOGY, GROUNDED_DIRECT, SUPPORT, UNGROUNDED_HUMAN
import pytest

import m7_llm_fact_proposer_v0_1 as m7
from m7_llm_fact_proposer_v0_1 import (
    LLMProposal,
    OllamaUnavailable,
    llm_evidence_for_prediction,
    ollama_generate_json,
    ollama_generate_json_with_fallback,
    propose_relation_llm,
)

KNOWN_FACTS = [("MERE_DE", "Amanda", "David"), ("MERE_DE", "Amanda", "Alice")]


def _fake_generator(response):
    return lambda prompt: response


# ---------------------------------------------------------------------------
# 1. The real predicted value is never leaked into the prompt.
# ---------------------------------------------------------------------------

def test_predicted_object_is_never_present_in_the_prompt():
    """Regression guard for the exact bug found 2026-09-17: an earlier
    version of this prompt put the real predicted object directly in the
    instruction and the JSON example, making agreement trivial rather than a
    genuine independent check."""
    captured = {}

    def capturing_generator(prompt):
        captured["prompt"] = prompt
        return {"object": "Hugo"}

    propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="Alice", relation="MERE_DE",
        generate_fn=capturing_generator,
    )
    assert "Hugo" not in captured["prompt"]  # the real answer must never appear in what the LLM is shown


# ---------------------------------------------------------------------------
# 2. Fail-closed parsing: malformed LLM output is "no proposal", never fabricated.
# ---------------------------------------------------------------------------

def test_none_response_is_no_proposal():
    result = propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="X", relation="MERE_DE",
        generate_fn=_fake_generator(None),
    )
    assert result is None


def test_non_dict_response_is_no_proposal():
    result = propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="X", relation="MERE_DE",
        generate_fn=lambda prompt: "not a dict",
    )
    assert result is None


def test_missing_object_key_is_no_proposal():
    result = propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="X", relation="MERE_DE",
        generate_fn=_fake_generator({"something_else": "Y"}),
    )
    assert result is None


def test_non_string_object_is_no_proposal():
    result = propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="X", relation="MERE_DE",
        generate_fn=_fake_generator({"object": 42}),
    )
    assert result is None


def test_empty_string_object_is_no_proposal():
    result = propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="X", relation="MERE_DE",
        generate_fn=_fake_generator({"object": "   "}),
    )
    assert result is None


# ---------------------------------------------------------------------------
# 3. A well-formed proposal IS accepted, with subject/relation taken from the
#    caller (known context), only object genuinely elicited from the LLM.
# ---------------------------------------------------------------------------

def test_well_formed_proposal_is_accepted():
    result = propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="David", relation="FRERE_DE",
        generate_fn=_fake_generator({"object": "Alice"}),
    )
    assert result == LLMProposal(relation="FRERE_DE", subject="David", object="Alice", model="llama3.2:latest", raw_response=result.raw_response)


# ---------------------------------------------------------------------------
# 4. Evidence classification: always GROUNDED_ANALOGY, never GROUNDED_DIRECT
#    or UNGROUNDED_HUMAN. Agreement -> SUPPORT, disagreement -> CHALLENGE.
# ---------------------------------------------------------------------------

def test_agreeing_proposal_yields_support_grounded_analogy():
    proposal = LLMProposal(relation="MERE_DE", subject="Alice", object="Hugo", model="m", raw_response="{}")
    evidence = llm_evidence_for_prediction(proposal, candidate_id="c1", predicted_object="Hugo", evidence_index=0)
    assert evidence.polarity == SUPPORT
    assert evidence.provenance == GROUNDED_ANALOGY
    assert evidence.provenance != GROUNDED_DIRECT
    assert evidence.provenance != UNGROUNDED_HUMAN


def test_disagreeing_proposal_yields_challenge_grounded_analogy():
    proposal = LLMProposal(relation="MERE_DE", subject="Alice", object="SomeoneElse", model="m", raw_response="{}")
    evidence = llm_evidence_for_prediction(proposal, candidate_id="c1", predicted_object="Hugo", evidence_index=0)
    assert evidence.polarity == CHALLENGE
    assert evidence.provenance == GROUNDED_ANALOGY


def test_evidence_source_id_identifies_the_model_not_a_human():
    proposal = LLMProposal(relation="MERE_DE", subject="Alice", object="Hugo", model="llama3.2:latest", raw_response="{}")
    evidence = llm_evidence_for_prediction(proposal, candidate_id="c1", predicted_object="Hugo", evidence_index=0)
    assert evidence.source_id == "llm::llama3.2:latest"
    assert evidence.kind != "HUMAN"


# ---------------------------------------------------------------------------
# 5. An unreachable Ollama host raises OllamaUnavailable, distinct from a
#    reachable server giving an unusable response (which is "no proposal").
# ---------------------------------------------------------------------------

def test_unreachable_host_raises_ollama_unavailable():
    with pytest.raises(OllamaUnavailable):
        ollama_generate_json("test", host="http://localhost:1", timeout=2)


# ---------------------------------------------------------------------------
# 6. LAN sandbox fallback (192.168.1.11): triggers ONLY on genuine primary
#    unreachability, never merely on an unusable-but-reachable response.
#    Deterministic via monkeypatching the underlying single-host call --
#    no real network dependency in this file.
# ---------------------------------------------------------------------------

def test_fallback_is_used_when_primary_is_unreachable(monkeypatch):
    calls = []

    def fake_generate(prompt, *, model, host, timeout):
        calls.append(host)
        if host == "primary-host":
            raise OllamaUnavailable("simulated primary down")
        return {"object": "from-fallback"}

    monkeypatch.setattr(m7, "ollama_generate_json", fake_generate)
    response, model_used = ollama_generate_json_with_fallback(
        "prompt", primary_host="primary-host", fallback_host="fallback-host",
        primary_model="primary-model", fallback_model="fallback-model",
    )
    assert response == {"object": "from-fallback"}
    assert model_used == "fallback-model"  # correctly attributed to whichever backend actually answered
    assert calls == ["primary-host", "fallback-host"]


def test_fallback_is_not_used_when_primary_succeeds():
    def fake_generate(prompt, *, model, host, timeout):
        return {"object": "from-primary" if host == "primary-host" else "from-fallback"}

    m7_original = m7.ollama_generate_json
    m7.ollama_generate_json = fake_generate
    try:
        response, model_used = ollama_generate_json_with_fallback(
            "prompt", primary_host="primary-host", fallback_host="fallback-host",
            primary_model="primary-model", fallback_model="fallback-model",
        )
    finally:
        m7.ollama_generate_json = m7_original
    assert response == {"object": "from-primary"}
    assert model_used == "primary-model"


def test_fallback_is_not_used_when_primary_is_reachable_but_unusable(monkeypatch):
    """A reachable primary that returns an unusable response (None) is "no
    proposal" from that model -- must NOT trigger asking a different model
    on the fallback host, which would make the result depend on which
    backend happened to answer rather than on one consistent witness."""
    calls = []

    def fake_generate(prompt, *, model, host, timeout):
        calls.append(host)
        return None

    monkeypatch.setattr(m7, "ollama_generate_json", fake_generate)
    response, model_used = ollama_generate_json_with_fallback(
        "prompt", primary_host="primary-host", fallback_host="fallback-host",
        primary_model="primary-model", fallback_model="fallback-model",
    )
    assert response is None
    assert model_used == "primary-model"  # still correctly attributed even though the response was unusable
    assert calls == ["primary-host"]  # fallback never called


def test_both_primary_and_fallback_unreachable_propagates():
    def fake_generate(prompt, *, model, host, timeout):
        raise OllamaUnavailable(f"simulated {host} down")

    m7_original = m7.ollama_generate_json
    m7.ollama_generate_json = fake_generate
    try:
        with pytest.raises(OllamaUnavailable):
            ollama_generate_json_with_fallback(
                "prompt", primary_host="primary-host", fallback_host="fallback-host"
            )
    finally:
        m7.ollama_generate_json = m7_original


def test_fallback_defaults_point_at_the_lan_sandbox_server():
    assert m7.LAN_FALLBACK_HOST == "http://192.168.1.11:11434"
    assert m7.LOCAL_HOST == "http://localhost:11434"


def test_propose_relation_llm_attributes_fallback_answer_to_the_correct_model(monkeypatch):
    """Integration-level regression guard for the exact bug found 2026-09-17
    running the real fallback end to end: with the primary down, the
    resulting LLMProposal.model must name the model that actually answered
    (the LAN fallback), never the primary model that was merely requested
    but never responded."""
    def fake_generate(prompt, *, model, host, timeout):
        if host == m7.LOCAL_HOST:
            raise OllamaUnavailable("simulated local down")
        return {"object": "Hugo"}

    monkeypatch.setattr(m7, "ollama_generate_json", fake_generate)
    result = propose_relation_llm(known_facts=KNOWN_FACTS, subject="Alice", relation="MERE_DE")
    assert result.object == "Hugo"
    assert result.model == m7.LAN_FALLBACK_MODEL
    assert result.model != m7.LOCAL_MODEL
