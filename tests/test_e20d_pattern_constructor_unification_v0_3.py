import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel2 import (
    Node, NodeRef, PatternRef, PatternSlot, ShapeRewrite, ShapeTerm,
    OBSERVATION, PATTERN, SHAPE_PATTERN,
    ref_object, pattern_ref, reference_equal, pattern_structural_equal,
    compare_pattern_references, structural_signature,
)


def make_pattern(ref_id="P", mapping=(0, 1, 2)):
    return Node(
        node_id=f"p::{ref_id}",
        kind=PATTERN,
        children=tuple(PatternSlot(source_position=i) for i in mapping),
        provenance=(ref_id,),
    )


def make_shape(mapping=(0, 1, 2)):
    n = len(mapping)
    op = ShapeTerm("VAR", 0)
    src = ShapeTerm("APPLY", op, tuple(ShapeTerm("VAR", i + 1) for i in range(n)))
    dst = ShapeTerm("APPLY", op, tuple(ShapeTerm("VAR", i + 1) for i in mapping))
    return Node(
        node_id="shape::mapping",
        kind=SHAPE_PATTERN,
        children=(ShapeRewrite(src, dst, n),),
        provenance=("shape",),
    )


def test_constructor_dispatches_pattern_to_patternref():
    p = make_pattern(mapping=(1, 0, 2))
    r = ref_object("P1", p)
    assert isinstance(r, PatternRef)
    assert r.kind == PATTERN
    assert r.pattern is p
    assert r.ref.ref_id == "P1"


def test_explicit_constructor_accepts_both_internal_kinds():
    p = pattern_ref("P1", make_pattern(mapping=(1, 0, 2)))
    s = pattern_ref("S1", make_shape(mapping=(1, 0, 2)))
    assert p.kind == PATTERN
    assert s.kind == SHAPE_PATTERN
    assert p.pattern.kind == PATTERN
    assert s.pattern.kind == SHAPE_PATTERN


def test_same_structure_different_pattern_refs_stay_distinct():
    p = make_pattern(mapping=(1, 0, 2))
    p1 = PatternRef("P1", p)
    p2 = PatternRef("P2", make_pattern("P2", mapping=(1, 0, 2)))
    assert not reference_equal(p1, p2)
    assert pattern_structural_equal(p1, p2)
    assert compare_pattern_references(p1, p2) is True


def test_pattern_and_shapepattern_unify_for_pure_mapping():
    p = PatternRef("P1", make_pattern(mapping=(1, 0, 2)))
    s = PatternRef("S1", make_shape(mapping=(1, 0, 2)))
    assert compare_pattern_references(p, s) is True
    assert pattern_structural_equal(p, s)
    assert structural_signature(p.pattern) == structural_signature(s.pattern)


def test_different_transformations_do_not_unify():
    p = PatternRef("P1", make_pattern(mapping=(1, 0, 2)))
    s = PatternRef("S1", make_shape(mapping=(0, 2, 1)))
    assert compare_pattern_references(p, s) is False
    assert not pattern_structural_equal(p, s)


def test_literal_pattern_does_not_get_falsely_forced_into_tree_mapping():
    p = Node(
        node_id="literal",
        kind=PATTERN,
        children=(
            PatternSlot(source_position=0, literal_constraint=NodeRef("fixed")),
            PatternSlot(source_position=1),
        ),
    )
    s = make_shape(mapping=(0, 1))
    assert compare_pattern_references(PatternRef("P", p), PatternRef("S", s)) is False


def test_same_value_different_refs_inside_pattern_remain_distinct():
    # The two leaves may carry equal external payloads, but distinct refs are
    # different structural atoms to the kernel.
    n1 = Node("n1", OBSERVATION, (NodeRef("A1"), NodeRef("B1")))
    n2 = Node("n2", OBSERVATION, (NodeRef("A2"), NodeRef("B2")))
    r1 = ref_object("P1", n1)
    r2 = ref_object("P2", n2)
    assert not structural_signature(r1) == structural_signature(r2)


if __name__ == "__main__":
    tests = [
        test_constructor_dispatches_pattern_to_patternref,
        test_explicit_constructor_accepts_both_internal_kinds,
        test_same_structure_different_pattern_refs_stay_distinct,
        test_pattern_and_shapepattern_unify_for_pure_mapping,
        test_different_transformations_do_not_unify,
        test_literal_pattern_does_not_get_falsely_forced_into_tree_mapping,
        test_same_value_different_refs_inside_pattern_remain_distinct,
    ]
    results = []
    for test in tests:
        try:
            test()
            results.append({"test": test.__name__, "status": "PASS"})
        except Exception as exc:
            results.append({"test": test.__name__, "status": "FAIL", "error": repr(exc)})
    out = {
        "suite": "E20-D.1 pattern constructor + structural unification v0.3",
        "passed": sum(r["status"] == "PASS" for r in results),
        "failed": sum(r["status"] == "FAIL" for r in results),
        "tests": results,
    }
    out_path = Path(__file__).with_name("TEST_RESULTS_E20D_PATTERN_UNIFICATION_V0_3.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
