# MetaHIA — M4 Validation Summary

Date: 17 September 2026
Status: PASS_INDEPENDENT_SCOPE (project decision recorded in the validation history).

## Local evidence
- 25/25 targeted tests
- 131/131 global regression
- kernel2.py unchanged
- critical corpus and evidence provenance guards covered

## Independent validation
The project history records a positive third-party validation of the frozen M4 package. The detailed external report is not present in the current clean source directory; this summary therefore records the project decision without inventing missing external details.

## Core validated invariants
Human evidence cannot be declared grounded direct/analogy; M1/system output cannot count as independent evidence; independent groups are deduplicated; UNKNOWN is preserved; insufficient evidence can escalate; human provenance is explicit; analogy and direct provenance are distinct; N_min is counted over independent groups; acquisition transitions are auditable; repeated runs are deterministic.
