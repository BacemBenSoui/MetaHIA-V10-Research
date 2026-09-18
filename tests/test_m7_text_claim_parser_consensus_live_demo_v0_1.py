"""M7 -- consensus text-claim parser, live Ollama demonstration v0.1.

Makes REAL calls to BOTH the local Ollama server AND the LAN sandbox server
-- unlike every other live demo in this repo, this one needs TWO reachable
hosts (both voters are always contacted, never primary/fallback). Skipped
cleanly if either is unreachable.

Does not pin an exact record count or outcome distribution -- live LLM
output is not reproducible across runs/models/hardware. Only asserts the
structural guarantees: every accepted record is GROUNDED_ANALOGY with a
consensus model tag, and every candidate is honestly accounted for across
the four exclusion reasons or a produced record.
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from m4_cold_start_evidence_v0_1 import CONTRADICTED, GROUNDED_ANALOGY, SUPPORTED
from m7_corpus_from_text_claims_consensus_v0_1 import build_consensus_text_claim_corpus
from m7_llm_fact_proposer_v0_1 import LAN_FALLBACK_HOST, LOCAL_HOST


def _reachable(host: str) -> bool:
    try:
        urllib.request.urlopen(f"{host}/api/tags", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not (_reachable(LOCAL_HOST) and _reachable(LAN_FALLBACK_HOST)),
    reason=f"Both {LOCAL_HOST} and {LAN_FALLBACK_HOST} must be reachable for the consensus demo -- skipping",
)


def test_live_consensus_corpus_honestly_accounts_for_every_candidate():
    report = build_consensus_text_claim_corpus()
    assert report.candidate_patterns_considered == 14

    accounted = (
        len(report.records)
        + len(report.excluded_voter_failed)
        + len(report.excluded_disagreement)
        + len(report.excluded_parsing_mismatch)
        + len(report.excluded_no_matching_text_claim)
    )
    assert accounted >= report.candidate_patterns_considered

    for r in report.records:
        assert r.provenance == GROUNDED_ANALOGY
        assert r.outcome in (SUPPORTED, CONTRADICTED)
        assert r.record_id.startswith("textconsensusv1::")
