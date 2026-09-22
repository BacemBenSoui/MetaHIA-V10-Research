# MetaHIA — Third-party Validation Protocol — P4-T Structural Transformation Induction v0.1

## Purpose

Blind independent validation of P4-T's structural-transformation-induction mechanism
(Gates A-G, `p4t_structural_transformation_induction_v0_1.py`) and its two locked
train/holdout/witness benchmarks (`p4t_locked_benchmark_runner_v0_1.py`,
`p4t_locked_benchmark_runner_v0_2.py`), plus the two adapters built on top of it:
P4-T.5 emergent-structure verification (`p4t_emergent_structure_v0_1.py`) and P4-T.6
ROI scoring reused from E20-D.19 (`score_hypothesis_roi()`, inside the main P4-T
module).

This is **P4-T.7** in the project's own roadmap
(`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.2, item 7):
"validation indépendante (paquet tiers, comme M4-M7)". It follows the exact same
pattern already established for M6 and M7 — see
`MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md`,
`..._M6_NonDegenerate_V0_2.md`, and `..._M7_V0_1.md`, all of which stay frozen and
unaffected by this protocol.

## What this protocol does NOT ask you to validate

This is **not** a validation that P4-T closes the E20-D gate, and **not** a validation
of general unsupervised relation discovery. P4-T's own design document already
discloses, without prompting, that this is "structural transformation induction from
paired examples", not "autonomous discovery in an unstructured graph" — the mechanism
receives `(source, target)` pairs during training; it does not discover that a
relation exists in the first place. Your task is to confirm that the
discover→select→freeze→blind-replay→commit→reveal pipeline is **honest, non-circular,
fail-closed, and reproducible** in its deterministic parts — the same mechanism-level
scope already validated for M6 and M7, not a judgment on whether P4-T amounts to
general relational learning.

## Required environment

- Clone `https://github.com/BacemBenSoui/MetaHIA-V10-Research` at the commit this
  protocol ships in (report the exact commit hash used: `git rev-parse HEAD`).
- Do not modify any file in the repository.
- Python 3.11+ recommended.
- **No network access, no LLM/Ollama, no external service of any kind is required or
  used anywhere in this protocol.** Every mechanism under test here is deterministic
  Python with no I/O beyond writing one JSON prediction file per locked benchmark
  version (`validation/p4t_locked_benchmark_predictions_v0_1.json`,
  `..._v0_2.json`) — this distinguishes P4-T from M7, whose critical suite needed a
  network-free subset carved out specifically to avoid an LLM dependency; here the
  full existing test files already are that subset.
- Run exactly, from the repository root:

```text
python -m pytest -q tests/test_p4t_structural_transformation_induction_v0_1.py tests/test_p4t_locked_benchmark_v0_1.py tests/test_p4t_locked_benchmark_v0_2.py tests/test_p4t_emergent_structure_v0_1.py
```

Then, for full-suite zero-regression confirmation:

```text
python -m pytest -q
```

## Frozen file hashes (SHA-256)

| File | SHA-256 |
|---|---|
| `kernel2.py` | `c76adfd2eed8e3ba6022200e7eba6c381f262602f626850cd80af65a0efc9aa9` |
| `e20d_protocol.py` | `522e42bd4eb8fbfcafe34b496bdce21b11a98a802d9e6bd8271880dfa608540a` |
| `e20d_cognitive_control_v0_1.py` | `e090f578ffa72adbc1a693748b879ca94967a63cb88a1eb1c13ccbaea6a15aba` |
| `p4t_structural_transformation_induction_v0_1.py` | `0888c6198bed2ec60deb82ff4c4e1e2977b1d2faa9a4fdceb3f8ad2641108493` |
| `p4t_locked_benchmark_cases_v0_1.py` | `d5d1d13f368c6eff1e1850c9c579ea342950c652b65fc40b312012093929f9ee` |
| `p4t_locked_benchmark_witness_v0_1.py` | `b6a7d1c5fce91c00dbdd0e5a413fe46881d00cb0764584011f07d786d5cfc307` |
| `p4t_locked_benchmark_runner_v0_1.py` | `9c264c790b35a5970bb653b035c1944ea0ffa1afd234622b0939240a6c06ea5a` |
| `p4t_locked_benchmark_cases_v0_2.py` | `c1955d95d78ca729cca5a9adb1f64fc343d73142ef613d9929c994e25ca0eba4` |
| `p4t_locked_benchmark_witness_v0_2.py` | `aa5d2306fdf17662a67e71053aef72735c7e278940a0968faf1ef5e6740f3fcb` |
| `p4t_locked_benchmark_runner_v0_2.py` | `10b339be3a719a376a8852a22d29f4a42bc9d8436be2a2f828522c87db7448cb` |
| `p4t_emergent_structure_v0_1.py` | `262bca52fb906a5ab2fc682d9c2a02f7e51dc811e4ba36c23b8412101142c771` |

`kernel2.py`'s hash is unchanged from the M6/M7 protocols (same file, same commit
history). `.gitattributes` (`* text=auto eol=lf`) is already in place repo-wide, so a
plain `git clone` on any OS reproduces these hashes directly.

## Critical contract

The evaluator must verify that:

1. **C01 — No provenance leak (reference/permutation/recursive families, Gate B).**
   A frozen transformation never embeds a training `NodeRef`/row id anywhere an
   observer could read it back — verified by
   `test_frozen_transformation_does_not_leak_training_node_refs` and
   `test_frozen_recursive_transformation_does_not_leak_training_row_ids`.
2. **C02 — No provenance leak (pattern literal constraint, P4-T.1 bis hardening).**
   `test_frozen_pattern_does_not_leak_a_literal_constraint_node_ref` — the specific
   residual leak an earlier external review found and this project fixed (see
   `documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 6.2).
3. **C03 — No provenance leak (multi-source family, P4-T.4).**
   `test_multi_source_frozen_transformation_does_not_leak_training_identities`.
4. **C04 — Anti-cheating probes hold (Gate E, SELECTION_MAPPING).** The mechanism
   refuses rather than fabricates a transformation when trained on adversarial data:
   `test_selection_mapping_rejects_a_contradictory_mapping_rather_than_forcing_one`,
   `test_selection_mapping_rejects_a_constant_target_not_derived_from_source`,
   `test_selection_mapping_rejects_a_per_row_varying_but_structurally_unrelated_target`.
5. **C05 — Hypothesis selection is honest (P4-T.3).** A genuine tie at the best
   complexity rank is exposed as `AMBIGUOUS_SELECTION`, never guessed:
   `test_select_hypothesis_exposes_ambiguity_for_symmetric_tied_families`. A genuine
   unique lowest-rank hypothesis is retained even when a higher-rank alternative also
   exists: `test_select_hypothesis_retains_a_unique_lowest_rank_hypothesis`,
   `test_select_hypothesis_prefers_lower_rank_over_a_coexisting_higher_rank_alternative`.
6. **C06 — Locked benchmark v0.1 is genuinely blind and matches its witness 7/7.**
   The witness module is never imported at module scope
   (`test_witness_module_is_not_imported_at_module_scope`) and is dynamically absent
   from `sys.modules` at the moment predictions are committed
   (`test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed`);
   all 7 locked cases match the witness on outcome, and every case with an expected
   prediction matches it structurally
   (`test_run_locked_benchmark_matches_witness_on_every_case`, in
   `tests/test_p4t_locked_benchmark_v0_1.py`).
7. **C07 — Locked benchmark v0.2 (real P4-T.3 integration) is genuinely blind and
   matches its witness 6/6.** The runner discovers its own position pairs via
   `discover_all_hypotheses()`/`select_hypothesis()` rather than being told them by
   the cases file; the case built to have 2+ valid hypotheses with a unique winner
   genuinely does (`test_v2c03_genuinely_has_more_than_one_hypothesis_before_selection_narrows_it`),
   and the case built to have a genuine tie genuinely does
   (`test_v2c04_genuinely_has_a_tie_at_the_best_rank`); all 6 locked cases match the
   witness (`test_run_locked_benchmark_matches_witness_on_every_case`, in
   `tests/test_p4t_locked_benchmark_v0_2.py`).
8. **C08 — Committed predictions are deterministic across runs.** Re-running the
   locked benchmark produces byte-identical predictions (timestamp aside) both for
   v0.1 and v0.2 (`test_committed_predictions_file_is_written_and_deterministic_across_runs`
   in both locked-benchmark test files).
9. **C09 — Emergent structure is verified novel, never fabricated (P4-T.5).** A
   frozen transformation applied to a genuinely unseen operand produces a structure
   independently verified as novel
   (`test_projection_applied_to_a_genuinely_novel_operand_creates_emergent_structure`);
   an exact duplicate of an already-observed structure is correctly refused as novel
   (`test_exact_observed_structure_is_not_claimed_novel`); a pattern-based family
   given an incompatible single operand fails closed to `NO_PREDICTION` rather than
   fabricating a structure
   (`test_pattern_based_family_with_a_single_operand_fails_closed_not_created`).
10. **C10 — ROI adapter is honest (P4-T.6).** `score_hypothesis_roi()` reuses
    E20-D.19's decision constants completely unchanged
    (`test_score_hypothesis_roi_reuses_e20d19_decision_constants_unchanged`); its cost
    figure is real and never zero
    (`test_score_hypothesis_roi_cost_is_real_and_never_zero`); it never fabricates a
    historical match to inflate novelty, and correctly drops novelty to zero only for
    a genuine historical match
    (`test_score_hypothesis_roi_is_novel_without_a_historical_match`,
    `test_score_hypothesis_roi_drops_to_zero_for_a_genuine_historical_match`).

## Anti-cheating constraints

- Do not add semantic dictionaries, relation names, domain rules, or hidden thresholds
  to any file listed under "Frozen file hashes".
- Do not modify `kernel2.py`, `e20d_protocol.py`, or `e20d_cognitive_control_v0_1.py` —
  P4-T is required to reuse these completely unmodified (see
  `documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 2 and Sec. 7.1).
- Do not replace test inputs with expected outputs, or hand-construct a
  `FrozenTransformation`/`SelectionResult`/`PathRecord` to stand in for the actual
  mechanism's output when checking C01-C10.
- Do not inspect `p4t_locked_benchmark_witness_v0_1.py`/`_v0_2.py` manually and then
  claim the locked benchmark ran blind — the point of C06/C07 is that the MECHANISM's
  own code never imports the witness before commit, verified statically (AST) and
  dynamically (`sys.modules`); reading the witness file yourself to sanity-check the
  numbers afterward is fine (and expected, for your report), but do not alter the
  runner or cases files to reference it earlier.
- Do not tune any complexity-rank or ROI constant to force a specific outcome — the
  critical suite does not test threshold tuning; it tests whether the existing fixed
  thresholds behave honestly on the fixed locked corpus.

## Required report

- OS and Python version;
- command executed;
- git commit hash of the checkout;
- raw test output for the critical suite (the 4-file command above) and the full
  suite;
- PASS/FAIL per critical case (C01-C10);
- confirmation of no file modification;
- confirmation that `python -m pytest -q` (full suite) is zero-regression;
- any discrepancy with this document.

## Known, already-disclosed limitations (not discrepancies to (re)discover)

- P4-T is **structural transformation induction from paired examples**, not
  **autonomous relation discovery in an unstructured graph** — the mechanism is told
  which `(source, target)` pairs exist at training time; it never discovers that a
  relation exists in the first place. This is the project's own stated distinction
  (`STRUCTURAL_TRANSFORMATION_INDUCTION` vs `AUTONOMOUS_DISCOVERY_GENERAL`), not
  something to flag as a gap.
- Only four transformation families are covered (REFERENCE-EQUALITY / PERMUTATION /
  RECURSIVE / SELECTION, including multi-source selection and composition of
  selections) — a genuinely semantic function (e.g. arithmetic over opaque values) is
  rejected by design, verified by the anti-cheating probes (C04), not merely assumed.
- P4-T.5's emergent-structure novelty check does not extend to the pattern-based
  families (`COMPARE_PERMUTATION`, `COMPARE_RECURSIVE`) beyond correctly failing
  closed on incompatible operand counts — extending genuine novelty verification to
  those families is unstarted, documented as a real scope boundary in
  `documentation/P4T5_Emergent_Structure_V0_1.md`, not a silent omission.
- P4-T.6's ROI adapter still requires the caller to supply `gain_attendu` (expected
  gain) — exactly like E20-D.19 itself already does; no automatic gain estimation
  exists anywhere in this pipeline.
- Hypothesis selection is currently purely structural (lowest complexity rank);
  cost/ROI-weighted selection is not yet integrated into `select_hypothesis()` itself.
- The two locked benchmarks (v0.1: 7 cases, v0.2: 6 cases) are small, hand-authored
  corpora, not a large-scale held-out dataset — the same honest scale disclosure
  already made for M6 v0.1's own small holdout.

## Governance rule

P4-T (Gates A-G, both locked benchmarks, P4-T.5 emergent structure, P4-T.6 ROI
adapter) `= PASS_INDEPENDENT_SCOPE` only if all ten critical cases pass, the
repository remains unmodified, and the full suite stays at zero regression. **A local
PASS does not close the independent gate** — this protocol has so far only been
self-executed during development (see the self-execution note in
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.2, item 7, and
`release_manifest.json`'s `p4t7_thirdparty_validation_protocol_*` entry), exactly the
same rule already applied to M6 and M7 (`JOURNAL_DE_BORD.md`). **Closing this gate is
a decision for the project owner (Bacem Ben Soui), made only on the basis of a
genuinely external execution** — no session of this assistant may self-declare
closure, and no simulated or self-administered "external" run counts, echoing the
lesson already learned from the Phase-2 P1 annotation gate (an annotator who is the
project owner, however careful, is not a fully independent third party, see
`documentation/P1_GATE_HUMAN_ANNOTATION_RESULT_2026-09-15.md`'s own methodological
reserve).

## Scientific non-closure

Even if all critical cases pass, this protocol does not establish:

- that E20-D's gate is closed (P4-T's own design document is explicit: "ce document
  ne prétend pas fermer E20-D");
- that P4-T amounts to general unsupervised relation discovery, rather than
  transformation induction from paired examples;
- that the four covered transformation families exhaust what a genuinely emergent
  structural mechanism should support;
- readiness to extend P4-T.5's novelty verification to pattern-based families;
- readiness for automatic (rather than caller-supplied) ROI gain estimation;
- production readiness.
