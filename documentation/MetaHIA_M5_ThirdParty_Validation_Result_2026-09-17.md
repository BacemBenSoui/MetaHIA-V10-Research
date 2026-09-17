# MetaHIA — M5 Third-party Validation Result

Date: 17 September 2026
Status: PASS_INDEPENDENT_SCOPE
Source: result reported after independent execution by the external evaluator.

## Environment
- OS: Windows 11 Pro 10.0.26200
- Python: 3.13.14
- pytest: 9.1.1
- Command: `python -m pytest -q`
- Fresh extraction; no package modification

## Repeated execution
- Run 1: 26/26 PASS
- Run 2: 26/26 PASS
- Run 3: 26/26 PASS
- Repeatability: confirmed

## Frozen hashes
- kernel2.py: `987839172357c4b0e43e5d3d03dcda32825f4da817dbb02390a5bc4c3f9ea3d9`
- m5_metacognitive_dynamic_controller_v0_1.py: `e12961da38edb1661632e91d4e2cc8c69f9423a8ad140994c3fb8d1666504698`
- e20d_cognitive_control_v0_1.py: `e090f578ffa72adbc1a693748b879ca94967a63cb88a1eb1c13ccbaea6a15aba`
- Package hash: `906dcd6533dbf84d1bf5121d6a54a7b7f918758a5b5a5c846a21202b55eede38`

## Critical contract
All 10 requirements passed: determinism; observation-gated adaptation; positive-utility adaptation; conservative response to persistent negative drift; REQUEST_EVIDENCE; CHANGE_STRATEGY; semantic-label independence; replay identity; dynamic-vs-exhaustive observability; conservative empty-history baseline.

## Dynamic benchmark scenario
- dynamic_cost = 1.5
- exhaustive_cost = 4.0
- cost reduction = 62.5%
- dynamic_gain = 1.4
- exhaustive_gain = 2.0
- gain retained = 70%
- useful coverage = 2/2 = 100%

These figures describe the validation scenario only; they are not a generalized performance claim.

## Semantic leakage / integrity
- No semantic relation dictionary detected in M5 module.
- No corpus-specific decision override detected.
- No file difference between fresh extraction and executed package.
- Python compilation: PASS.

## Governance consequence
M5 is promoted to `PASS_INDEPENDENT_SCOPE`. This validates the controller contract on the tested scope; it does not prove general cognitive superiority, nor close the broader E20-D discovery program.
