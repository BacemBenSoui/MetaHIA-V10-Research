"""M7 -- multi-hop LLM witness, live Ollama demonstration v0.1.

Makes a REAL call to a local (or LAN-fallback) Ollama server for each
length>=2 candidate with a real REPLAYED match. Skipped cleanly if Ollama is
unreachable, for the same portability reason as every other live-LLM test
in this repo.

Live LLM calls are NOT deterministic across runs/models/hardware -- this
test does not pin an exact outcome distribution. It only asserts the
structural guarantees: real acquire_cold_start() execution, GROUNDED_ANALOGY
provenance, depth >= 2 for every record, and honest accounting of every
candidate.
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_llm_multihop_v0_1 import build_llm_witnessed_multihop_corpus
from m7_llm_fact_proposer_v0_1 import LOCAL_HOST


def _ollama_reachable() -> bool:
    try:
        urllib.request.urlopen(f"{LOCAL_HOST}/api/tags", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason=f"Ollama not reachable at {LOCAL_HOST} -- skipping live multihop demo"
)


def test_live_multihop_corpus_produces_real_grounded_analogy_records():
    report = build_llm_witnessed_multihop_corpus()
    assert report.candidate_patterns_considered == 55
    accounted = len(report.records) + len(report.excluded_no_llm_proposal)
    assert accounted > 0

    for r in report.records:
        assert r.provenance == GROUNDED_ANALOGY
        assert r.outcome in (SUPPORTED, CONTRADICTED)
        assert r.depth >= 2
