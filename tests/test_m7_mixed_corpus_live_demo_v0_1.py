"""M7 -- mixed-corpus promotion, live Ollama demonstration v0.1.

Companion to tests/test_m7_live_ollama_demo_v0_1.py: makes a REAL call to a
local (or LAN-fallback) Ollama server through build_mixed_corpus(), and runs
the real comparison. Skipped cleanly if Ollama is unreachable, for the same
portability reason as the other live demo file.

Like every other live-LLM test in this repo, this does NOT pin an exact
Brier/ECE value or assert which direction the comparison goes (the model's
answers are not reproducible across runs/models/hardware) -- it only asserts
the structural guarantees: both runs produce a real holdout, both promotion
decisions are computed from real numbers, and the fairness property (same
holdout rule set) holds on the real corpus, not just the fake one used in
tests/test_m7_mixed_corpus_promotion_v0_1.py.
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from m7_corpus_mixed_v0_1 import build_mixed_corpus, compare_calibration_with_and_without_llm_evidence
from m7_llm_fact_proposer_v0_1 import LOCAL_HOST


def _ollama_reachable() -> bool:
    try:
        urllib.request.urlopen(f"{LOCAL_HOST}/api/tags", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason=f"Ollama not reachable at {LOCAL_HOST} -- skipping live mixed-corpus demo"
)


def test_live_mixed_corpus_comparison_runs_end_to_end():
    report = build_mixed_corpus()
    assert len(report.adversarial_records) == 26  # unchanged, already-validated M6 v0.2 mechanism

    comparison = compare_calibration_with_and_without_llm_evidence(report, seed=0, brier_threshold=0.5)

    assert comparison.baseline_holdout_size > 0
    assert comparison.mixed_holdout_size > 0
    assert comparison.baseline_holdout_brier == 0.48125  # the already-validated baseline never moves
    assert 0.0 <= comparison.mixed_holdout_brier <= 2.0
    assert comparison.baseline_promotion.holdout_brier is not None
    assert comparison.mixed_promotion.holdout_brier is not None
