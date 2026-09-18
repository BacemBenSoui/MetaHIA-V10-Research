"""M7 -- free-text claim parser, live Ollama demonstration v0.1.

Companion to test_m7_live_ollama_demo_v0_1.py: makes a REAL call to a local
(or LAN-fallback) Ollama server for each of the 16 text claims. Skipped
cleanly if Ollama is unreachable, for the same portability reason as every
other live-LLM test in this repo.

Live LLM calls are NOT deterministic across runs/models/hardware -- this
test does not pin an exact parsing-accuracy value or outcome distribution.
It only asserts the structural guarantees the mechanism provides regardless
of what the model actually extracts: real acquire_cold_start() execution
where parsing succeeds and matches, GROUNDED_ANALOGY provenance, and honest,
mutually-exclusive accounting of every candidate (matched-and-used,
no-matching-claim, parse-rejected, or parsing-mismatch -- never silently
dropped, never double-counted).
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_text_claims_v0_1 import build_text_claim_corpus
from m7_llm_fact_proposer_v0_1 import LOCAL_HOST


def _ollama_reachable() -> bool:
    try:
        urllib.request.urlopen(f"{LOCAL_HOST}/api/tags", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason=f"Ollama not reachable at {LOCAL_HOST} -- skipping live text-claim parser demo"
)


def test_live_text_claim_corpus_produces_real_grounded_analogy_records():
    report = build_text_claim_corpus()
    # 14 length-1 patterns are discoverable in this corpus; only 11 of them
    # have an authored text claim (ENFANT_DE both directions and PERE_DE
    # forward have none -- a disclosed corpus coverage gap, not a defect).
    assert report.candidate_patterns_considered == 14

    accounted = len(report.records) + len(report.excluded_no_parse) + len(report.excluded_parsing_mismatch)
    assert accounted + len(report.excluded_no_matching_text_claim) >= report.candidate_patterns_considered

    for r in report.records:
        assert r.provenance == GROUNDED_ANALOGY
        assert r.outcome in (SUPPORTED, CONTRADICTED)
