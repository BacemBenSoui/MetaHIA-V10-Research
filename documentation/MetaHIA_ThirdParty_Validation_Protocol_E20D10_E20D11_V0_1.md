# MetaHIA — Third-Party Validation Protocol
## E20-D.10 / E20-D.11 Graph and Path Discovery

### Purpose

Blind external validation of the graph/path layer on synthetic adversarial data and the supplied family-tree case. The evaluator must receive the code and corpus but no expected verdicts beyond this protocol.

### Test A — Linear chain

Input:

`R(A,B)`
`R(B,C)`
`R(C,D)`

Expected structural observations:

- a 3-step path A→D is discoverable;
- operator sequence is `[R,R,R]`;
- provenance is preserved;
- no semantic name is assigned to the path.

### Test B — Reverse traversal

Input:

`R(A,B)`

Query B→A with reverse traversal enabled.

Expected: one path with operator `R` and direction `REVERSE`.

Failure condition: inventing an operator named `inverse(R)` or equivalent without explicit evidence.

### Test C — Same payload / different reference

Construct distinct NodeRefs `A1` and `A2` with externally equal payloads.

Expected: they remain distinct structural nodes.

### Test D — Provenance

Use a path spanning observations `r1,r2,r3`.

Expected: path provenance is exactly `(r1,r2,r3)` in traversal order.

### Test E — No semantic filtering

Use arbitrary opaque operators and nodes, including a structurally odd path.

Expected: the path remains discoverable if structurally valid; no semantic rejection is allowed.

### Test F — Family-tree supplied case

Facts:

`FRERE_DE(David,Sonia)`
`MERE_DE(Sonia,Alice)`
`AGE(Alice,18)`
`POSSEDE(David,Moto)`

Expected paths:

1. Sonia→Moto: `REVERSE(FRERE_DE)` then `FORWARD(POSSEDE)`.
2. David→18: `FORWARD(FRERE_DE)`, `FORWARD(MERE_DE)`, `FORWARD(AGE)`.

The evaluator must report the paths structurally, without assigning family semantics.

### Test G — Bounded exploration

Verify `max_depth` and `max_paths` only limit enumeration and never alter the definition of a valid discovered step.

### Required external report

The third party should return:

- exact code revision/hash tested;
- Python version and OS;
- raw test output;
- PASS/FAIL per case;
- any discrepancy between expected structural behavior and observed behavior;
- any hidden semantic assumption detected in the implementation.

The report must not modify the expected results silently; deviations must be explicitly flagged.
