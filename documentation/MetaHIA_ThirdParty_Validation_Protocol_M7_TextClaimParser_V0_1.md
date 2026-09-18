# MetaHIA — Third-party Validation Protocol — M7 Free-text Claim Parser v0.1

## Purpose

Blind independent validation of M7's free-text claim parser
(`m7_text_claim_parser_v0_1.py`, `m7_corpus_from_text_claims_v0_1.py`): the LLM extracts a
(subject, relation, object) claim from one independently-authored French sentence, and that
claim is compared to a real structural prediction from kernel replay -- producing
`GROUNDED_ANALOGY` evidence through M4's real `acquire_cold_start()`/evaluator machinery,
exactly like the already-validated closed-question mechanism
(`m7_llm_fact_proposer_v0_1.py`, see `MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md`,
which stays frozen and unaffected by this protocol).

## What this protocol does NOT ask you to validate

Exactly as for the closed-question M7 protocol: this is **not** a validation of the LLM's
accuracy. The already-disclosed empirical result (see "Known, already-disclosed limitations"
below) is 50% parsing fidelity against an independent golden check, with genuine outcome
diversity among the successfully-parsed claims. Your task is to confirm the **mechanism** is
honest, non-circular, fail-closed on both malformed output AND on a closed relation
vocabulary, and correctly distinguishes "no answer" from "wrong answer" from "answer about
the wrong subject" -- not to judge whether the LLM parses French sentences well.

## Required environment

- Clone `https://github.com/BacemBenSoui/MetaHIA-V10-Research` at the commit this protocol
  ships in (report the exact commit hash used: `git rev-parse HEAD`).
- Do not modify any file in the repository.
- Python 3.11+ recommended (developed and locally verified on 3.13.14).
- **No Ollama installation or network access is required to pass this protocol.** The
  mandatory critical suite uses an injected fake LLM backend throughout. If Ollama happens to
  be reachable at `http://localhost:11434` on your machine, one additional live-demonstration
  test will run instead of skipping (see "Optional live demonstration" below); this is
  informative extra confirmation, not part of the pass/fail contract.
- Run exactly, from the repository root:

```text
python -m pytest -q tests/test_m7_text_claim_parser_critical_validation_v0_1.py
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
| `m7_llm_fact_proposer_v0_1.py` | `973270e66c8d5661d04ef0697002d95fd0c6a245e771bdcbd388dbfc158e0642` |
| `m7_text_claim_parser_v0_1.py` | `7250584087d7e9f233b5901c2fa71a9ad182d4be0ffcc6864e46a61dd0be0e45` |
| `m7_corpus_from_text_claims_v0_1.py` | `67cf5cf7c6605d6b7cbd0318e15db5c96421c85d0c65359009685316bc67f620` |
| `corpus/family_tree_facts_v0_2.json` | `af11fced7a07437685828977625243fe2b759adf984e8692a1a184db389792d5` |
| `corpus/family_tree_text_claims_v0_1.json` | `908568d1682336635887bf685a5b80136fae9817143e70efa75de125b94edcc7` |

`kernel2.py`, `m4_cold_start_evidence_v0_1.py`, `m6_structural_learning_v0_1.py`,
`m7_llm_fact_proposer_v0_1.py` and `corpus/family_tree_facts_v0_2.json` are unchanged from the
M7 fact-proposer protocol -- same hashes. `.gitattributes` (`* text=auto eol=lf`) is already in
place repo-wide, so a plain `git clone` on any OS reproduces these hashes directly, including
the French-accented content of `family_tree_text_claims_v0_1.json` (verify this specifically --
a text-encoding mismatch would be a real integrity discrepancy here, unlike in the other
protocols where corpus content is plain ASCII).

## Critical contract

The evaluator must verify that:

1. **C01 — Fail-closed parsing.** Any malformed, non-JSON, non-dict, missing-key,
   non-string, or empty-string response is treated as "no claim" -- never fabricated into
   one.
2. **C02 — Fail-closed vocabulary.** A relation named outside the closed vocabulary provided
   to the model is rejected outright -- never coerced into the nearest-looking known
   relation.
3. **C03 — Well-formed acceptance.** A well-formed, in-vocabulary extraction is accepted,
   with fields correctly trimmed.
4. **C04 — Genuine constraint delivery.** The prompt actually contains both the sentence
   being parsed and the FULL closed relation vocabulary -- the fail-closed vocabulary
   contract only means something if the model is actually told the constraint.
5. **C05 — Mismatch exclusion.** A well-formed extraction whose subject/relation do NOT
   match what the sentence is independently known to be about is excluded as a parsing
   mismatch -- never silently paired with the wrong structural candidate.
6. **C06 — Honest "no answer" accounting.** A model that never answers usably yields zero
   evidence records, with every candidate accounted for as `excluded_no_parse`.
7. **C07 — Non-circularity.** The corpus author's own answer key (`asserted_object`) never
   influences the evidence decision -- SUPPORT/CHALLENGE is computed purely from comparing
   the model's own extracted object to the real kernel-predicted object, confirmed by
   forcing every extraction to a value that disagrees with `asserted_object` and observing
   the outcome is still computed correctly against the real prediction (all `CONTRADICTED`
   in that forced scenario, not mixed).
8. **C08 — Mechanism wiring.** A simulated perfect parser (one that always extracts exactly
   what the corpus author intended) reproduces the corpus's designed outcome diversity: 10
   agreeing, 6 deliberately wrong.
9. **C09 — Cross-mechanism consistency.** The candidate-pattern count matches the sibling
   closed-question mechanism (`m7_corpus_from_llm_v0_1.py`) exactly, since both draw on the
   same underlying corpus and the same length-1 scoping.

## Anti-cheating constraints

- Do not add semantic dictionaries, relation names, domain rules, or hidden thresholds.
- Do not change `kernel2.py`, `m4_cold_start_evidence_v0_1.py`, `m6_structural_learning_v0_1.py`,
  or `m7_llm_fact_proposer_v0_1.py`.
- Do not replace test inputs with expected outputs.
- Do not hand-construct `ParsedClaim`s or `StructuralOutcomeRecord`s to stand in for the
  actual mechanism's output when checking C01-C09.
- Do not read `asserted_object` from any code path other than a dedicated, separate golden
  check -- confirm by inspection of `m7_corpus_from_text_claims_v0_1.py` that its main
  builder function never references that key.
- Do not tune the fail-closed vocabulary check to accept a near-miss relation string.

## Optional live demonstration (not required for PASS)

If Ollama is reachable at `http://localhost:11434` with `llama3.2:latest` pulled, you may
additionally run:

```text
python -m pytest -q tests/test_m7_text_claim_parser_live_demo_v0_1.py -v -s
```

Not required for this protocol's verdict -- skips cleanly (`SKIPPED`, not a failure) when
Ollama is unreachable. If you do run it, report the actual numbers observed (not pinned to an
exact value, since live LLM output is not reproducible across models/hardware) -- and note
that even two calls with the identical sentence to the same local model may disagree (already
observed and disclosed here, not a protocol violation if you see it too).

## Required report

- OS and Python version;
- command executed;
- git commit hash of the checkout;
- raw test output for both the critical suite and the full suite;
- PASS/FAIL per critical case (C01-C09);
- confirmation of no file modification;
- confirmation that `python -m pytest -q` (full suite) is zero-regression;
- confirmation that `corpus/family_tree_text_claims_v0_1.json`'s French accented text reads
  correctly (not mojibake) after your checkout -- a real encoding discrepancy would be worth
  reporting here, distinct from a display artifact in a diagnostic script;
- whether Ollama was reachable, and if so, the raw output of the optional live-demo test (or
  explicit confirmation it was skipped);
- any discrepancy with this document.

## Known, already-disclosed limitations (not discrepancies to (re)discover)

- Real parsing fidelity against the golden check was **8/16 (50%)** in the actual run
  performed 2026-09-18 with `llama3.2:latest` -- a genuine empirical finding about this small
  model's accuracy on a closed-book French sentence-understanding task, not a mechanism
  defect (see `MetaHIA_M7_TextClaimParser_V0_1.md` Sec.5).
- Of the 7 failures beyond outright rejection, one was a genuine parsing-fidelity error
  (subject/object inverted, relation confused with its reverse) -- an example of exactly the
  C05 mismatch category, observed for real, not merely hypothesized.
- The golden check and the corpus-building pipeline each call Ollama separately (no caching)
  for the identical sentence; at least one case produced a DIFFERENT answer between the two
  real calls -- this small local model is not perfectly stable run-to-run at default
  temperature. Not a mechanism defect; disclosed as a property of the LLM backend.
- 3 of 14 candidate patterns (`ENFANT_DE` both directions, `PERE_DE` forward) have no authored
  text claim in this v0.1 corpus -- a disclosed coverage gap, not a matching-logic defect (see
  C09's exact candidate count, which includes these uncovered patterns).
- This mechanism only covers length-1 (direct) patterns, mirroring
  `m7_corpus_from_llm_v0_1.py`'s own scoping precedent.
- The alternative architectural role considered and set aside for this version -- the LLM
  authoring NEW graph facts directly, rather than evidence about an existing prediction -- is
  out of scope here entirely (see `MetaHIA_M7_TextClaimParser_V0_1.md` Sec.2).

## Governance rule

This mechanism `= PASS_INDEPENDENT_SCOPE` only if all nine critical cases pass, the
repository remains unmodified, and the full suite stays at zero regression. A local PASS does
not close the independent gate -- this protocol has not yet been executed by a genuinely
external reviewer, only self-executed during development, and self-execution does not count
(same rule already applied to M6 and to M7's closed-question mechanism, see
`JOURNAL_DE_BORD.md`).

## Scientific non-closure

Even if all critical cases pass, this protocol does not establish:

- that the LLM is an accurate or reliable French-sentence parser (the opposite is the current
  disclosed finding, 50% fidelity);
- readiness to extend this mechanism to patterns of length > 1;
- readiness to integrate this evidence source into the M6 mixed-corpus promotion pipeline;
- that the "text → new graph facts" architectural alternative (set aside for this version)
  would be safe or well-specified;
- production readiness.
