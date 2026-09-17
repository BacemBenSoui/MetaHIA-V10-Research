# Third-party validation protocol — E20-D.12

## Blind objective
Verify that Path Pattern Generalization:
- uses only structural references, operators, directions and provenance;
- preserves repeated-reference constraints;
- does not merge distinct references because payloads might be equal;
- fails closed on incompatible path skeletons;
- does not attach semantic labels.

## Required cases
1. Two isomorphic paths with distinct NodeRefs.
2. Same-reference repetition in all examples.
3. Repetition in only one example — must NOT generalize as co-reference.
4. Different operator skeleton — must return `None`.
5. Different length — must return `None`.
6. Same path body reified under two PatternRefs — identities must remain distinct while structural bodies remain equivalent.
7. Family path pair `MERE_DE + reverse(ENFANT_DE)` — must produce an anonymous path pattern, not `GRANDPARENT`.
8. A deliberately odd path such as `reverse(FRERE_DE) + POSSEDE` — must be accepted structurally if constructible and remain semantically unnamed.

## Evidence to return
- exact kernel version/hash;
- test command and raw output;
- JSON trace for every case;
- PASS/FAIL per criterion;
- any discovered issue with reproduction steps.

## Important prohibition
Do not add semantic dictionaries or hand-written family rules during validation.
