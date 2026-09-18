"""One-off script (not a test): measures REAL resource overhead (network
call count, per-call latency, host used, total wall-clock time) of each M7
evidence mechanism, to inform the keep-both/keep-one decision the project
owner asked for. Monkeypatches m7_llm_fact_proposer_v0_1.ollama_generate_json
at runtime (this process only, not the source file) to instrument every
real call without duplicating any network logic.
"""
from __future__ import annotations

import json
import time

import m7_llm_fact_proposer_v0_1 as m7base

_calls = []
_real_ollama_generate_json = m7base.ollama_generate_json


def _instrumented(prompt, *, model, host, timeout=30.0):
    start = time.perf_counter()
    try:
        result = _real_ollama_generate_json(prompt, model=model, host=host, timeout=timeout)
        _calls.append({"host": host, "model": model, "seconds": time.perf_counter() - start, "ok": True})
        return result
    except Exception:
        _calls.append({"host": host, "model": model, "seconds": time.perf_counter() - start, "ok": False})
        raise


m7base.ollama_generate_json = _instrumented


def _measure(label, fn):
    _calls.clear()
    t0 = time.perf_counter()
    report = fn()
    wall_seconds = time.perf_counter() - t0
    calls_by_host = {}
    for c in _calls:
        calls_by_host.setdefault(c["host"], []).append(c["seconds"])
    return {
        "label": label,
        "wall_seconds": round(wall_seconds, 2),
        "total_calls": len(_calls),
        "calls_by_host": {h: {"count": len(v), "total_seconds": round(sum(v), 2), "mean_seconds": round(sum(v) / len(v), 2)} for h, v in calls_by_host.items()},
        "records": len(report.records),
    }


results = []

from m7_corpus_from_llm_v0_1 import build_llm_witnessed_corpus
results.append(_measure("witness_alone", build_llm_witnessed_corpus))

from m7_corpus_from_text_claims_v0_1 import build_text_claim_corpus
results.append(_measure("parser_alone", build_text_claim_corpus))

from m7_corpus_from_cross_mechanism_consensus_v0_1 import build_cross_mechanism_corpus
results.append(_measure("cross_mechanism_consensus", build_cross_mechanism_corpus))

print(json.dumps(results, indent=2))
