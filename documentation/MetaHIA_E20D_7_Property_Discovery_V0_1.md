# MetaHIA — E20-D.7 — Structural Operator-Property Discovery v0.1

## Objective
Test whether an operator property can be **generated from observed behaviour**, rather than supplied as `COMMUTATIVE`, `ITERATIVE`, etc.

## Principle
The input corpus contains only:
- operator references;
- operand references;
- observed outputs;
- case identifiers.

The mechanism derives generic structural invariants such as:
- arity;
- fixed-point/reference preservation;
- output invariance under a discovered position swap.

The mechanism does **not** assign a semantic interpretation to these invariants.

## Result
Targeted suite: **7/7 PASS**.

Interpretation: `PASS_MICROSTRUCTURAL`.

This does **not** yet prove semantic identification such as `+` = addition or `×` = multiplication, nor does it prove that an emergent property corresponds to a known mathematical axiom. It demonstrates only the structural generation and reification of a property-like invariant from behavioural evidence.

## Governance
- Generated property objects keep their own references.
- Structural equality and reference equality remain distinct.
- Ambiguous/no-evidence situations fail closed.
- No core M1 primitive was added.


## Executed validation

- Targeted tests: **7/7 PASS**
- Full regression suite: **52/52 PASS**
- Input semantic property labels: **none**
- M1 kernel modified: **no**

## Interpretation

The experiment demonstrates that a property-like invariant can be **generated and reified from behaviour alone**, while remaining semantically uninterpreted. This is the required bridge toward an open operator space.

The next unresolved question is stronger: can several independently discovered invariants be structurally compared, composed, and used to identify an existing operator/property family or generate a new one, with contradiction and ambiguity handled explicitly?
