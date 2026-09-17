# MetaHIA — E20-D Executable Protocol v0.2

Date: 2026-09-16
Status: EXECUTABLE MICROSTRUCTURAL PROTOCOL
Governance status of E20-D: OPEN

## 1. Objective

Operationalize E20-D as a replayable experiment that enumerates ordered
`(source_position, target_position)` pairs and attempts to discover a
structural transformation using only the existing generic kernel mechanisms.

The protocol must preserve the architectural invariant:

`Reference identity != structural equivalence != external value equality`

No semantic dictionary or domain-specific transformation detector is allowed.

## 2. Implemented chain

Observation corpus
-> enumerate ordered source/target positions
-> build source and target structural columns
-> check exact reference identity row-by-row
-> otherwise call the generic Compare mechanism
-> retain only unique structural permutation
-> wrap discovered transformation in RefObject
-> attach evidence/provenance
-> replay on an unseen corpus where the transformation is executable.

## 3. Reference/value discipline

The protocol never uses equal external payloads as identity.

A direct dependency is accepted only when, for every evidence row:

`reference_equal(source_ref, target_ref) == True`

Distinct references are never merged merely because an external system could
assign them equal payloads.

## 4. Ambiguity contract

`compare_candidates()` is used whenever ambiguity must be inspected.

If more than one structural permutation is possible, E20-D records the pair
under `ambiguous_pairs` and does not create a candidate.

No enumeration-order choice is accepted as evidence.

## 5. Current demonstrated scope

The executable protocol demonstrates two structural classes:

1. `REFERENCE_EQUALITY`
   - same NodeRef identity at source and target positions for all evidence rows.

2. `COMPARE_PERMUTATION`
   - target column is a uniquely identifiable permutation of source column,
     discovered through the generic Compare mechanism.

This does **not** prove identification of arbitrary functions from finite
opaque observations. Such identification remains an open problem and is not
silently approximated.

## 6. Tests

`tests/test_e20d_v02.py`

7/7 PASS:

- reference equality discovery
- same-value/different-reference non-fusion
- generic Compare permutation discovery
- unseen replay of permutation
- ambiguity is not forced
- mechanical provenance
- distinct PatternRef / same structure

Existing PatternRef/NodeRef suite:

`tests/test_pattern_ref_invariant_v0_1.py`

19/19 PASS.

## 7. Governance decision

E20-D remains `OPEN` because the current executable protocol has not yet shown
that arbitrary cross-slot transformations can be discovered and unified in one
representation. In particular, generic PATTERN and SHAPE_PATTERN transformation
spaces are still internally distinct.

What is closed by this step:

- executable enumeration of source/target position pairs
- explicit reference/value separation in the protocol
- fail-closed ambiguity handling
- reifiable transformation references
- mechanical provenance path

What remains open:

- unified transformation representation across PATTERN/SHAPE_PATTERN
- generic transformation identification beyond permutation/reference equality
- adversarial corpus covering broader transformation families
- full provenance/information-conservation invariant

M1 v0.4 remains FROZEN.
