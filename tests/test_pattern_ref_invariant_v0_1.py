from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import kernel2 as k


def obs(node_id, op, *args):
    # Kernel convention: children = operator, args..., output
    return k.Node(node_id, k.OBSERVATION, (op, *args, args[-1] if args else None))


def node(node_id, *children):
    return k.Node(node_id, k.OBSERVATION, tuple(children))


def main():
    results = {}

    # 1. Leaf reference identity is independent from external payload equality.
    p = k.node_ref("P")
    p1 = k.node_ref("P1")
    p2 = k.node_ref("P2")
    results["leaf_same_ref"] = k.reference_equal(p, k.node_ref("P"))
    results["leaf_distinct_same_payload_possible"] = (not k.reference_equal(p1, p2))

    # 2. Referenced calculated objects: same structure, distinct identities.
    a = k.node_ref("A")
    b = k.node_ref("B")
    structure = k.Node("P-body", k.PATTERN, (
        k.PatternSlot(0), k.PatternSlot(1)
    ))
    P1 = k.ref_object("P1", structure)
    P2 = k.ref_object("P2", structure)
    P1_same_id = k.ref_object("P1", structure)
    results["pattern_same_ref"] = k.reference_equal(P1, P1_same_id)
    results["pattern_distinct_ref_same_structure"] = (
        not k.reference_equal(P1, P2) and k.structural_equal(P1, P2)
    )
    results["pattern_distinct_structure"] = (
        not k.structural_equal(P1, k.ref_object("P3", k.Node("P3-body", k.PATTERN, (k.PatternSlot(0), k.PatternSlot(2)))))
    )

    # 3. *P = f(*A,*B): reference identity of the pattern is separate from
    #    references of its constituents.
    composed = k.Node("P-body", k.PATTERN, (
        k.PatternSlot(source_position=0),
        k.PatternSlot(source_position=1),
    ))
    P = k.ref_object("P", composed)
    P_alt = k.ref_object("P_alt", composed)
    results["composed_pattern_identity_separate"] = (
        not k.reference_equal(P, P_alt) and k.structural_equal(P, P_alt)
    )

    # 4. Recursive structural equality: same topology and same NodeRefs,
    #    despite different wrapper identity.
    rec1 = k.Node("rec1", k.OBSERVATION, (k.node_ref("F"), k.node_ref("A"), k.node_ref("B")))
    rec2 = k.Node("rec2", k.OBSERVATION, (k.node_ref("F"), k.node_ref("A"), k.node_ref("B")))
    results["recursive_structure_equal"] = k.structural_equal(
        k.ref_object("R1", rec1), k.ref_object("R2", rec2)
    )
    rec3 = k.Node("rec3", k.OBSERVATION, (k.node_ref("F"), k.node_ref("A2"), k.node_ref("B")))
    results["recursive_distinct_ref_not_equal"] = not k.structural_equal(rec1, rec3)

    # 5. E18 coreference discipline: same NodeRef repeated => same structural
    #    variable; distinct NodeRefs => distinct variables, even conceptually
    #    equal external payloads.
    same = k.Node("same", k.OBSERVATION, (k.node_ref("O"), k.node_ref("P"), k.node_ref("P"), k.node_ref("X")))
    diff = k.Node("diff", k.OBSERVATION, (k.node_ref("O"), k.node_ref("P1"), k.node_ref("P2"), k.node_ref("X")))
    ts = k._shape_template(same)
    td = k._shape_template(diff)
    vars_same = [
        ts.children[0].children[0] if False else None
    ]
    # Extract ShapeTerm VAR indices recursively for direct invariant check.
    def collect_vars(term):
        out=[]
        if isinstance(term, k.ShapeTerm):
            if term.kind == "VAR":
                out.append(term.value)
            for c in term.children:
                out.extend(collect_vars(c))
            out.extend(collect_vars(term.value) if isinstance(term.value, k.ShapeTerm) else [])
        return out
    vs = collect_vars(ts)
    vd = collect_vars(td)
    results["E18_same_ref_corefers"] = (vs.count(1) == 2)
    results["E18_distinct_ref_not_corefer"] = (vd.count(1) == 1 and vd.count(2) == 1)

    # 6. Pattern references preserve identity across repeated occurrence in a
    #    larger structural expression.
    outer_same = k.Node("outer_same", k.OBSERVATION, (k.node_ref("G"), P, P, k.node_ref("Z")))
    outer_diff = k.Node("outer_diff", k.OBSERVATION, (k.node_ref("G"), P, P_alt, k.node_ref("Z")))
    os_t = k._shape_template(outer_same)
    od_t = k._shape_template(outer_diff)
    os_v = collect_vars(os_t)
    od_v = collect_vars(od_t)
    results["pattern_ref_same_object_corefers"] = (os_v.count(1) >= 2)
    results["pattern_ref_distinct_objects_separate"] = (od_v.count(1) == 1 and od_v.count(2) == 1)

    # 7. Apply through a referenced pattern: representation identity does not
    #    alter application semantics when the denoted structure is retrieved.
    base_a = k.Node("a", k.OBSERVATION, ("O", "A", "B", "C"))
    base_b = k.Node("b", k.OBSERVATION, ("O", "B", "A", "C"))
    pat = k.compare(base_a, base_b)
    pat_ref = k.ref_object("P-swap", pat)
    fresh = k.Node("fresh", k.OBSERVATION, ("O", "X", "Y", "Z"))
    direct = k.apply(pat, fresh)
    via_ref = k.apply(pat_ref.structure, fresh)
    results["pattern_ref_preserves_apply"] = (direct == via_ref)

    # 8. Nested Pattern object remains a structural object, not a payload.
    nested1 = k.ref_object("N1", k.Node("n1", k.PATTERN, (k.PatternSlot(0),)))
    nested2 = k.ref_object("N2", k.Node("n2", k.PATTERN, (k.PatternSlot(0),)))
    results["nested_pattern_same_structure"] = k.structural_equal(nested1, nested2)

    # 9. Regression E13 / E18 / E19 basic behavior.
    pred = k.Node("pred", k.OBSERVATION, ("O", "X", "Y", "Z"))
    results["regression_E13_compare"] = pat is not None
    applied = k.apply(pat, pred)
    results["regression_E13_apply"] = applied is not None

    e19_obs = [
        k.Node("e19a", k.OBSERVATION, ("Z", "A", "K9", "A")),
        k.Node("e19b", k.OBSERVATION, ("Z", "B", "K9", "B")),
        k.Node("e19c", k.OBSERVATION, ("Z", "C", "K9", "C")),
    ]
    e19 = k.aggregate_observations(e19_obs)
    bad = k.Node("e19bad", k.OBSERVATION, ("Z", "FOO", "K9", "BAR"))
    results["regression_E19_pattern"] = e19 is not None
    results["regression_E19_guard"] = e19 is not None and not k.is_applicable(e19, bad)

    # 10. Compile-time-ish runtime invariant: no external payload is present
    #     on NodeRef and representation comparison never needs it.
    results["NodeRef_only_ref_id"] = tuple(k.NodeRef.__dataclass_fields__.keys()) == ("ref_id",)

    passed = all(results.values())
    payload = {
        "kernel": str(ROOT / "kernel2.py"),
        "test": "pattern_ref_invariant_v0.1",
        "results": results,
        "passed": passed,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
