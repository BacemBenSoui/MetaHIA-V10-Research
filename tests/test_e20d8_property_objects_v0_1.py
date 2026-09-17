from kernel2 import (
    Node,
    NodeRef,
    RefObject,
    OBSERVATION,
    apply,
    apply_operator,
    ref_object,
    reference_equal,
    structural_equal,
    structural_signature,
    compare,
)


def _property(ref_id: str, op_id: str, *operands: str) -> RefObject:
    return ref_object(
        ref_id,
        Node(
            f"body::{ref_id}",
            OBSERVATION,
            (NodeRef(op_id),) + tuple(NodeRef(x) for x in operands),
        ),
    )


def main() -> int:
    checks = []

    # 1. Property objects remain ordinary reference-bearing structures.
    p1 = _property("P1", "pi1", "A", "B")
    p2 = _property("P2", "pi2", "C", "D")
    p1_clone = _property("P1_CLONE", "pi1", "A", "B")
    checks.append((not reference_equal(p1, p1_clone) and structural_equal(p1, p1_clone), "identity_vs_structure"))

    # 2. K3 Apply constructor form composes two property objects without semantics.
    m12 = apply_operator(NodeRef("f"), p1, p2, node_id="M12")
    checks.append((m12.kind == OBSERVATION and isinstance(m12.children[0], NodeRef) and m12.children[0].ref_id == "f", "operator_application"))
    checks.append((m12.children[1] is p1 and m12.children[2] is p2, "property_refs_preserved"))

    # 3. The public Apply overload gives the same constructor semantics.
    m12_public = apply(NodeRef("f"), p1, p2, node_id="M12-public")
    checks.append((structural_equal(m12, m12_public), "public_apply_constructor"))

    # 4. A composed structure can itself be reified and become an operand.
    m12_ref = ref_object("M12REF", m12)
    m123 = apply_operator(NodeRef("g"), m12_ref, p1, node_id="M123")
    checks.append((m123.children[1] is m12_ref, "recursive_meta_operand"))
    checks.append((isinstance(m123.children[1], RefObject), "recursive_refobject_retained"))

    # 5. Two independently reified composites can be structurally equivalent.
    m12_clone = ref_object("M12REF-2", m12)
    checks.append((not reference_equal(m12_ref, m12_clone) and structural_equal(m12_ref, m12_clone), "composite_identity_vs_structure"))

    # 6. Compare can look through the reference-bearing envelope when the body is an observation.
    p3 = _property("P3", "pi3", "A", "B")
    p4 = _property("P4", "pi3", "B", "A")
    pattern = compare(p3, p4)
    checks.append((pattern is not None and pattern.kind == "PATTERN", "compare_property_objects"))

    # 7. Nested recurrent RefObject is visible to the structural flattening view.
    inner = Node("inner", OBSERVATION, (NodeRef("r"), NodeRef("A"), NodeRef("B"), NodeRef("I_OUT")))
    wrapped_inner = ref_object("INNER", inner)
    outer = Node("outer", OBSERVATION, (NodeRef("r"), wrapped_inner, NodeRef("C"), NodeRef("O_OUT")))
    flat_sig = structural_signature(outer)
    # Structural signature must still distinguish the wrapper identity at ordinary positions.
    checks.append(("REF_OBJECT" in repr(flat_sig), "ordinary_structural_signature_keeps_wrapper"))

    # 8. Actual recurrent tree flattening sees through RefObject only during shape comparison.
    from kernel2 import _flatten_recurrent_args
    flat, out = _flatten_recurrent_args(outer)
    checks.append((tuple(x.ref_id for x in flat if isinstance(x, NodeRef)) == ("A", "B", "C") and out.ref_id == "O_OUT", "refobject_recurrent_flattening"))

    # 9. Pattern Compare remains unaffected by constructor overload.
    obs1 = Node("o1", OBSERVATION, (NodeRef("op"), NodeRef("X"), NodeRef("Y"), NodeRef("out")))
    obs2 = Node("o2", OBSERVATION, (NodeRef("op"), NodeRef("Y"), NodeRef("X"), NodeRef("out")))
    perm = compare(obs1, obs2)
    checks.append((perm is not None and perm.kind == "PATTERN", "compare_regression"))

    # 10. Existing pattern Apply behavior remains available.
    pred = apply(perm, obs1)
    checks.append((pred is not None and pred.kind == OBSERVATION, "pattern_apply_regression"))

    failed = [name for ok, name in checks if not ok]
    print(f"E20-D.8 checks: {len(checks) - len(failed)}/{len(checks)} PASS")
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
