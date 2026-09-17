# MetaHIA — Third-party Validation Protocol — M6 Non-Degenerate Evidence Mechanism v0.2

## Purpose

Blind independent validation of M6's non-degenerate evidence mechanism
(`m6_corpus_from_m4_m5_v0_2.py`): the fix for a confirmed degeneracy in the base mechanism
(`m6_corpus_from_m4_m5_v0_1.py`, covered by `MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md`,
which stays frozen and unaffected by this protocol) — the base mechanism could, on any
internally-consistent corpus, only ever produce `SUPPORTED` (or no evidence at all), never a
real `CONTRADICTED`, regardless of corpus size.

## Required environment

- Clone `https://github.com/BacemBenSoui/MetaHIA-V10-Research` at the commit this protocol
  ships in (report the exact commit hash used: `git rev-parse HEAD`).
- Do not modify any file in the repository.
- Python 3.11+ recommended (developed and locally verified on 3.13.14).
- Run exactly, from the repository root:

```text
python -m pytest -q tests/test_m6_v0_2_critical_validation_v0_1.py
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
| `m6_corpus_from_m4_m5_v0_2.py` | `6afead8b3e7f75dde47f4f5794ea8cd00e9a7d9b93965c6d6bd50b8a357fdb23` |
| `corpus/family_tree_facts_v0_2.json` | `af11fced7a07437685828977625243fe2b759adf984e8692a1a184db389792d5` |
| `corpus/family_tree_verification_claims_v0_1.json` | `e11d50376034f69e6ce3fb5cd4894b3678d698d3b41fa86ba428e9a046cc70fb` |

`kernel2.py`, `m4_cold_start_evidence_v0_1.py`, `e20d_cognitive_control_v0_1.py` and
`m6_structural_learning_v0_1.py` are unchanged from the M6 v0.1 protocol — same hashes.
`.gitattributes` (`* text=auto eol=lf`) is already in place repo-wide, so a plain `git clone`
on any OS reproduces these hashes directly (see M6 v0.1 protocol's own discrepancy history —
resolved before this protocol was written, not reintroduced).

## Critical contract

The evaluator must verify that the non-degenerate mechanism:

1. **C01 — Evidence comes from independent verification, not replay alone.** A
   `replay_path_pattern_holdout` match against a graph built purely from real facts is
   correct by construction; the presence of any real `CONTRADICTED` record proves the
   independent verification-claims corpus, not the replay itself, decides the outcome.
2. **C02 — Genuine, non-degenerate outcome diversity.** Both `SUPPORTED` and `CONTRADICTED`
   must actually appear among the real records produced.
3. **C03 — Claims match by full skeleton, any length.** Both length-1 (direct relation) and
   length-2 (derived, multi-hop) patterns must reach real evidence — not length-1 only.
4. **C04 — Repeatability.** `build_real_corpus_v2()` must produce the same records and the
   same outcomes across repeated runs.
5. **C05 — Genuinely informative holdout calibration.** The holdout must be non-empty, and
   the resulting Brier score must be strictly between `0.0` and `2.0` — neither the trivial
   perfect score nor the maximally wrong one.
6. **C06 — Promotion gate responds to the threshold on real data.** `evaluate_promotion`
   must block at a threshold just below the actual holdout Brier and allow at a threshold
   just above it, on the same real holdout.
7. **C07 — Honest exclusion.** Every candidate pattern must either produce at least one
   record or be explicitly counted in `excluded_no_verification_claim` — never neither
   (silently dropped) and never both (double-counted); no record may be fabricated for a
   pattern with no matching claim.

## Anti-cheating constraints

- Do not add semantic dictionaries, relation names, domain rules, or hidden thresholds.
- Do not change `kernel2.py`, `m4_cold_start_evidence_v0_1.py`, or
  `e20d_cognitive_control_v0_1.py`.
- Do not replace test inputs with expected outputs.
- Do not hand-construct `StructuralOutcomeRecord`s to stand in for
  `build_real_corpus_v2()`'s actual output when checking C01–C03/C07.
- Do not read the verification claims' `verdict` field from any code path — it is
  documentation only; agreement/disagreement must be discovered by comparing
  `claimed_object` to the real `predicted_end`, confirm this by inspection of
  `m6_corpus_from_m4_m5_v0_2.py` if in doubt.
- Do not tune `brier_threshold` to force a specific promotion verdict for C06 — use the
  actual computed holdout Brier ± 0.05 as specified.

## Required report

- OS and Python version;
- command executed;
- git commit hash of the checkout;
- raw test output for both the critical suite and the full suite;
- PASS/FAIL per critical case (C01–C07);
- confirmation of no file modification;
- confirmation that `python -m pytest -q` (full suite) is zero-regression;
- semantic leakage scan result, including a check that `verdict` is genuinely unused;
- any discrepancy with this document.

## Known, already-disclosed limitations (not discrepancies to (re)discover)

- No claim exists for a pattern of length > 2 — the discovery corpus produces no path longer
  than 2 hops, so this is untested at greater depth, not a limitation of the matching
  mechanism itself.
- The verification-claims corpus is deliberately, transparently adversarial (authored by the
  same people who built the kernel) — it demonstrates the mechanism correctly discriminates
  SUPPORT from CHALLENGE evidence, not that the family-tree facts contain a naturally
  occurring real-world contradiction.
- 49 of 69 candidate patterns have no matching claim and are excluded; this reflects the
  claims corpus's current coverage, not a defect in the matching logic (see C07).

## Governance rule

This mechanism `= PASS_INDEPENDENT_SCOPE` only if all seven critical cases pass, the
repository remains unmodified, the full suite stays at zero regression, and no semantic
leakage is found (including confirming `verdict` is unused). A local PASS does not close the
independent gate — this protocol has not yet been executed by a genuinely external reviewer,
only self-executed during development, and self-execution does not count.

## Scientific non-closure

Even if all critical cases pass, this protocol does not establish:

- a calibration result generalizable beyond this small adversarial verification corpus;
- that the family-tree facts contain any naturally occurring (non-adversarially-authored)
  contradiction;
- optimality of the context-bucketing scheme or the chosen calibration thresholds;
- readiness for promotion of any concrete trained policy;
- production readiness.
