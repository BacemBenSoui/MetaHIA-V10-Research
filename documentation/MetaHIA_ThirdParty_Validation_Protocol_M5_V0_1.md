# MetaHIA — Third-party Validation Protocol — M5 v0.1

## Purpose

Blind independent validation of the dynamic metacognitive controller.

## Required environment

- Fresh extraction of the package.
- Do not modify any supplied file.
- Python 3.11+ recommended.
- Run exactly:

```text
python -m pytest -q
```

## Critical contract

The evaluator must verify that M5:

1. is deterministic for identical context and identical policy history;
2. changes its policy only after observations;
3. can adapt after positive realized utility;
4. becomes conservative after persistent negative drift;
5. can issue `REQUEST_EVIDENCE` under high uncertainty when evidence is available;
6. can emit `CHANGE_STRATEGY` after poor historical usefulness;
7. does not inspect semantic labels to choose a decision;
8. reproduces identical policy state under replay;
9. makes dynamic cost/gain observable against an external exhaustive baseline;
10. remains conservative with empty history.

## Anti-cheating constraints

Do not add semantic dictionaries, relation names, domain rules, hidden thresholds, or corpus-specific decision overrides.

Do not change `kernel2.py`.

Do not replace test inputs with expected outputs.

## Required report

- OS and Python version;
- pytest version;
- command executed;
- raw test output;
- PASS/FAIL per critical case;
- package hash;
- `kernel2.py` hash;
- M5 module hash;
- confirmation of no file modification;
- semantic leakage scan result;
- repeatability result;
- dynamic-vs-exhaustive metrics;
- any discrepancy.

## Governance rule

`M5 = PASS_INDEPENDENT_SCOPE` only if all critical assertions pass, the package remains unmodified, the rerun is reproducible, and no semantic leakage is found.

This is a controller validation, not a proof of general cognitive superiority.
