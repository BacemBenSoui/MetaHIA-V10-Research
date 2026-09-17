# MetaHIA — Third-party validation protocol M4 v0.1

## Purpose

Independently verify the cold-start/evidence contract without changing the supplied implementation, adding semantic rules, or substituting gold labels for evaluation output.

## Required command

```bash
python -m pytest -q
```

## Environment report

The evaluator must report OS, Python version, pytest version, execution path and package hash.

## Required checks

1. Human evidence cannot be declared grounded direct/analogy.
2. System or M1-derived sources cannot count as independent evidence.
3. Independent groups deduplicate correctly.
4. `UNKNOWN` is preserved when no evaluator changes state.
5. Level A evidence can be insufficient and escalate to Level B/C.
6. Level C records human provenance as `UNGROUNDED_HUMAN`.
7. Analogy and direct provenance remain distinct.
8. `N_min` is measured over independent groups rather than raw duplicate records.
9. Acquisition attempts and transitions are auditable.
10. The same request/provider result is deterministic across repeated runs.

## Anti-cheating constraints

- no semantic relation dictionary;
- no ontology injection;
- no manual patch of expected results;
- no modification of the implementation under test;
- no use of gold outcome fields as evaluator output;
- no post-hoc editing of traces before reporting.

## Mandatory report

- command executed;
- runtime/environment;
- package hash;
- test output;
- pass/fail per critical case;
- repeatability result;
- changed files, if any;
- semantic leakage findings;
- conclusion and unresolved observations.

## Governance

Local PASS is not equivalent to scientific closure. M4 can be promoted to `PASS_INDEPENDENT_SCOPE` only after an external execution reproduces all critical checks on the frozen package.
