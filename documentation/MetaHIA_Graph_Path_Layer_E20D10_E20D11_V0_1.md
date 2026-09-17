# MetaHIA — Graph / Path Discovery Layer V0.1

## Scope

This extension preserves the K3 core hypothesis `Node / Apply / Compare`. The graph/path records are infrastructure views over already represented structures, not new ontological primitives.

## Structural contract

An observed binary relation is represented as:

`OBSERVATION(operator, source_ref, target_ref)`

and becomes an edge:

`source_ref --operator--> target_ref`

Traversal in the opposite direction is represented by the traversal flag `REVERSE`; the kernel does **not** invent an inverse operator.

## Path discovery

From a graph, the engine can enumerate simple paths up to a bounded depth. A path contains:

- endpoint references;
- ordered opaque operator sequence;
- explicit FORWARD/REVERSE directions;
- source observation provenance.

The depth and path-count bounds are exploration controls, not semantic rules.

## Structural properties

A path yields structural features such as length, number of distinct nodes, number of distinct operators, repeated-operator presence, reverse traversal, and graph degree at endpoints.

These features are descriptive only; no human semantic interpretation is attached.

## Reification

A path or a path-derived link can be wrapped in the existing `RefObject` mechanism:

`*P = path_structure`

`*L = link_structure`

Identity remains independent from denoted structure, preserving R-V-1.

## Family-tree smoke case

For the opaque facts:

- `FRERE_DE(David, Sonia)`
- `POSSEDE(David, Moto)`

starting at `Sonia`, the engine discovers the path:

`Sonia --REVERSE/FRERE_DE--> David --FORWARD/POSSEDE--> Moto`

No label such as “brother's motorcycle” is created by the core.

Likewise:

`David --FORWARD/FRERE_DE--> Sonia --FORWARD/MERE_DE--> Alice --FORWARD/AGE--> 18`

is discovered as a three-step anonymous structural path.

## Evidence status

- Graph/path core extension: **PASS_MICROSTRUCTURAL**
- Family smoke tests: **2/2 PASS**
- Full repository tests after modification: **68 passed** under `PYTHONPATH=.` + pytest
- Kernel compilation: **PASS**
- Independent third-party validation: **NOT YET DONE**

Kernel SHA-256: `052949f986008608687c2cf8131b73aaeb5942eeadd988f58aaaf4ef5492b3ee`
