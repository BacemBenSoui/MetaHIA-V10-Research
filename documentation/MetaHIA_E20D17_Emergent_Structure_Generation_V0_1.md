# MetaHIA — E20-D.17 — Emergent Structure Generation V0.1

## Purpose

D17 tests whether a structurally reified operation can generate a new K3
structure whose exact structural form is absent from the observed graph.

The test deliberately does **not** require semantic naming of the result.
The generated node can therefore be structurally valid and epistemically
unknown.

## Chain

`OperationalRelation -> DerivedOperation -> Apply -> NewStructure`

Input:
- a reference-bearing derived operation;
- one or more NodeRef operands;
- an optional observed set used only for novelty verification.

Output:
- an ordinary K3 `Node(OBSERVATION, ...)`;
- operation reference;
- operands;
- provenance;
- an explicit novelty verdict.

## Key invariant

`NewStructure != KnownStructure` is judged structurally, not semantically.
Reference identity remains separate from structural equality.

## Meaning

A result such as `OP::OPAQUE(Sonia, Moto)` is accepted as a valid generated
structure even if no human-readable interpretation is attached. This is a
core generativity test, not a semantic truth test.

## Scope

No change to the K3 ontology or M1 v0.4. The implementation is additive and
uses existing `apply_operator()`.
