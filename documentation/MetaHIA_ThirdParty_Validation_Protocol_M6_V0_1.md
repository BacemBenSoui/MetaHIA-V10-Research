# MetaHIA — Third-party Validation Protocol — M6 v0.1

## Purpose

Blind independent validation of M6 — Structural Learning: `Rule × Context × Depth ×
Provenance → distribution of epistemic outcomes`, including its real-corpus integration
with M4 (evidence acquisition) and M5-lineage structural scoring (E20-D.19).

## Required environment

- Clone `https://github.com/BacemBenSoui/MetaHIA-V10-Research` at the commit this protocol
  ships in (report the exact commit hash used — do not assume it, print it: `git rev-parse HEAD`).
- Do not modify any file in the repository.
- Python 3.11+ recommended (developed and locally verified on 3.13.14).
- Run exactly, from the repository root:

```text
python -m pytest -q tests/test_m6_critical_validation_v0_1.py
```

Then, for full-suite zero-regression confirmation:

```text
python -m pytest -q
```

## Frozen file hashes (SHA-256)

| File | SHA-256 |
|---|---|
| `kernel2.py` | `c76adfd2eed8e3ba6022200e7eba6c381f262602f626850cd80af65a0efc9aa9` |
| `m4_cold_start_evidence_v0_1.py` | `7f135417370a621abab0cd8aa733f90aa25eb2160a31413f14b5eeb4b6973400` |
| `e20d_cognitive_control_v0_1.py` | `e090f578ffa72adbc1a693748b879ca94967a63cb88a1eb1c13ccbaea6a15aba` |
| `m6_structural_learning_v0_1.py` | `f62ccd53aff14a437a8b09d658472b21f00a8e07dd1b1b31fb2296c1c55cbdc6` |
| `m6_corpus_from_m4_m5_v0_1.py` | `f075f730498492412788173bb96fb13a60bac147dbddef83a418c97a88e4a1bd` |
| `corpus/family_tree_facts_v0_1.json` | `e53f8226419d0ce79f70f24c72b7af9a32aa6cb7ede7cae70f2f505616153976` |

`kernel2.py` is unchanged by M6 (M6 only imports `structural_signature`, `PathPattern`,
`path_pattern_structural_form` from it) — the hash above matches the kernel already
validated by the M3/M4/M5 third-party protocols in this same repository.

## Critical contract

The evaluator must verify that M6:

1. **C01 — No derived gold.** `outcome=DERIVED` is never accepted as a training label —
   only the three settled M4/M2 states (`SUPPORTED`, `CONTRADICTED`, `UNKNOWN`).
2. **C02 — Structural rule identity.** Two differently-instantiated occurrences of the same
   abstract rule — a Node-kind PATTERN discovered from two different observation pairs, or
   a `PathPattern` discovered from two different path pairs (different `pattern_id`/
   `source_path_ids`) — must land in the same learning bucket. Two genuinely different rules
   must not.
3. **C03 — Rule-level holdout.** `split_by_rule` must never place records of the same rule
   into two different partitions, and must be deterministic for a fixed seed.
4. **C04 — Versioning discipline.** A policy's `version` only advances through `fit()`;
   calling `predict()` any number of times must never change it.
5. **C05 — Honest backoff.** `predict()` must report which basis it used
   (`EXACT_BUCKET` / `RULE_ONLY` / `GLOBAL_PRIOR` / `UNIFORM_NO_DATA`) and must never
   report a finer basis than the data actually supports.
6. **C06 — Proper, bounded, decomposed calibration.** Multi-class Brier score stays in
   `[0, 2]` and is exactly `0` for a perfectly correct policy; `calibration_report` must
   mark a bucket below `min_support` as `sufficient_data=False` rather than silently
   including or silently dropping it.
7. **C07 — Promotion fails closed.** `evaluate_promotion` must refuse promotion on an empty
   holdout, on a candidate regressing versus the previous version, and on any
   sufficiently-supported catastrophically-miscalibrated bucket — and must NOT let an
   under-supported bucket block promotion either way.
8. **C08 — Genuine, traceable real-corpus evidence.** Every `StructuralOutcomeRecord`
   produced by `m6_corpus_from_m4_m5_v0_1.build_real_corpus()` must trace to a real,
   non-empty `AcquisitionResult.evidence` obtained through `acquire_cold_start()`, using
   only `evidence_facts` genuinely disjoint from the `discovery_facts` a rule was
   generalized from. Candidates without admissible evidence must be excluded and reported,
   never assigned a fabricated outcome.
9. **C09 — Negative path on real machinery, kept separate.** `demo_contradicted_case()`
   must reach `CONTRADICTED` through the same real `acquire_cold_start()`/evaluator
   machinery when evidence genuinely conflicts, and must not be counted as part of the
   real-corpus statistics reported under C08.

## Anti-cheating constraints

- Do not add semantic dictionaries, relation names, domain rules, or hidden thresholds.
- Do not change `kernel2.py`, `m4_cold_start_evidence_v0_1.py`, or
  `e20d_cognitive_control_v0_1.py`.
- Do not replace test inputs with expected outputs.
- Do not hand-construct `StructuralOutcomeRecord`s to stand in for
  `build_real_corpus()`'s actual output when checking C08/C09.
- Do not tune `brier_threshold` / `per_bucket_brier_threshold` to force a specific
  promotion verdict — report the verdict the stated thresholds actually produce.

## Required report

- OS and Python version;
- command executed;
- git commit hash of the checkout;
- raw test output for both the critical suite and the full suite;
- PASS/FAIL per critical case (C01–C09);
- confirmation of no file modification;
- confirmation that `python -m pytest -q` (full suite) is zero-regression;
- semantic leakage scan result;
- any discrepancy with this document.

## Known, already-disclosed limitation (not a discrepancy to (re)discover)

The real corpus (`corpus/family_tree_facts_v0_1.json`, 22 facts) is small: only 2 of 28
candidate patterns reach real evidence, and 2 rules are too few for `split_by_rule` to
produce a non-empty holdout at default fractions. `evaluate_promotion` therefore correctly
returns `EMPTY_HOLDOUT` on this corpus (see C08's test and
`MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 5) — this is expected, not a defect, and
does not by itself constitute a failure of any critical case above.

## Governance rule

`M6 = PASS_INDEPENDENT_SCOPE` only if all nine critical cases pass, the repository remains
unmodified, the full suite stays at zero regression, and no semantic leakage is found. A
local PASS does not close the independent gate.

## Scientific non-closure

Even if all critical cases pass, this protocol does not establish:

- a calibration result generalizable beyond this small real corpus;
- optimality of the context-bucketing scheme (3×3 novelty/redundancy bands) or of the
  chosen calibration thresholds;
- semantic truth of any learned rule's predicted outcome distribution;
- readiness for promotion of any concrete trained policy;
- production readiness.
