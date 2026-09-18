"""One-off script (not a test): prints the real text-claim parser results --
parsing fidelity against the corpus author's own asserted_object (golden
check, informational only, never used to gate the evidence mechanism) and
the actual evidence outcome distribution. Makes a real Ollama call.
"""
from __future__ import annotations

import json

from m7_corpus_from_text_claims_v0_1 import TEXT_CLAIMS_PATH, build_text_claim_corpus
from m7_text_claim_parser_v0_1 import parse_claim_from_text

data = json.loads(TEXT_CLAIMS_PATH.read_text(encoding="utf-8"))
allowed_relations = ["MERE_DE", "PERE_DE", "ENFANT_DE", "FILS_DE", "FILLE_DE", "FRERE_DE", "SOEUR_DE", "EPOUSE_DE", "EPOUX_DE"]

golden_rows = []
for claim in data["claims"]:
    parsed = parse_claim_from_text(claim["text"], allowed_relations=allowed_relations)
    golden_rows.append({
        "claim_id": claim["claim_id"],
        "text": claim["text"],
        "declared": (claim["subject"], claim["relation"], claim["asserted_object"]),
        "parsed": None if parsed is None else (parsed.subject, parsed.relation, parsed.object),
        "subject_relation_match": parsed is not None and parsed.subject == claim["subject"] and parsed.relation == claim["relation"],
        "object_match": parsed is not None and parsed.object == claim["asserted_object"],
    })

report = build_text_claim_corpus()

print(json.dumps({
    "golden_parsing_check": golden_rows,
    "parsing_fidelity_subject_relation": sum(1 for r in golden_rows if r["subject_relation_match"]) / len(golden_rows),
    "parsing_fidelity_object": sum(1 for r in golden_rows if r["object_match"]) / len(golden_rows),
    "candidate_patterns_considered": report.candidate_patterns_considered,
    "records": len(report.records),
    "excluded_no_matching_text_claim": len(report.excluded_no_matching_text_claim),
    "excluded_no_parse": len(report.excluded_no_parse),
    "excluded_parsing_mismatch": len(report.excluded_parsing_mismatch),
    "outcomes": {o: sum(1 for r in report.records if r.outcome == o) for o in {r.outcome for r in report.records}},
}, indent=2, ensure_ascii=False, default=str))
