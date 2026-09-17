import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import (
    OBSERVATION,
    Node,
    NodeRef,
    PathPropertyObject,
    RefObject,
    build_structural_graph,
    discover_paths,
    path_properties,
    path_property_objects,
    path_property_structural_form,
    path_properties_structural_form,
    reify_path_property,
    reify_path_properties,
    reference_equal,
    structural_equal,
    structural_signature,
)


def rel(i, op, a, b):
    return Node(i, OBSERVATION, (NodeRef(op), NodeRef(a), NodeRef(b)), provenance=(i,))


def one_path(edges, start, end, depth):
    g = build_structural_graph(edges)
    return discover_paths(g, NodeRef(start), NodeRef(end), depth, allow_reverse=True)[0]


def test_path_properties_are_extracted_as_standalone_objects():
    p = one_path([
        rel("r1", "R", "A", "B"),
        rel("r2", "S", "B", "C"),
    ], "A", "C", 2)
    props = path_property_objects(p)
    assert len(props) == 10
    assert all(isinstance(x, PathPropertyObject) for x in props)
    assert props[0].key == "length"
    assert props[0].value == 2
    assert props[0].provenance == p.provenance


def test_property_structural_form_ignores_identity_metadata():
    p = one_path([rel("r1", "R", "A", "B")], "A", "B", 1)
    prop = path_property_objects(p)[0]
    clone = PathPropertyObject("different-id", prop.key, prop.value, "other-path", ("other-source",))
    assert not reference_equal(reify_path_property(prop, "X"), reify_path_property(prop, "Y"))
    assert structural_equal(prop, clone)
    assert structural_signature(prop) == structural_signature(clone)
    assert path_property_structural_form(prop) == path_property_structural_form(clone)


def test_different_property_values_remain_structurally_distinct():
    p1 = one_path([rel("r1", "R", "A", "B")], "A", "B", 1)
    p2 = one_path([
        rel("r2", "R", "A", "B"),
        rel("r3", "S", "B", "C"),
    ], "A", "C", 2)
    a = [x for x in path_property_objects(p1) if x.key == "length"][0]
    b = [x for x in path_property_objects(p2) if x.key == "length"][0]
    assert not structural_equal(a, b)
    assert structural_signature(a) != structural_signature(b)


def test_path_properties_bundle_is_reifiable_and_structural():
    p = one_path([
        rel("r1", "R", "A", "B"),
        rel("r2", "S", "B", "C"),
    ], "A", "C", 2)
    bundle = path_properties(p)
    x = reify_path_properties(bundle, "B1")
    y = reify_path_properties(bundle, "B2")
    assert isinstance(x, RefObject)
    assert isinstance(y, RefObject)
    assert not reference_equal(x, y)
    assert structural_equal(x, y)
    assert structural_signature(x.structure) == structural_signature(y.structure)


def test_property_objects_from_two_paths_can_be_compared_structurally():
    p1 = one_path([rel("r1", "R", "A", "B")], "A", "B", 1)
    p2 = one_path([rel("r2", "R", "X", "Y")], "X", "Y", 1)
    a = {x.key: x for x in path_property_objects(p1)}
    b = {x.key: x for x in path_property_objects(p2)}
    for key in ("length", "distinct_node_count", "distinct_operator_count", "repeated_operator"):
        assert structural_equal(a[key], b[key])


def test_properties_preserve_path_provenance_without_leaking_into_structure():
    p = one_path([rel("r1", "R", "A", "B")], "A", "B", 1)
    prop = path_property_objects(p)[1]
    assert prop.provenance == ("r1",)
    assert prop.path_id == p.path_id
    form = path_property_structural_form(prop)
    assert form[0] == "PATH_PROPERTY"
    assert "r1" not in form


def test_direction_and_reversal_are_structural_properties():
    p = one_path([rel("r1", "R", "A", "B")], "B", "A", 1)
    props = {x.key: x.value for x in path_property_objects(p)}
    assert props["direction_sequence"] == ("REVERSE",)
    assert props["reversed_traversal"] is True


def test_property_bundle_contains_only_structural_features():
    p = one_path([rel("r1", "R", "A", "B")], "A", "B", 1)
    props = path_properties(p)
    form = path_properties_structural_form(props)
    assert form[0] == "PATH_PROPERTIES"
    assert all(item[0] == "PATH_PROPERTY" for item in form[1])
    assert not any("r1" in repr(item) for item in form[1])
