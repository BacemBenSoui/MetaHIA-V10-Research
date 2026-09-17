import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import (
    OBSERVATION,
    Node,
    NodeRef,
    PathPattern,
    PATH_FORWARD, PATH_REVERSE,
    build_structural_graph,
    discover_paths,
    generalize_path_pattern,
    path_pattern_structural_form,
    reify_path_pattern,
    reference_equal,
    structural_equal,
    RefObject,
)


def rel(i, op, a, b):
    return Node(i, OBSERVATION, (NodeRef(op), NodeRef(a), NodeRef(b)), provenance=(i,))


def path(nodes_edges, start, end, depth):
    g = build_structural_graph(nodes_edges)
    return discover_paths(g, start=NodeRef(start), end=NodeRef(end), max_depth=depth, allow_reverse=True)[0]


def test_generalize_two_isomorphic_paths():
    p1 = path([rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')], 'A', 'C', 2)
    p2 = path([rel('r3', 'R', 'X', 'Y'), rel('r4', 'S', 'Y', 'Z')], 'X', 'Z', 2)
    pat = generalize_path_pattern([p1, p2], 'P1')
    assert isinstance(pat, PathPattern)
    assert pat.length == 2
    assert pat.direction_sequence == (PATH_FORWARD, PATH_FORWARD)
    assert pat.node_binding == (0, 1, 2)
    assert pat.position_groups == ((0,), (1,), (2,))
    assert pat.source_path_ids == (p1.path_id, p2.path_id)


def test_generalize_preserves_repeated_reference_structure():
    from kernel2 import PathRecord, PathStep

    p1 = PathRecord(
        "p1", NodeRef("A"), NodeRef("A"),
        (
            PathStep("e1", "r1", NodeRef("R"), PATH_FORWARD, NodeRef("A"), NodeRef("B")),
            PathStep("e2", "r2", NodeRef("S"), PATH_FORWARD, NodeRef("B"), NodeRef("A")),
        ),
        ("r1", "r2"),
    )
    p2 = PathRecord(
        "p2", NodeRef("X"), NodeRef("X"),
        (
            PathStep("e3", "r3", NodeRef("R"), PATH_FORWARD, NodeRef("X"), NodeRef("Y")),
            PathStep("e4", "r4", NodeRef("S"), PATH_FORWARD, NodeRef("Y"), NodeRef("X")),
        ),
        ("r3", "r4"),
    )
    pat = generalize_path_pattern([p1, p2], 'P2')
    assert pat.node_binding == (0, 1, 0)
    assert pat.position_groups == ((0, 2), (1,))


def test_generalize_intersects_reference_constraints_never_unions_them():
    from kernel2 import PathRecord, PathStep

    p1 = PathRecord(
        "p1", NodeRef("A"), NodeRef("C"),
        (
            PathStep("e1", "r1", NodeRef("R"), PATH_FORWARD, NodeRef("A"), NodeRef("A")),
            PathStep("e2", "r2", NodeRef("S"), PATH_FORWARD, NodeRef("A"), NodeRef("C")),
        ),
        ("r1", "r2"),
    )
    p2 = PathRecord(
        "p2", NodeRef("X"), NodeRef("Z"),
        (
            PathStep("e3", "r3", NodeRef("R"), PATH_FORWARD, NodeRef("X"), NodeRef("Y")),
            PathStep("e4", "r4", NodeRef("S"), PATH_FORWARD, NodeRef("Y"), NodeRef("Z")),
        ),
        ("r3", "r4"),
    )
    pat = generalize_path_pattern([p1, p2], 'P3')
    assert pat.node_binding == (0, 1, 2)
    assert pat.position_groups == ((0,), (1,), (2,))


def test_generalize_rejects_different_operator_direction_skeleton():
    p1 = path([rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')], 'A', 'C', 2)
    p2 = path([rel('r3', 'R', 'X', 'Y'), rel('r4', 'T', 'Y', 'Z')], 'X', 'Z', 2)
    assert generalize_path_pattern([p1, p2], 'P4') is None


def test_generalize_rejects_different_lengths():
    p1 = path([rel('r1', 'R', 'A', 'B')], 'A', 'B', 1)
    p2 = path([rel('r2', 'R', 'X', 'Y'), rel('r3', 'S', 'Y', 'Z')], 'X', 'Z', 2)
    assert generalize_path_pattern([p1, p2], 'P5') is None


def test_generalize_requires_two_paths():
    p1 = path([rel('r1', 'R', 'A', 'B')], 'A', 'B', 1)
    assert generalize_path_pattern([p1], 'P6') is None


def test_reify_path_pattern_preserves_reference_structure_separation():
    p1 = path([rel('r1', 'R', 'A', 'B')], 'A', 'B', 1)
    p2 = path([rel('r2', 'R', 'X', 'Y')], 'X', 'Y', 1)
    pat = generalize_path_pattern([p1, p2], 'P7')
    a = reify_path_pattern(pat, 'PP1')
    b = reify_path_pattern(pat, 'PP2')
    assert isinstance(a, RefObject) and isinstance(b, RefObject)
    assert not reference_equal(a, b)
    assert structural_equal(a, b)
    assert path_pattern_structural_form(pat)[0] == 'PATH'


def test_family_path_can_be_generalized_without_semantic_labeling():
    p1 = path([
        rel('f1', 'MERE_DE', 'Amanda', 'David'),
        rel('f2', 'ENFANT_DE', 'Lucas', 'David'),
    ], 'Amanda', 'Lucas', 2)
    p2 = path([
        rel('f3', 'MERE_DE', 'Amanda', 'David'),
        rel('f4', 'ENFANT_DE', 'Emma', 'David'),
    ], 'Amanda', 'Emma', 2)
    pat = generalize_path_pattern([p1, p2], 'FAM')
    assert pat is not None
    assert pat.operator_sequence == (NodeRef('MERE_DE'), NodeRef('ENFANT_DE'))
    assert pat.direction_sequence == (PATH_FORWARD, PATH_REVERSE)
    assert pat.node_binding == (0, 1, 2)
