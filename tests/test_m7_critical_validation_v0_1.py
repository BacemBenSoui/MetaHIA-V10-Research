"""M7 (Empirical LLM Loop, fact-proposer scope + mixed-corpus promotion
integration) -- Critical Validation v0.1.

Third-party validation suite for
MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md. Cases C01-C09 map 1:1 to
that protocol's critical contract. Self-contained: does not import from the
other M7 test files, does not modify any frozen module.

Deliberately network-free: every case uses an injected fake `generate_fn`,
never a real Ollama call, so this suite runs identically whether or not the
evaluator has Ollama installed -- matching the portability discipline already
established for the M6 protocols (no external service required to pass the
mandatory critical suite). The real, non-reproducible live-LLM numbers
(16/16 CONTRADICTED, mixed holdout Brier=0.47) are reported as
already-disclosed empirical findings in the protocol document, not asserted
here.
"""
from __future__ import annotations

from m4_cold_start_evidence_v0_1 import CHALLENGE, GROUNDED_ANALOGY, GROUNDED_DIRECT, SUPPORT, UNGROUNDED_HUMAN
from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m7_corpus_mixed_v0_1 import build_mixed_corpus, compare_calibration_with_and_without_llm_evidence
from m7_llm_fact_proposer_v0_1 import (
    LLMProposal,
    OllamaUnavailable,
    llm_evidence_for_prediction,
    ollama_generate_json_with_fallback,
    propose_relation_llm,
)

KNOWN_FACTS = [("MERE_DE", "Amanda", "David"), ("MERE_DE", "Amanda", "Alice")]


# ---------------------------------------------------------------------------
# C01 -- The real predicted value is never leaked into the prompt sent to the LLM.
# ---------------------------------------------------------------------------

def test_c01_predicted_object_never_appears_in_the_prompt():
    captured = {}

    def capturing_generator(prompt):
        captured["prompt"] = prompt
        return {"object": "Hugo"}

    propose_relation_llm(
        known_facts=KNOWN_FACTS, subject="Alice", relation="MERE_DE", generate_fn=capturing_generator
    )
    assert "Hugo" not in captured["prompt"]


# ---------------------------------------------------------------------------
# C02 -- Fail-closed parsing: malformed LLM output is always "no proposal",
# never fabricated into one.
# ---------------------------------------------------------------------------

def test_c02_malformed_responses_are_never_fabricated_into_a_proposal():
    malformed = [None, "not a dict", {"something_else": "Y"}, {"object": 42}, {"object": "   "}]
    for raw in malformed:
        result = propose_relation_llm(
            known_facts=KNOWN_FACTS, subject="X", relation="MERE_DE", generate_fn=lambda p, r=raw: r
        )
        assert result is None, f"malformed response {raw!r} must yield no proposal"


# ---------------------------------------------------------------------------
# C03 -- Evidence classification is always GROUNDED_ANALOGY, never
# GROUNDED_DIRECT/UNGROUNDED_HUMAN; agreement -> SUPPORT, disagreement -> CHALLENGE.
# ---------------------------------------------------------------------------

def test_c03_evidence_is_always_grounded_analogy_and_polarity_reflects_agreement():
    agreeing = LLMProposal(relation="MERE_DE", subject="Alice", object="Hugo", model="m", raw_response="{}")
    ev_agree = llm_evidence_for_prediction(agreeing, candidate_id="c1", predicted_object="Hugo", evidence_index=0)
    assert ev_agree.provenance == GROUNDED_ANALOGY
    assert ev_agree.provenance not in (GROUNDED_DIRECT, UNGROUNDED_HUMAN)
    assert ev_agree.polarity == SUPPORT

    disagreeing = LLMProposal(relation="MERE_DE", subject="Alice", object="Other", model="m", raw_response="{}")
    ev_disagree = llm_evidence_for_prediction(disagreeing, candidate_id="c1", predicted_object="Hugo", evidence_index=0)
    assert ev_disagree.provenance == GROUNDED_ANALOGY
    assert ev_disagree.polarity == CHALLENGE


# ---------------------------------------------------------------------------
# C04 -- LAN fallback triggers ONLY on genuine primary unreachability, never
# merely on a reachable-but-unusable response.
# ---------------------------------------------------------------------------

def test_c04_fallback_triggers_only_on_genuine_unreachability(monkeypatch):
    import m7_llm_fact_proposer_v0_1 as m7

    calls = []

    def unreachable_then_ok(prompt, *, model, host, timeout):
        calls.append(host)
        if host == "primary-host":
            raise OllamaUnavailable("simulated down")
        return {"object": "from-fallback"}

    monkeypatch.setattr(m7, "ollama_generate_json", unreachable_then_ok)
    response, model_used = ollama_generate_json_with_fallback(
        "prompt", primary_host="primary-host", fallback_host="fallback-host",
        primary_model="primary-model", fallback_model="fallback-model",
    )
    assert response == {"object": "from-fallback"}
    assert model_used == "fallback-model"
    assert calls == ["primary-host", "fallback-host"]

    calls.clear()

    def reachable_but_unusable(prompt, *, model, host, timeout):
        calls.append(host)
        return None

    monkeypatch.setattr(m7, "ollama_generate_json", reachable_but_unusable)
    response, model_used = ollama_generate_json_with_fallback(
        "prompt", primary_host="primary-host", fallback_host="fallback-host",
        primary_model="primary-model", fallback_model="fallback-model",
    )
    assert response is None
    assert model_used == "primary-model"
    assert calls == ["primary-host"]  # fallback host never contacted


# ---------------------------------------------------------------------------
# C05 -- The proposal's model field always names whichever backend actually
# answered, never the primary model merely requested.
# ---------------------------------------------------------------------------

def test_c05_proposal_model_names_whichever_backend_actually_answered(monkeypatch):
    import m7_llm_fact_proposer_v0_1 as m7

    def fake_generate(prompt, *, model, host, timeout):
        if host == m7.LOCAL_HOST:
            raise OllamaUnavailable("simulated local down")
        return {"object": "Hugo"}

    monkeypatch.setattr(m7, "ollama_generate_json", fake_generate)
    result = propose_relation_llm(known_facts=KNOWN_FACTS, subject="Alice", relation="MERE_DE")
    assert result.model == m7.LAN_FALLBACK_MODEL
    assert result.model != m7.LOCAL_MODEL


# ---------------------------------------------------------------------------
# C06 -- Mixed-corpus fairness: the LLM mechanism can only add records for
# rule signatures ALREADY present in the adversarial corpus, never a new one.
# ---------------------------------------------------------------------------

def test_c06_llm_evidence_never_introduces_a_rule_absent_from_the_adversarial_corpus():
    report = build_mixed_corpus(generate_fn=lambda p: {"object": "Placeholder"})
    adversarial_rules = {r.rule_signature for r in report.adversarial_records}
    combined_rules = {r.rule_signature for r in report.combined_records}
    assert combined_rules == adversarial_rules


# ---------------------------------------------------------------------------
# C07 -- No hidden transformation: zero LLM evidence must leave the mixed
# comparison numerically IDENTICAL to the adversarial-only baseline.
# ---------------------------------------------------------------------------

def test_c07_zero_llm_evidence_yields_numerically_identical_comparison():
    report = build_mixed_corpus(generate_fn=lambda p: None)
    comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)
    assert comparison.mixed_holdout_brier == comparison.baseline_holdout_brier
    assert comparison.mixed_holdout_ece == comparison.baseline_holdout_ece
    assert comparison.mixed_train_size == comparison.baseline_train_size
    assert comparison.mixed_holdout_size == comparison.baseline_holdout_size


# ---------------------------------------------------------------------------
# C08 -- The mixed-corpus module does not silently alter the already-validated
# M6 v0.2 adversarial mechanism: same baseline Brier as its own frozen test.
# ---------------------------------------------------------------------------

def test_c08_baseline_reproduces_the_already_validated_m6_v0_2_number():
    report = build_mixed_corpus(generate_fn=lambda p: None)
    comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)
    assert comparison.baseline_holdout_brier == 0.48125
    direct = build_real_corpus_v2()
    assert [r.record_id for r in direct.records] == [r.record_id for r in report.adversarial_records]


# ---------------------------------------------------------------------------
# C09 -- Honest accounting: every length-1 candidate pattern the LLM mechanism
# considers either yields a record or is explicitly excluded -- never neither.
# ---------------------------------------------------------------------------

def test_c09_every_llm_candidate_is_accounted_for_never_silently_dropped():
    from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus

    report = build_llm_witnessed_corpus(generate_fn=lambda p: {"object": "Placeholder"})
    patterns_with_records = {r.record_id[len("llmv1::"):].rsplit("::", 1)[0] for r in report.records}
    excluded_patterns = {msg.split(": ", 1)[0] for msg in report.excluded_no_llm_proposal}
    assert patterns_with_records.isdisjoint(excluded_patterns)
    assert len(patterns_with_records) + len(excluded_patterns) == report.candidate_patterns_considered
