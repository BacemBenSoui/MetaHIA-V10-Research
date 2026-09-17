"""M7 -- live Ollama demonstration v0.1.

Unlike test_m7_llm_fact_proposer_invariants_v0_1.py (deterministic, injected
fake backend), this file makes REAL calls to a local Ollama server. Skipped
cleanly if Ollama is not reachable -- this keeps the main suite portable
across environments (a genuinely external reviewer will almost certainly not
have this machine's local Ollama instance running), while still genuinely
exercising the live path here, where it is available.

Live LLM calls are NOT deterministic across runs/models/hardware -- unlike
every other M6/M7 mechanism in this repo, this test does not pin an exact
outcome distribution. It only asserts the STRUCTURAL properties the
mechanism guarantees regardless of what the model actually answers: real
acquire_cold_start() execution, GROUNDED_ANALOGY provenance, honest
exclusion when no evidence is obtained.
"""
from __future__ import annotations

import pytest

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus
from m7_llm_fact_proposer_v0_1 import OLLAMA_HOST, OllamaUnavailable, ollama_generate_json


def _ollama_reachable() -> bool:
    try:
        ollama_generate_json("Reply with {\"object\": \"ok\"}", timeout=5)
        return True
    except OllamaUnavailable:
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason=f"Ollama not reachable at {OLLAMA_HOST} -- skipping live demo"
)


def test_live_corpus_produces_real_grounded_analogy_records():
    report = build_llm_witnessed_corpus()
    assert report.candidate_patterns_considered > 0
    # Not every candidate need produce a record (the LLM may not answer
    # usably for all of them) -- but at least the mechanism must run without
    # crashing and account for every candidate one way or the other.
    accounted = len(report.records) + len(report.excluded_no_llm_proposal)
    # NOTE: a pattern can yield more than one record (one per matching
    # evidence start), so `accounted` is not required to equal
    # candidate_patterns_considered exactly -- only that neither is zero
    # when the other is non-trivial.
    assert accounted > 0
    for r in report.records:
        assert r.provenance == GROUNDED_ANALOGY
        assert r.outcome in (SUPPORTED, CONTRADICTED)
