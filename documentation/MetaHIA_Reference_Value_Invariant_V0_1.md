# MetaHIA — Reference/Value Invariant for Calculated Patterns V0.1

Date: 2026-09-16

## Scope

The experimental `kernel2.py` now applies the same reference/value separation used by `NodeRef` to calculated structural objects, including extracted Patterns and recursively composed structures.

Core representation:

```text
*P = f(*A, *B, ...)
```

Identity and denoted structure are separate:

```text
reference_equal(P1, P2)   -> same referenced object
structural_equal(P1, P2)  -> equivalent denoted kernel structure
```

A different reference may denote an identical structure. A different `NodeRef` remains a different structural identity even when an external payload system gives the references equal values.

## Kernel changes

- Added `RefObject(ref, structure)` as a kernel-owned referencable calculated object.
- Added `reference_equal()` for strong identity comparison.
- Added recursive `structural_equal()` for denoted kernel structures.
- Added `resolve_structure()` for explicitly resolving a `RefObject` to its kernel-owned structure; bare `NodeRef` remains non-dereferenceable inside the kernel.
- `compare()`, `compare_candidates()`, `apply()`, `is_applicable()` and `apply_pattern()` accept a `RefObject` where a kernel structure is expected and operate on its denoted structure.
- `_shape_template()` treats `RefObject` as an atomic reference at the current structural level, preserving the distinction between an object reference and inspecting that object's internals.
- No domain dictionary or property-specific detector was added.
- Production `M1 v0.4` and `structural/` remain untouched.

## Tests executed

Focused test suite: `tests/test_pattern_ref_invariant_v0_1.py`

Assertions: 19

Result: **PASS — all 19 assertions passed.**

Validated cases include:

1. same reference -> same identity;
2. distinct references -> distinct identity;
3. distinct references with identical denoted structure -> structural equality without identity equality;
4. distinct internal `NodeRef`s remain distinct even when external payload equality could occur;
5. repeated same `NodeRef` in E18 -> genuine coreference;
6. different `NodeRef`s in E18 -> no accidental coreference;
7. repeated same Pattern reference in a larger structure -> genuine structural reuse;
8. distinct Pattern references -> no accidental identity merge;
9. Pattern reference preserves `Apply` semantics;
10. recursive structure equality works over nested kernel structures;
11. E13 comparison/application regression;
12. E19 aggregate pattern and dependency guard regression;
13. `NodeRef` still contains only `ref_id`.

## Governance consequence

The following invariant is now explicit for E18/E19/E20-D and future recursive mechanisms:

> **R-V-1 — Reference/Value Separation:** structural identity MUST be represented by an explicit reference and MUST NOT be inferred from equality of external values. Structural equivalence may be tested separately from reference identity. The distinction MUST be preserved recursively for Nodes, Patterns, Transformations and MetaStructures.

For E20-D, this means that discovery of `(source_position, target_position)` pairs must operate over structural positions/references. Equal payloads may constitute evidence, but cannot by themselves create identity or coreference.

## Status

`NodeRef` + referencable calculated structures: **PASS_MICROSTRUCTURAL** for this experimental kernel spike.

This result does **not** close E20-D. The E20-D lock remains open until the generic cross-slot discovery pipeline can compare/merge the resulting transformations across the unified structural space with ambiguity, provenance and contradiction tests.
