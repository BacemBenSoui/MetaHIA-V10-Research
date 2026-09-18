# MetaHIA — Third-party Validation Protocol — M7 Empirical LLM Loop v0.1

## Purpose

Blind independent validation of M7's two components:

1. **Fact-proposer mechanism** (`m7_llm_fact_proposer_v0_1.py`,
   `m7_corpus_from_llm_v0_1.py`) — an LLM acting as an independent witness over an
   already-structured corpus, feeding `GROUNDED_ANALOGY` evidence through M4's real
   `acquire_cold_start()`/evaluator machinery. Includes a LAN-sandbox fallback
   (`192.168.1.11`) that must trigger only on genuine unreachability.
2. **Mixed-corpus promotion integration** (`m7_corpus_mixed_v0_1.py`) — unions the LLM
   evidence with M6's already-validated adversarial-corpus evidence
   (`m6_corpus_from_m4_m5_v0_2.py`) and re-runs M6's unchanged
   `split_by_rule`/`StructuralLearningPolicy`/`evaluate_promotion` pipeline, to check
   whether adding LLM evidence changes holdout calibration.

Both M6 protocols (`MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md` and
`..._M6_NonDegenerate_V0_2.md`) stay frozen and unaffected by this protocol.

## What this protocol does NOT ask you to validate

This is deliberately **not** a validation of the LLM's accuracy. The already-disclosed
empirical result (see "Known, already-disclosed limitations" below) is that the local
model's answers disagree with ground truth on every case tested, and that mixing this
evidence into the M6 promotion pipeline was calibration-neutral, not an improvement.
Your task is to confirm the **mechanism** is honest, non-circular, fail-closed and
reproducible in its deterministic parts — not to judge whether the LLM is a good
witness. A mechanically-sound package that reports a weak or neutral result is a PASS
here, exactly as the M6 v0.1 protocol validated a mechanism that produced only 2/28 real
evidence records and an empty holdout.

## Required environment

- Clone `https://github.com/BacemBenSoui/MetaHIA-V10-Research` at the commit this
  protocol ships in (report the exact commit hash used: `git rev-parse HEAD`).
- Do not modify any file in the repository.
- Python 3.11+ recommended (developed and locally verified on 3.13.14).
- **No Ollama installation or network access is required to pass this protocol.** The
  mandatory critical suite (below) uses an injected fake LLM backend throughout — it
  never makes a real network call. If Ollama happens to be reachable at
  `http://localhost:11434` on your machine, two additional live-demonstration tests will
  run instead of skipping (see "Optional live demonstration" below); this is informative
  extra confirmation, not part of the pass/fail contract.
- Run exactly, from the repository root:

```text
python -m pytest -q tests/test_m7_critical_validation_v0_1.py
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
| `m6_structural_learning_v0_1.py` | `f62ccd53aff14a437a8b09d658472b21f00a8e07dd1b1b31fb2296c1c55cbdc6` |
| `m6_corpus_from_m4_m5_v0_2.py` | `6afead8b3e7f75dde47f4f5794ea8cd00e9a7d9b93965c6d6bd50b8a357fdb23` |
| `m7_llm_fact_proposer_v0_1.py` | `973270e66c8d5661d04ef0697002d95fd0c6a245e771bdcbd388dbfc158e0642` |
| `m7_corpus_from_llm_v0_1.py` | `aa3ddc19534723174fa857faa598222fd1d6c640904f7daec70d9174d71baab2` |
| `m7_corpus_mixed_v0_1.py` | `f6b4f6876718fc34fee8c16efafc20bcdd787ebd3bfc7536202bfa62a1891c61` |
| `corpus/family_tree_facts_v0_2.json` | `af11fced7a07437685828977625243fe2b759adf984e8692a1a184db389792d5` |
| `corpus/family_tree_verification_claims_v0_1.json` | `e11d50376034f69e6ce3fb5cd4894b3678d698d3b41fa86ba428e9a046cc70fb` |

`kernel2.py`, `m4_cold_start_evidence_v0_1.py`, `m6_structural_learning_v0_1.py`,
`m6_corpus_from_m4_m5_v0_2.py` and both corpus files are unchanged from the M6 v0.2
protocol — same hashes. `.gitattributes` (`* text=auto eol=lf`) is already in place
repo-wide, so a plain `git clone` on any OS reproduces these hashes directly (see the M6
v0.1 protocol's own past CRLF discrepancy, resolved before this protocol was written and
not reintroduced).

## Critical contract

The evaluator must verify that:

1. **C01 — No prompt leakage.** The real predicted object is never present in the prompt
   text sent to the LLM (the fact-proposer's core non-circularity guarantee).
2. **C02 — Fail-closed parsing.** Any malformed, non-JSON, non-dict, missing-key,
   non-string, or empty LLM response is treated as "no proposal" — never fabricated into
   one.
3. **C03 — Evidence classification.** LLM evidence is always `GROUNDED_ANALOGY`, never
   `GROUNDED_DIRECT` or `UNGROUNDED_HUMAN`; agreement with the real prediction yields
   `SUPPORT`, disagreement yields `CHALLENGE`.
4. **C04 — Fallback discipline.** The LAN-sandbox fallback triggers only when the primary
   host is genuinely unreachable — never merely because it returned an unusable
   response.
5. **C05 — Correct attribution.** A proposal's `.model` field always names whichever
   backend actually answered (local or LAN fallback), never the primary model merely
   requested but never answering.
6. **C06 — Mixed-corpus fairness.** The LLM mechanism can only add evidence for rule
   signatures already present in the adversarial corpus — never a rule the adversarial
   mechanism doesn't already know about. This is what makes the promotion comparison a
   genuine same-holdout comparison rather than one confounded by different holdout
   composition.
7. **C07 — No hidden transformation.** With zero LLM evidence (the LLM proposes
   nothing), the "mixed" calibration run must be numerically **identical** to the
   adversarial-only baseline — not merely close.
8. **C08 — No silent alteration of the already-validated mechanism.** The mixed-corpus
   module's adversarial-only baseline must reproduce exactly the holdout Brier
   (`0.48125`) already independently validated for `m6_corpus_from_m4_m5_v0_2.py` in the
   M6 v0.2 protocol, and its record set must match `build_real_corpus_v2()`'s own output
   record-for-record.
9. **C09 — Honest exclusion.** Every length-1 candidate pattern the LLM mechanism
   considers either yields at least one record or is explicitly counted in
   `excluded_no_llm_proposal` — never neither (silently dropped) and never both
   (double-counted).

## Anti-cheating constraints

- Do not add semantic dictionaries, relation names, domain rules, or hidden thresholds.
- Do not change `kernel2.py`, `m4_cold_start_evidence_v0_1.py`,
  `m6_structural_learning_v0_1.py`, or `m6_corpus_from_m4_m5_v0_2.py`.
- Do not replace test inputs with expected outputs.
- Do not hand-construct `StructuralOutcomeRecord`s or `LLMProposal`s to stand in for the
  actual mechanism's output when checking C01-C09.
- Do not inspect or use `raw_response`/prompt internals to shortcut C01 — verify by
  capturing the actual prompt string, as the shipped test does.
- Do not tune `brier_threshold` to force a specific promotion verdict — the critical
  suite does not test the promotion gate's threshold behavior directly (that is already
  covered, unchanged, by the M6 v0.2 protocol); it only checks C07/C08's numerical
  identity/reproduction properties.

## Optional live demonstration (not required for PASS)

If Ollama is reachable at `http://localhost:11434` on your machine with `llama3.2:latest`
pulled, you may additionally run:

```text
python -m pytest -q tests/test_m7_live_ollama_demo_v0_1.py tests/test_m7_mixed_corpus_live_demo_v0_1.py -v -s
```

These make real network calls and are **not required** for this protocol's pass/fail
verdict — they skip cleanly (reported as `SKIPPED`, not a failure) when Ollama is
unreachable, which is the expected and normal outcome for most evaluators. If you do run
them, report the actual numbers you observe (they are not pinned to an exact value,
since a live LLM call is not reproducible across models/hardware) alongside a note on
which model answered.

## Required report

- OS and Python version;
- command executed;
- git commit hash of the checkout;
- raw test output for both the critical suite and the full suite;
- PASS/FAIL per critical case (C01-C09);
- confirmation of no file modification;
- confirmation that `python -m pytest -q` (full suite) is zero-regression;
- whether Ollama was reachable, and if so, the raw output of the two optional live-demo
  tests (or explicit confirmation they were skipped);
- any discrepancy with this document.

## Known, already-disclosed limitations (not discrepancies to (re)discover)

- The local model (`llama3.2:latest`) disagreed with the real structural prediction on
  **16/16** length-1 cases in the actual run performed 2026-09-17 (all classified
  `CONTRADICTED`) — a genuine empirical finding about this small model's accuracy on this
  closed-book task, not a mechanism defect (see
  `MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` Sec.4 for the traced example).
- Feeding this evidence into the mixed-corpus promotion pipeline (2026-09-18) moved the
  holdout Brier from `0.48125` (baseline) to `0.47` (mixed) — a small movement on a
  5-8-record holdout, explicitly assessed as calibration-**neutral** at this scale, not a
  demonstrated improvement (see `MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` Sec.6). This is
  the reason this protocol validates the mechanism, not the model's competence.
- M7's LLM mechanism only covers length-1 (direct) patterns; the adversarial corpus it is
  compared against also covers length-2 (derived) patterns. This asymmetry is
  intentional (documented scope choice, not an oversight) and is exactly why C06/C07/C08
  check fairness and non-alteration rather than full parity of coverage.
- The free-text-to-structure parser (LLM turning natural language into facts) is a
  separately deferred roadmap item, entirely out of scope here — M7 v0.1 only asks the
  LLM about relations already present in a structured corpus.

## Governance rule

M7 (fact-proposer + mixed-corpus integration) `= PASS_INDEPENDENT_SCOPE` only if all nine
critical cases pass, the repository remains unmodified, and the full suite stays at zero
regression. A local PASS does not close the independent gate — this protocol has not yet
been executed by a genuinely external reviewer, only self-executed during development,
and self-execution does not count (same rule already applied to M6, see
`JOURNAL_DE_BORD.md`).

## Scientific non-closure

Even if all critical cases pass, this protocol does not establish:

- that the LLM is an accurate or useful witness (the opposite is the current disclosed
  finding);
- that adding LLM evidence to the M6 promotion pipeline improves calibration in general,
  on a larger corpus, or with a different model;
- readiness to extend this mechanism to patterns of length > 1;
- readiness for third-party validation of a free-text-to-structure parser (a distinct,
  unstarted roadmap item);
- production readiness.
