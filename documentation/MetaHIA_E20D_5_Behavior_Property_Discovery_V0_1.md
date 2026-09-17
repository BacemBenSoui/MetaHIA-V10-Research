# MetaHIA — E20-D.5 — Behavioral / Property-to-Operator Discovery v0.1

Date: 2026-09-16

## Objective

Test the transition from an observed relation between operators to an operator relation inferred from structural behaviour, without interpreting operator labels semantically.

Target chain:

```text
S1, S2 / behaviour witnesses
        ↓
structural behavioural relation
        ↓
R'(O1,O2)
        ↓
reified relation object *R
        ↓
existing relation identification OR new relation object
```

## Implemented mechanism

A behaviour witness is an opaque structural observation whose first child is the target operator and whose nested structure can contain repeated references to that operator.

The discovery mechanism:

1. extracts the source operator reference from the source observation;
2. extracts the witness operator reference from the witness root;
3. recursively counts occurrences of the witness operator reference using reference identity;
4. requires a stable repeated occurrence pattern across at least three witnesses;
5. fail-closes when occurrence counts disagree or the target operator is not recursively embedded;
6. reifies the discovered relation as a `RefObject` while preserving reference identity independently from structure.

No interpretation of `+`, `*`, or any other label is performed.

## Example

Observed behavioural witnesses can have the structural form:

```text
*(A,B)  →  +(A, +(A, A))
*(C,D)  →  +(C, +(C, C))
*(E,F)  →  +(E, +(E, E))
```

The current mechanism does **not** conclude "multiplication is repeated addition". It discovers only the structural fact that the target operator `+` is recursively embedded in the witness with a stable count, yielding a relation object structurally connecting `*` and `+`.

## Results

Targeted tests: **10/10 PASS**.

Full regression suite: **38/38 PASS**.

Compilation/import: PASS.

## What is demonstrated

- behavioural evidence can produce an operator-level relation without the relation being supplied as an input fact;
- the relation is reified as a reference-bearing structural object;
- reference identity and structural equality remain separated;
- repeated structural behaviour can be carried forward to the operator-space layer;
- contradictions in the observed behavioural pattern fail closed.

## What is NOT demonstrated

This step does not yet derive a mathematical law from opaque behaviour in the strong sense of identifying a general function `f(O1,O2)`.

It also does not yet prove that a discovered relation such as `* -> +` is best explained by a specific semantic property such as iteration. That would require a further generic search over structural transformations/properties and a holdout validation mechanism.

## Governance status

`E20-D.5 = PASS_MICROSTRUCTURAL`.

`E20-D = OPEN`.

No modification of M1 v0.4 is justified by this result.

## Architectural consequence

The current E20-D chain is now:

```text
R(S1,S2)
  ↓
R'(O1,O2)
  ↓
behavioural evidence
  ↓
structural relation object *R
  ↓
operator-space identification / construction
```

The next scientific question is whether MetaHIA can search the space of candidate structural properties/compositions and discover an explanatory operator construction rather than only a behavioural relation.
