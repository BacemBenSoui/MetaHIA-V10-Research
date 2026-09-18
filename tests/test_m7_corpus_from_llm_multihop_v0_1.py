"""Permanent invariant tests for M7 -- multi-hop witness corpus builder v0.1.

Uses an injected fake `generate_fn` throughout -- no network call. The
live-Ollama demonstration is a separate, explicitly-skippable test file
(test_m7_corpus_from_llm_multihop_live_demo_v0_1.py).
"""
from __future__ import annotations

from m4_cold_start_evidence_v0_1 import CONTRADICTED
from m7_corpus_from_llm_multihop_v0_1 import build_llm_witnessed_multihop_corpus


def test_candidate_patterns_considered_matches_m6_v0_2s_own_length_2_count():
    """m6_corpus_from_m4_m5_v0_2.py's own critical test asserts 69 total
    candidates (14 length-1 + this module's length>=2 territory) -- so this
    module must consider exactly 69 - 14 = 55 patterns, the same corpus,
    same discovery, same scoping."""
    report = build_llm_witnessed_multihop_corpus(generate_fn=lambda p: None)
    assert report.candidate_patterns_considered == 55


def test_non_answering_model_yields_zero_records_all_excluded():
    report = build_llm_witnessed_multihop_corpus(generate_fn=lambda p: None)
    assert report.records == ()
    assert len(report.excluded_no_llm_proposal) == 55


def test_a_consistently_wrong_answer_yields_only_contradicted_never_supported():
    """Wiring check: a fake that always proposes the same wrong placeholder
    (never able to coincidentally match a real predicted_end) must produce
    real REPLAYED-backed records that are ALL CONTRADICTED -- confirms the
    outcome is computed from a genuine comparison to the real kernel
    prediction, not fabricated or defaulted to SUPPORTED."""
    report = build_llm_witnessed_multihop_corpus(generate_fn=lambda p: {"object": "GuaranteedWrongPlaceholder_XYZ"})
    assert len(report.records) > 0
    assert all(r.outcome == CONTRADICTED for r in report.records)
    assert all(r.depth >= 2 for r in report.records)


def test_records_are_all_grounded_analogy():
    from m4_cold_start_evidence_v0_1 import GROUNDED_ANALOGY

    report = build_llm_witnessed_multihop_corpus(generate_fn=lambda p: {"object": "GuaranteedWrongPlaceholder_XYZ"})
    assert all(r.provenance == GROUNDED_ANALOGY for r in report.records)
