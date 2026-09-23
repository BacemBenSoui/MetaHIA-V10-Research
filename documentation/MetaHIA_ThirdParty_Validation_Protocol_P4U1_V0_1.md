# MetaHIA — Third-party Validation Protocol — P4-U.1 Unsupervised Compositional Pattern Discovery v0.1

## Purpose

Blind independent validation of P4-U.1's unsupervised compositional pattern
discovery mechanism (Gate A/B unchanged from v0.2,
`p4u1_unsupervised_pattern_discovery_v0_1.py`; Gate C redefined as a
set-valued replay in v0.3, `p4u1_set_valued_replay_v0_1.py`) and its locked
train/holdout/witness benchmark (`p4u1_locked_benchmark_runner_v0_1.py`,
U1/U2/U3).

This follows the same pattern already established for M6, M7, and P4-T.7 —
see `MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md`,
`..._M6_NonDegenerate_V0_2.md`, `..._M7_V0_1.md`, and
`..._P4T_V0_1.md`, all of which stay frozen and unaffected by this protocol.

**Two commits matter here, deliberately distinguished so you never
validate a different benchmark state than the one these hashes were
frozen from:**

```text
3e3c21b83aec22e6ed852e862ece378f2f569df7 = benchmark artifact commit
    (the exact state of the 6 files hashed below: the locked benchmark
    was built, calibrated, and run BLIND at this commit -- this is the
    commit the "Frozen file hashes" table and the 7/7 result in
    documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md
    Sec. 20 refer to)

HEAD of the branch you cloned (any commit at or after 3e3c21b that
    contains THIS FILE) = documentary package -- this protocol itself,
    plus governance-decision text, journal entries, and the
    repository-wide hash manifest, none of which touch any of the 6
    frozen files. Several purely documentary commits sit between
    3e3c21b and the tip of `main` (visible in `git log`); none of them
    change the 6 files below -- verified below, not assumed.
```

**Clone at the tip of `main`** (or whatever commit your source hands
you, as long as it contains this file) — do **not** clone at `3e3c21b`
alone, since that commit does not yet contain this protocol document.
Verified directly, not merely asserted, at the time this protocol was
written: the 6 files in "Frozen file hashes" below are BYTE-IDENTICAL
between `3e3c21b` and the commit you are reading this file from
(`git diff 3e3c21b83aec22e6ed852e862ece378f2f569df7 HEAD -- kernel2.py
p4u1_unsupervised_pattern_discovery_v0_1.py p4u1_set_valued_replay_v0_1.py
p4u1_locked_benchmark_cases_v0_1.py p4u1_locked_benchmark_witness_v0_1.py
p4u1_locked_benchmark_runner_v0_1.py` produces zero output) — so cloning
at the tip and verifying the hashes below is exactly equivalent to
verifying the benchmark's original construction commit. This is exactly
the check required in your report (see "Required report" below) — run
it yourself and confirm it is still empty for YOUR checkout before trusting the
hashes below, since a later commit could in principle touch these
files (none currently do, but this protocol does not ask you to take
that on faith beyond this one check).

## What this protocol does NOT ask you to validate

This is **not** a validation that the numeric thresholds
(`p4u1_locked_benchmark_cases_v0_1.GATE_PARAMS`) generalize to any graph
other than this specific locked benchmark, and **not** a validation of
general autonomous relation discovery. P4-U.1's own protocol document
already discloses, without prompting, that it discovers COMPOSITIONS on a
graph whose relations are already labeled — it is explicitly not
`P4-U.2` (undefined future work: discovery of unknown relations). It is
also, by the project owner's own explicit decision after reviewing this
same benchmark, **not yet closed even at the mechanism level**: the status
retained is `MECHANISM VALIDATED ON LOCKED SELF-ADMINISTERED BENCHMARK /
GENERALIZATION OPEN`, precisely because the thresholds and the witness were
calibrated and frozen inside the same experimental environment your
execution is meant to test independence from. Your task is to confirm
that the discover→Gate B→freeze→set-valued-replay→Gate C→commit→reveal
pipeline is **honest, non-circular, and reproducible** in its deterministic
parts on a fresh checkout — not a judgment on whether P4-U.1 generalizes to
an unknown graph.

## Required environment

- Clone `https://github.com/BacemBenSoui/MetaHIA-V10-Research` at the commit
  this protocol ships in (report the exact commit hash used:
  `git rev-parse HEAD`).
- Do not modify any file in the repository.
- Python 3.11+ recommended.
- **No network access, no LLM/Ollama, no external service of any kind is
  required or used anywhere in this protocol.** Every mechanism under test
  here is deterministic Python with no I/O beyond writing one JSON
  prediction file (`validation/p4u1_locked_benchmark_predictions_v0_1.json`).
  This claim covers ONLY the two commands below, both of which pass
  `-k "not live"` deliberately — the repository also contains 10 unrelated
  M7 tests (`tests/test_m7_*_live_demo_v0_1.py`) that attempt real
  Ollama/LAN calls; they have nothing to do with P4-U.1 and are excluded
  by this filter, exactly like every other locked-benchmark protocol in
  this project (M6/M7/P4-T.7) already does for its own critical suite. Do
  **not** drop `-k "not live"` — a first verification pass of this exact
  package, done directly by this session before sending it, found that
  running the bare `python -m pytest -q` (no filter) collects those 10
  live tests too and took **28 minutes** in an environment that happened
  to reach a reachable LLM backend; in an environment without one, they
  would very plausibly hang far longer on connection timeouts instead of
  failing fast. Their outcome (pass, fail, or hang) says nothing about
  P4-U.1 either way.
- **Runtime warning, disclosed explicitly so you do not mistake it for a
  hang**: the locked-benchmark test file computes a real 200-replicate
  null-max distribution for TRAIN and HOLDOUT across all three cases — on
  the development machine this took **~2.5-3 minutes** for the critical
  suite alone, and about the same again for the full suite (both commands
  below re-run the locked benchmark from a clean `sys.modules` state, per
  its own test fixture design). This is a genuine, measured computation
  cost (see
  `documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`
  Sec. 3 for why `max_paths` is capped at 1000 rather than left unbounded),
  not an infinite loop.
- Run exactly, from the repository root:

```text
python -m pytest -q tests/test_p4u1_unsupervised_pattern_discovery_v0_1.py tests/test_p4u1_set_valued_replay_v0_1.py tests/test_p4u1_locked_benchmark_v0_1.py
```

Then, for full-suite zero-regression confirmation (~3 minutes, same
reason — and note the same `-k "not live"` filter, for the reason
explained above):

```text
python -m pytest -q -k "not live"
```

## Frozen file hashes (SHA-256)

| File | SHA-256 |
|---|---|
| `kernel2.py` | `c76adfd2eed8e3ba6022200e7eba6c381f262602f626850cd80af65a0efc9aa9` |
| `p4u1_unsupervised_pattern_discovery_v0_1.py` | `05604555c5ac48bab478994ff55670f2947d77bbc05c5acd36abfddbe84aaf9e` |
| `p4u1_set_valued_replay_v0_1.py` | `3f2d0c1b6901dd22681ded50abb5be3c3e30a71ec7804f0d4f88b5768833ebbb` |
| `p4u1_locked_benchmark_cases_v0_1.py` | `f6e5ab9beec33df717214280cce48ddccff22c3e0d2420ebd24565fd2eafdec8` |
| `p4u1_locked_benchmark_witness_v0_1.py` | `d84929bf236e4d6369976c0eb89f37abebe4917108c4ee384fb4f7662c6f8c93` |
| `p4u1_locked_benchmark_runner_v0_1.py` | `fe2c2f1cb6bef5c8e82bb22eb6e45967a420b5bd526d3c6807030bb901ed586a` |

`kernel2.py`'s hash is unchanged from the M6/M7/P4-T protocols (same file,
same commit history — P4-U.1 reuses it completely unmodified, see the
Governance/Anti-cheating sections below). `.gitattributes`
(`* text=auto eol=lf`) is already in place repo-wide, so a plain
`git clone` on any OS reproduces these hashes directly.

## Critical contract

The evaluator must verify that:

1. **C01 — Wedge exclusion is precise, not overbroad.** Same-relation
   "wedge" skeletons (a path that walks one relation backward then
   immediately forward again) are excluded from candidacy, but a genuine
   two-relation composition with a reversed step is still discovered:
   `test_discover_candidates_excludes_trivial_same_relation_wedges`,
   `test_discover_candidates_keeps_genuine_two_relation_reverse_traversal`
   (`tests/test_p4u1_unsupervised_pattern_discovery_v0_1.py`).
2. **C02 — Gate B's rejection reason is always the FIRST violated
   condition, in a fixed order (depth, then absolute threshold, then
   null-significance).** `test_gate_b_rejects_below_min_depth_even_with_high_support`,
   `test_gate_b_rejects_below_s_min`, `test_gate_b_rejects_not_null_significant`.
3. **C03 — The null model's disclosed, weaker-than-exact-degree
   guarantee holds exactly as documented**: no entity outside the
   original per-label pool is ever introduced, no self-loop is ever
   created, and results are deterministic per seed.
   `test_null_generator_never_introduces_an_entity_outside_the_original_pool`,
   `test_null_generator_never_creates_a_self_loop`,
   `test_null_generator_is_deterministic_per_seed`.
4. **C04 — `FrozenPatternU1` is leak-free and its digest is deterministic
   and skeleton-specific.** `test_freeze_pattern_never_carries_training_identity_fields`,
   `test_freeze_pattern_digest_is_deterministic_and_skeleton_specific`.
5. **C05 — The central resolution this v0.3 revision exists for.** On the
   SAME hub corpus, `kernel2.replay_path_pattern_holdout()` (UNMODIFIED)
   reports `AMBIGUOUS` while the new set-valued adapter correctly reports
   `REPLICATED=True` — decided purely structurally, never by consulting
   which branch is correct.
   `test_hub_with_multiple_valid_continuations_is_replicated`,
   `test_legacy_status_is_ambiguous_at_the_same_hub_where_the_adapter_says_replicated`
   (`tests/test_p4u1_set_valued_replay_v0_1.py`).
6. **C06 — Anti-circularity of the set-valued replay adapter (protocol
   v0.3 Sec. 10.5).** None of its public functions accept a witness,
   label, or other ground-truth hint.
   `test_replay_set_valued_signature_never_accepts_a_witness_or_ground_truth`.
7. **C07 — The co-reference (`position_groups`) check is real and
   correctly discriminating when exercised directly**, even though it is
   currently unreachable via the standard discovery pipeline (see "Known,
   already-disclosed limitations" below — do not flag this as a
   discrepancy).
   `test_position_groups_satisfied_true_when_the_constrained_positions_genuinely_coincide`,
   `test_position_groups_satisfied_false_when_the_constrained_positions_differ`.
8. **C08 — The locked benchmark is genuinely blind, mechanically, not
   just by promise.** The witness module is never imported at module
   scope nor named anywhere in the discovery/commit functions, and is
   dynamically absent from `sys.modules` at the moment predictions are
   committed. `test_witness_module_is_not_imported_at_module_scope`,
   `test_discovery_and_commit_functions_never_mention_the_witness_module_by_name`,
   `test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed`
   (`tests/test_p4u1_locked_benchmark_v0_1.py`).
9. **C09 — All 7 declared candidates match the witness on Gate A/B/C,
   with real (non-borderline) margins on both the positive and the
   train-only-failure cases.**
   `test_run_locked_benchmark_matches_witness_on_every_declared_candidate`,
   `test_real_motif_clears_gate_b_and_gate_c_with_real_margin`,
   `test_decoy_train_only_clears_gate_b_but_fails_gate_c_at_zero_support`.
10. **C10 — Committed predictions are deterministic across runs.**
    `test_committed_predictions_file_is_deterministic_across_runs`.

## Anti-cheating constraints

- Do not add semantic dictionaries, relation names, domain rules, or
  hidden thresholds to any file listed under "Frozen file hashes".
- Do not modify `kernel2.py` — P4-U.1 is required to reuse
  `discover_paths()`, `generalize_path_pattern()`, and
  `replay_path_pattern_holdout()` completely unmodified (see
  `documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
  Sec. 4, Sec. 10.3-10.4, and the project's own governance rule that Gate B
  was deliberately left unchanged rather than adjusted to make Gate C
  easier).
- Do not replace test inputs with expected outputs, or hand-construct a
  `FrozenPatternU1`/`SetValuedReplayResult`/`CandidateSupport` to stand in
  for the actual mechanism's output when checking C01-C10.
- Do not inspect `p4u1_locked_benchmark_witness_v0_1.py` manually and then
  claim the locked benchmark ran blind — the point of C08 is that the
  MECHANISM's own code never imports the witness before commit, verified
  statically (AST/source-text) and dynamically (`sys.modules`); reading the
  witness file yourself afterward to sanity-check the numbers is fine (and
  expected, for your report), but do not alter the runner or cases files to
  reference it earlier.
- Do not tune `S_min`, `K_min`, `coverage_min`, `N_null`, or `max_paths` to
  force a specific outcome — the critical suite does not test threshold
  tuning; it tests whether the existing frozen thresholds
  (`p4u1_locked_benchmark_cases_v0_1.GATE_PARAMS`) behave honestly and
  reproducibly on the fixed locked corpus.
- Do not modify `discover_paths()` (or anything else in `kernel2.py`) to
  make `position_groups` reachable/non-trivial (C07) — this would be a new
  mechanism change requiring its own justification and protocol, not a fix
  applicable within this validation.

## Required report

- OS and Python version;
- command executed;
- git commit hash of the checkout (`git rev-parse HEAD`);
- output of `git diff 3e3c21b83aec22e6ed852e862ece378f2f569df7 HEAD --
  kernel2.py p4u1_unsupervised_pattern_discovery_v0_1.py
  p4u1_set_valued_replay_v0_1.py p4u1_locked_benchmark_cases_v0_1.py
  p4u1_locked_benchmark_witness_v0_1.py
  p4u1_locked_benchmark_runner_v0_1.py` (expected: empty — confirms your
  checkout's 6 frozen files match the benchmark's original construction
  commit, not just this protocol's own commit, see "Required
  environment" above);
- raw test output for the critical suite (the 3-file command above) and
  the full suite;
- PASS/FAIL per critical case (C01-C10);
- confirmation of no file modification;
- confirmation that `python -m pytest -q -k "not live"` (full suite) is
  zero-regression;
- any discrepancy with this document.

## Known, already-disclosed limitations (not discrepancies to (re)discover)

- P4-U.1 is **unsupervised discovery of COMPOSITIONS on a graph with
  already-labeled relations**, not **autonomous discovery of unknown
  relations** (`P4-U.2`, undefined future work) — the project's own stated
  distinction (`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
  Sec. 1), not something to flag as a gap.
- `position_groups` (the co-reference structure of a `FrozenPattern`) is
  real and correctly checked (C07), but `kernel2.discover_paths()`'s own
  no-revisit-within-a-path invariant means it can never produce a
  non-trivial (size >= 2) `position_groups` constraint for a candidate
  reached through the standard discovery pipeline — documented in full,
  including the honest reasoning, in
  `documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
  Sec. 10.7. `REPLICATED(start)` therefore reduces, with the data this
  pipeline can produce today, to existence of at least one
  skeleton-matching path — which still resolves the Gate B/Gate C tension
  this revision exists for (see C05), just without the co-reference
  refinement the field could add if a future path source allowed repeated
  positions. This is an open, non-blocking scientific point, not a defect
  to be silently patched by modifying `kernel2.py` (see the Anti-cheating
  constraints above).
- The numeric thresholds (`GATE_PARAMS`) and the three locked cases
  (U1/U2/U3) were calibrated and frozen by the SAME session/environment
  that also wrote this protocol — see
  `documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`
  for the full calibration record, disclosed rather than hidden. This is
  exactly the property this protocol exists to test independence from: a
  local PASS here (self-administered) has already been obtained and does
  not by itself establish that the thresholds are not overfit to their own
  construction.
- The corpus design (a "single-bridge" concentration: P parents converging
  on one node, Q children diverging from it) is a small, hand-authored
  synthetic structure, not a large-scale real-world graph — the same
  honest scale disclosure already made for M6 v0.1's and P4-T's own small
  locked benchmarks.
- Gate B is unchanged from v0.2; only Gate C's replay semantics changed in
  v0.3. If you find yourself wanting to question Gate B's statistical
  design (the max-statistic multiple-comparisons correction, Sec. 7), that
  critique applies to work already reviewed and frozen before this
  protocol and is out of scope here.

## Governance rule

P4-U.1 (Gate A/B unchanged, Gate C set-valued replay, locked benchmark
U1/U2/U3) `= PASS_INDEPENDENT_SCOPE` only if all ten critical cases pass,
the repository remains unmodified, and the full suite stays at zero
regression. **A local PASS does not close the independent gate** — this
protocol has so far only been self-executed during development (see
`JOURNAL_DE_BORD.md`'s 2026-09-23 entry on the locked benchmark run, and
`release_manifest.json`'s `p4u1_locked_benchmark_2026-09-23` entry), exactly
the same rule already applied to M6, M7, and P4-T.7. **Closing this gate is
a decision for the project owner (Bacem Ben Soui), made only on the basis
of a genuinely external execution** — no session of this assistant may
self-declare closure, and no simulated or self-administered "external" run
counts, echoing the lesson already learned from the Phase-2 P1 annotation
gate and reaffirmed at P4-T.7's own first (non-independent) round (see
`documentation/P1_GATE_HUMAN_ANNOTATION_RESULT_2026-09-15.md` and
`JOURNAL_DE_BORD.md`'s 2026-09-23 "Premier retour d'exécution P4-T.7"
entry).

Even after a genuinely independent PASS on this protocol, the retained
status is:

```text
P4-U.1 = MECHANISM VALIDATED ON LOCKED SELF-ADMINISTERED BENCHMARK
         (now independently reproduced) / GENERALIZATION OPEN
```

not `CLOSED` — see "Scientific non-closure" below.

## Scientific non-closure

Even if all critical cases pass, including a genuinely independent
execution, this protocol does not establish:

- that the frozen thresholds (`GATE_PARAMS`) generalize to any graph other
  than this specific locked benchmark's single-bridge design;
- that P4-U.1 amounts to general unsupervised relation discovery, rather
  than compositional pattern discovery on an already-labeled graph;
- that the co-reference (`position_groups`) refinement of Gate C would
  behave correctly if a future path source made it reachable — only that
  its isolated logic is correct today (C07);
- readiness to begin `P4-U.2` (undefined autonomous discovery of unknown
  relations) — that remains a separate scoping decision for the project
  owner, to be made after, not instead of, this validation;
- production readiness.
