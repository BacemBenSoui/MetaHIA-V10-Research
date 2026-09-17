"""Targeted regression for the two Reference/Value reserves found on 2026-09-16."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import kernel2 as k


def obs(node_id, op, *args, out="OUT"):
    return k.Node(node_id, k.OBSERVATION, (op,) + tuple(args) + (out,))


def run():
    results = {}

    # Reserve 1: a RefObject around a recurrent same-operator sub-application
    # must be visible to the recursive structural traversal.
    inner = obs("inner", "O", "A", "B", out="X")
    wrapped = k.RefObject(k.NodeRef("P"), inner)
    outer = obs("outer", "O", wrapped, "C", out="Y")
    flat, _ = k._flatten_recurrent_args(outer)
    results["reserve1_flatten_sees_through_refobject"] = (
        flat == ["A", "B", "C"]
    )
    shape = k._shape_template(outer)
    results["reserve1_shape_template_sees_nested_refobject"] = (
        shape.kind == "APPLY"
        and shape.children[0].kind == "APPLY"
    )

    # Reserve 2a: reference identity remains independent from structure.
    p1 = k.Node(
        "p1", k.PATTERN,
        (k.PatternSlot(0, literal_constraint="A"),
         k.PatternSlot(1, literal_constraint="B")),
    )
    p2 = k.Node(
        "p2", k.PATTERN,
        (k.PatternSlot(0, literal_constraint="A"),
         k.PatternSlot(1, literal_constraint="C")),
    )
    r1 = k.PatternRef("P", p1)
    r2 = k.PatternRef("P", p2)
    results["reserve2_same_reference_detected"] = k.reference_equal(r1, r2)
    results["reserve2_different_structure_remains_detectable"] = not k.structural_equal(r1, r2)

    # Reserve 2b: internal same-source constraints must use reference-aware
    # comparison, not RefObject.__eq__/Node payload equality.
    a = k.NodeRef("A")
    b = k.NodeRef("B")
    c = k.NodeRef("C")
    observations = [
        obs("r1", "R", a, a, out="Z"),
        obs("r2", "R", b, b, out="Z"),
        obs("r3", "R", c, c, out="Z"),
    ]
    pattern = k.aggregate_observations(observations)
    same = obs("same", "R", a, a, out="Z")
    diff = obs("diff", "R", a, b, out="Z")
    results["reserve2_requires_source_equal_same_ref"] = (
        pattern is not None and k.pattern_is_applicable(pattern, same)
    )
    results["reserve2_requires_source_equal_distinct_ref_rejected"] = (
        pattern is not None and not k.pattern_is_applicable(pattern, diff)
    )

    # RefObject literal constraints use structural comparison rather than raw
    # dataclass equality, so distinct references carrying the same structure
    # are structurally matchable when the constraint itself is structural.
    lit_a = k.RefObject(k.NodeRef("LA"), obs("lit-a", "V", "A", out="X"))
    lit_b = k.RefObject(k.NodeRef("LB"), obs("lit-b", "V", "A", out="X"))
    literal_pattern = k.Node(
        "lp", k.PATTERN,
        (k.PatternSlot(0, literal_constraint=lit_a),),
    )
    literal_observation = k.Node("lo", k.OBSERVATION, (lit_b,))
    results["reserve2_structural_literal_uses_structural_eq"] = (
        k.pattern_is_applicable(literal_pattern, literal_observation)
    )

    return results


if __name__ == "__main__":
    results = run()
    failed = [name for name, ok in results.items() if not ok]
    print({"passed": len(results) - len(failed), "failed": len(failed), "results": results})
    raise SystemExit(1 if failed else 0)
