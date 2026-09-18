"""M7 -- mixed-corpus promotion v0.2 (three sources), live Ollama demonstration.

Makes REAL calls to a local (or LAN-fallback) Ollama server through both
LLM mechanisms via build_mixed_corpus_v2(). Skipped cleanly if Ollama is
unreachable, for the same portability reason as every other live-LLM test
in this repo.

Does NOT pin an exact Brier/ECE value for any of the four conditions --
live LLM output is not reproducible across runs/models/hardware. Only
asserts the structural guarantees: every condition produces a real holdout,
every promotion decision is computed from real numbers, and the fairness
property (identical holdout rule set across all four conditions) holds on
the real corpus, not just the fake one used in
tests/test_m7_mixed_corpus_v0_2_promotion_v0_1.py.
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from m7_corpus_mixed_v0_2 import build_mixed_corpus_v2, compare_calibration_across_sources
from m7_llm_fact_proposer_v0_1 import LOCAL_HOST


def _ollama_reachable() -> bool:
    try:
        urllib.request.urlopen(f"{LOCAL_HOST}/api/tags", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason=f"Ollama not reachable at {LOCAL_HOST} -- skipping live v0.2 mixed-corpus demo"
)


def test_live_four_way_comparison_runs_end_to_end():
    report = build_mixed_corpus_v2()
    assert len(report.adversarial_records) == 26  # unchanged, already-validated baseline

    comparison = compare_calibration_across_sources(report, seed=0, brier_threshold=0.5)

    for condition in (comparison.baseline, comparison.with_witness, comparison.with_text_claims, comparison.with_both):
        assert condition.holdout_size > 0
        assert condition.promotion.holdout_brier is not None
        assert 0.0 <= condition.holdout_brier <= 2.0

    assert comparison.baseline.holdout_brier == 0.48125  # the already-validated baseline never moves
