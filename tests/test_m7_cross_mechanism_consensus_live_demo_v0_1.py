"""M7 -- cross-mechanism consensus, live Ollama demonstration v0.1.

Makes REAL calls to Ollama (both the witness and parser mechanisms, each
using their own real default backend -- local primary, LAN fallback only on
genuine unreachability). Skipped cleanly if the local host is unreachable,
same portability reason as the other live demos.

Does not pin an exact record count or outcome distribution -- live LLM
output is not reproducible across runs/models/hardware. Only asserts the
structural guarantees: every accepted record is GROUNDED_ANALOGY, and every
candidate is honestly accounted for.
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_cross_mechanism_consensus_v0_1 import build_cross_mechanism_corpus
from m7_llm_fact_proposer_v0_1 import LOCAL_HOST


def _ollama_reachable() -> bool:
    try:
        urllib.request.urlopen(f"{LOCAL_HOST}/api/tags", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason=f"Ollama not reachable at {LOCAL_HOST} -- skipping live cross-mechanism demo"
)


def test_live_cross_mechanism_corpus_honestly_accounts_for_every_candidate():
    report = build_cross_mechanism_corpus()
    assert report.candidate_patterns_considered == 14

    accounted = (
        len(report.records)
        + len(report.excluded_mechanism_failed)
        + len(report.excluded_disagreement)
        + len(report.excluded_parsing_mismatch)
        + len(report.excluded_no_matching_text_claim)
    )
    assert accounted >= report.candidate_patterns_considered

    for r in report.records:
        assert r.provenance == GROUNDED_ANALOGY
        assert r.outcome in (SUPPORTED, CONTRADICTED)
        assert r.record_id.startswith("crossconsensusv1::")
