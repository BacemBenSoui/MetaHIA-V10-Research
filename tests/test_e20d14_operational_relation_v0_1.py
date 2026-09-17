import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import (
    OBSERVATION, Node, NodeRef, PathPropertyObject, RefObject,
    build_structural_graph, discover_paths, generalize_path_pattern,
    reference_equal, structural_equal,
)
from e20d_operational_relation_v0_1 import (
    OperationalRelationRecord,
    discover_operational_relation,
    operational_relation_structural_equal,
    reify_operational_relation,
)


def rel(i, op, a, b):
    return Node(i, OBSERVATION, (NodeRef(op), NodeRef(a), NodeRef(b)), provenance=(i,))


def one_path(edges, start, end, depth):
    g = build_structural_graph(edges)
    return discover_paths(g, NodeRef(start), NodeRef(end), depth, allow_reverse=True)[0]


def test_same_path_property_is_structurally_equivalent():
    p1 = PathPropertyObject("p1", "length", 2, "path1", ("r1",))
    p2 = PathPropertyObject("p2", "length", 2, "path2", ("r2",))
    r = discover_operational_relation(p1, p2, "R1")
    assert isinstance(r, OperationalRelationRecord)
    assert r.relation_kind == "STRUCTURAL_EQUIVALENCE"
    assert r.fields[0].relation == "EQUAL"


def test_same_property_key_different_value_yields_relation_not_failure():
    p1 = PathPropertyObject("p1", "length", 2, "path1", ())
    p2 = PathPropertyObject("p2", "length", 3, "path2", ())
    r = discover_operational_relation(p1, p2, "R2")
    assert r is not None
    assert r.fields[0].relation == "DIFFERENT"
    assert r.relation_kind == "STRUCTURAL_RELATION"


def test_unrelated_property_keys_fail_closed():
    p1 = PathPropertyObject("p1", "length", 2, "path1", ())
    p2 = PathPropertyObject("p2", "direction_sequence", ("FORWARD",), "path2", ())
    assert discover_operational_relation(p1, p2) is None


def test_path_records_can_be_compared_via_common_structural_properties():
    p1 = one_path([rel("r1", "R", "A", "B"), rel("r2", "S", "B", "C")], "A", "C", 2)
    p2 = one_path([rel("r3", "R", "X", "Y"), rel("r4", "S", "Y", "Z")], "X", "Z", 2)
    r = discover_operational_relation(p1, p2, "R3")
    assert r is not None
    assert any(f.key == "length" and f.relation == "EQUAL" for f in r.fields)
    assert any(f.key == "operator_sequence" and f.relation == "EQUAL" for f in r.fields)


def test_path_pattern_relations_are_structural_and_opaque():
    p1 = one_path([rel("r1", "R", "A", "B"), rel("r2", "S", "B", "C")], "A", "C", 2)
    p2 = one_path([rel("r3", "R", "X", "Y"), rel("r4", "S", "Y", "Z")], "X", "Z", 2)
    a = generalize_path_pattern([p1, p2], "PP1")
    p3 = one_path([rel("r5", "R", "M", "N"), rel("r6", "S", "N", "Q")], "M", "Q", 2)
    p4 = one_path([rel("r7", "R", "U", "V"), rel("r8", "S", "V", "W")], "U", "W", 2)
    b = generalize_path_pattern([p3, p4], "PP2")
    r = discover_operational_relation(a, b, "R4")
    assert r is not None
    assert r.relation_kind == "STRUCTURAL_EQUIVALENCE"


def test_reified_operational_relation_keeps_identity_separate():
    p1 = PathPropertyObject("p1", "length", 2, "path1", ())
    p2 = PathPropertyObject("p2", "length", 2, "path2", ())
    r = discover_operational_relation(p1, p2, "R5")
    x = reify_operational_relation(r, "RX")
    y = reify_operational_relation(r, "RY")
    assert isinstance(x, RefObject) and isinstance(y, RefObject)
    assert not reference_equal(x, y)
    assert structural_equal(x, y)


def test_relation_structure_is_replayable_across_provenance():
    p1 = PathPropertyObject("p1", "length", 2, "path1", ("s1",))
    p2 = PathPropertyObject("p2", "length", 2, "path2", ("s2",))
    p3 = PathPropertyObject("p3", "length", 2, "path3", ("s3",))
    r1 = discover_operational_relation(p1, p2, "R6")
    r2 = discover_operational_relation(p2, p3, "R7")
    assert operational_relation_structural_equal(r1, r2)
