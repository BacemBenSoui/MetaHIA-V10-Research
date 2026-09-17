import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import (
    OBSERVATION,
    Node,
    NodeRef,
    RefObject,
    PATH_FORWARD,
    build_structural_graph,
    discover_paths,
    reify_path_link,
    reinject_reified_links,
    materialize_reified_link,
    structural_equal,
    reference_equal,
)


def rel(node_id, op, a, b, prov=None):
    return Node(
        node_id,
        OBSERVATION,
        (NodeRef(op), NodeRef(a), NodeRef(b)),
        provenance=(node_id,) if prov is None else tuple(prov),
    )


def test_reified_link_materializes_to_ordinary_binary_observation():
    observed = [rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')]
    graph = build_structural_graph(observed)
    path = discover_paths(graph, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    link = reify_path_link(path, ref_id='L1')
    materialized = materialize_reified_link(link, provenance=('L1', 'r1', 'r2'))
    assert materialized.kind == OBSERVATION
    assert materialized.children == (link, NodeRef('A'), NodeRef('C'))
    assert materialized.provenance == ('L1', 'r1', 'r2')


def test_reinject_adds_generated_link_as_opaque_operator_edge():
    observed = [rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')]
    graph = build_structural_graph(observed)
    path = discover_paths(graph, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    link = reify_path_link(path, ref_id='L1')
    closed = reinject_reified_links(graph, [link])
    assert len(closed.edges) == len(graph.edges) + 1
    generated = closed.edges[-1]
    assert isinstance(generated.operator, RefObject)
    assert reference_equal(generated.operator, link)
    assert reference_equal(generated.source, NodeRef('A'))
    assert reference_equal(generated.target, NodeRef('C'))


def test_generated_link_participates_in_next_path_exploration():
    observed = [
        rel('r1', 'R', 'A', 'B'),
        rel('r2', 'S', 'B', 'C'),
        rel('r3', 'T', 'C', 'D'),
    ]
    graph = build_structural_graph(observed)
    base_path = discover_paths(graph, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    link = reify_path_link(base_path, ref_id='L::AC')
    closed = reinject_reified_links(graph, [link])

    paths = discover_paths(closed, start=NodeRef('A'), end=NodeRef('D'), max_depth=2)
    assert any(p.length == 2 for p in paths)
    derived_path = next(p for p in paths if p.length == 2 and reference_equal(p.end, NodeRef('D')))
    assert derived_path.direction_sequence == (PATH_FORWARD, PATH_FORWARD)
    assert derived_path.provenance[0] == 'reinject::0::L::AC'
    assert derived_path.provenance[1] == 'r3'


def test_second_iteration_uses_newly_emerged_edge():
    observed = [
        rel('r1', 'R', 'A', 'B'),
        rel('r2', 'S', 'B', 'C'),
        rel('r3', 'T', 'C', 'D'),
        rel('r4', 'U', 'D', 'E'),
    ]
    graph0 = build_structural_graph(observed)
    p_ac = discover_paths(graph0, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    l_ac = reify_path_link(p_ac, ref_id='L::AC')
    graph1 = reinject_reified_links(graph0, [l_ac])

    p_ad = discover_paths(graph1, start=NodeRef('A'), end=NodeRef('D'), max_depth=2)[0]
    l_ad = reify_path_link(p_ad, ref_id='L::AD')
    graph2 = reinject_reified_links(graph1, [l_ad])

    paths = discover_paths(graph2, start=NodeRef('A'), end=NodeRef('E'), max_depth=2)
    assert any(p.length == 2 and reference_equal(p.end, NodeRef('E')) for p in paths)
    p_ae = next(p for p in paths if p.length == 2 and reference_equal(p.end, NodeRef('E')))
    assert p_ae.provenance[0] == 'reinject::0::L::AD'
    assert p_ae.provenance[1] == 'r4'


def test_loop_closure_does_not_mutate_original_graph():
    observed = [rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')]
    graph = build_structural_graph(observed)
    path = discover_paths(graph, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    link = reify_path_link(path, ref_id='L1')
    closed = reinject_reified_links(graph, [link])
    assert len(graph.edges) == 2
    assert len(closed.edges) == 3


def test_semantically_unknown_link_is_not_filtered():
    observed = [rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')]
    graph = build_structural_graph(observed)
    path = discover_paths(graph, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    link = reify_path_link(path, ref_id='LINK::UNKNOWN::MEANING')
    closed = reinject_reified_links(graph, [link])
    paths = discover_paths(closed, start=NodeRef('A'), end=NodeRef('C'), max_depth=1)
    assert any(p.length == 1 for p in paths)


def test_rv1_keeps_generated_operator_identity_distinct_from_structure():
    observed = [rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')]
    graph = build_structural_graph(observed)
    path = discover_paths(graph, start=NodeRef('A'), end=NodeRef('C'), max_depth=2)[0]
    l1 = reify_path_link(path, ref_id='L1')
    l2 = reify_path_link(path, ref_id='L2')
    assert not reference_equal(l1, l2)
    assert structural_equal(l1, l2)


def test_invalid_link_fails_closed():
    bad = RefObject(NodeRef('BAD'), ('NOT_A_LINK', NodeRef('A'), NodeRef('B')))
    try:
        materialize_reified_link(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid link was not rejected')
