# MetaHIA — E20-D.12 Path Pattern Generalization v0.1

## Objective
Generalize multiple discovered `PathRecord` objects into one anonymous structural `PathPattern` without semantic labels, domain rules, or value-based identity.

## Input réel
A set of at least two `PathRecord` instances produced from the structural graph layer.

Each path contains:
- ordered `NodeRef` sequence;
- ordered operator sequence;
- traversal directions;
- provenance.

## Compatibility contract
A group is generalized only when:
1. at least two paths are provided;
2. all paths have the same length;
3. operator/direction skeletons are structurally equal;
4. repeated-reference constraints are retained only if they hold in every path.

Any incompatible condition returns `None` (fail closed).

## Output théorique
A `PathPattern` contains:
- anonymous node-position bindings;
- position groups proving co-reference;
- operator sequence;
- direction sequence;
- source path identifiers;
- provenance.

Example:

`Amanda -> MERE_DE -> David <- ENFANT_DE <- Lucas`

and

`Amanda -> MERE_DE -> David <- ENFANT_DE <- Emma`

produce the anonymous structural pattern:

`VAR0 --MERE_DE/FORWARD--> VAR1 <--ENFANT_DE/REVERSE-- VAR2`

No label such as `GRANDPARENT` is assigned.

## R-V-1 discipline
Node identity is reference-based. Equal payloads are irrelevant to identity. Co-reference is inherited only from explicit reference equality inside every source path.

## Scope limit
D12 does not yet discover cross-example constants such as `Amanda` being shared as a source, nor does it synthesize a new operational relation from the path pattern. Those belong to later path-property and operational-discovery stages.

## Validation
- Targeted D12 tests: 8/8 PASS.
- Full repository regression after this change: 76/76 PASS.
- Compilation: PASS.
- Real family trace: `tests/E20D12_FAMILY_REAL_TRACE_2026-09-17.json`.

## Governance
Status: `PASS_MICROSTRUCTURAL`.

This does not close the global E20-D program. The next required step is extraction of structural properties from generalized path patterns and subsequent operational relation discovery.
