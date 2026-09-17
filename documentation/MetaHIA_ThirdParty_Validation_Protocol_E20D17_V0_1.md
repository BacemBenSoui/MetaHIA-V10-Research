# MetaHIA — Third-party validation protocol E20-D.17 V0.1

## Goal
Independently verify that a reified operation can generate a structurally new
K3 node on novel operands, while preserving reference identity, provenance,
and semantic agnosticism.

## Blind input
Use the supplied test module without changing the kernel or adding semantic
rules.

## Required cases
1. Generated structure absent from observations -> CREATED_EMERGENT.
2. Same operation reused on different operands -> distinct structures.
3. Opaque/semantically strange output remains valid as structure.
4. Novelty is determined structurally, not through payload semantics.
5. Exact observed structure -> NOT_NEW.
6. Provenance preserved.
7. Trace contains operation identity and novelty verdict.
8. Result remains an ordinary K3 OBSERVATION node.

## Anti-cheating constraints
Do not add relation dictionaries, semantic labels, domain rules, or external
truth judgments. Do not change NodeRef identity rules.

## Expected independent report
- execution command;
- environment/runtime;
- individual case verdicts;
- unexpected failures/warnings;
- hash of `kernel2.py` used;
- confirmation that the kernel was unmodified during the validation.

## Consolidation rule
E20-D.17 remains PASS_MICROSTRUCTURAL locally until an independent execution
reproduces the eight targeted results. Independent validation is additive and
does not replace the local regression suite.
