import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel2 import (
    OBSERVATION, Node, NodeRef, PATH_REPLAY_AMBIGUOUS, PATH_REPLAY_NOT_FOUND,
    PATH_REPLAYED, PathPattern, build_structural_graph, discover_paths,
    generalize_path_pattern, path_pattern_structural_form,
    predicted_link_from_replay, replay_path_pattern, replay_path_pattern_holdout,
    reference_equal, structural_equal,
)


def rel(i, op, a, b):
    return Node(i, OBSERVATION, (NodeRef(op), NodeRef(a), NodeRef(b)), provenance=(i,))


def first_path(edges, start, end):
    g = build_structural_graph(edges)
    paths = discover_paths(g, NodeRef(start), NodeRef(end), max_depth=3, allow_reverse=True)
    assert paths
    return paths[0]


def test_pattern_replay_predicts_unique_holdout_endpoint():
    p1 = first_path([rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')], 'A', 'C')
    p2 = first_path([rel('r3', 'R', 'X', 'Y'), rel('r4', 'S', 'Y', 'Z')], 'X', 'Z')
    pattern = generalize_path_pattern([p1, p2], 'PP::RS')
    holdout = [rel('h1', 'R', 'M', 'N'), rel('h2', 'S', 'N', 'P')]
    result = replay_path_pattern_holdout(pattern, holdout, NodeRef('M'))
    assert result.status == PATH_REPLAYED
    assert result.predicted_end == NodeRef('P')
    assert result.path is not None
    assert result.path.provenance == ('h1', 'h2')


def test_replay_produces_candidate_link_with_traceable_path():
    p1 = first_path([rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')], 'A', 'C')
    p2 = first_path([rel('r3', 'R', 'X', 'Y'), rel('r4', 'S', 'Y', 'Z')], 'X', 'Z')
    pattern = generalize_path_pattern([p1, p2], 'PP::LINK')
    result = replay_path_pattern(pattern, build_structural_graph([rel('h1', 'R', 'M', 'N'), rel('h2', 'S', 'N', 'P')]), NodeRef('M'))
    link = predicted_link_from_replay(result, 'LINK::HOLDOUT')
    assert link is not None
    assert link.ref == NodeRef('LINK::HOLDOUT')
    assert link.structure[0] == 'LINK'
    assert link.structure[1:3] == (NodeRef('M'), NodeRef('P'))


def test_replay_fails_closed_when_required_step_missing():
    p1 = first_path([rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')], 'A', 'C')
    p2 = first_path([rel('r3', 'R', 'X', 'Y'), rel('r4', 'S', 'Y', 'Z')], 'X', 'Z')
    pattern = generalize_path_pattern([p1, p2], 'PP::MISS')
    result = replay_path_pattern_holdout(pattern, [rel('h1', 'R', 'M', 'N')], NodeRef('M'))
    assert result.status == PATH_REPLAY_NOT_FOUND
    assert result.predicted_end is None
    assert result.path is None


def test_replay_fails_closed_when_step_is_ambiguous():
    p1 = first_path([rel('r1', 'R', 'A', 'B'), rel('r2', 'S', 'B', 'C')], 'A', 'C')
    p2 = first_path([rel('r3', 'R', 'X', 'Y'), rel('r4', 'S', 'Y', 'Z')], 'X', 'Z')
    pattern = generalize_path_pattern([p1, p2], 'PP::AMB')
    holdout = [
        rel('h1', 'R', 'M', 'N'),
        rel('h2', 'R', 'M', 'Q'),
        rel('h3', 'S', 'N', 'P'),
        rel('h4', 'S', 'Q', 'T'),
    ]
    result = replay_path_pattern_holdout(pattern, holdout, NodeRef('M'), max_candidates_per_step=1)
    assert result.status == PATH_REPLAY_AMBIGUOUS
    assert result.predicted_end is None


def test_replay_preserves_reference_identity_not_payload_value():
    p1 = first_path([rel('r1', 'R', 'A1', 'B1'), rel('r2', 'S', 'B1', 'C1')], 'A1', 'C1')
    p2 = first_path([rel('r3', 'R', 'A2', 'B2'), rel('r4', 'S', 'B2', 'C2')], 'A2', 'C2')
    pattern = generalize_path_pattern([p1, p2], 'PP::REF')
    holdout = [rel('h1', 'R', 'M', 'N1'), rel('h2', 'S', 'N1', 'P')]
    result = replay_path_pattern_holdout(pattern, holdout, NodeRef('M'))
    assert result.predicted_end == NodeRef('P')
    assert not reference_equal(result.predicted_end, NodeRef('N1'))


def test_replay_uses_operator_direction_skeleton_only():
    p = PathPattern(
        pattern_id='PP::REV',
        operator_sequence=(NodeRef('R'),),
        direction_sequence=('REVERSE',),
        node_binding=(0, 1),
        position_groups=((0,), (1,)),
        source_path_ids=('manual::rev',),
        provenance=('manual::rev',),
    )
    graph = build_structural_graph([rel('h1', 'R', 'A', 'B')])
    result = replay_path_pattern(p, graph, NodeRef('B'))
    assert result.status == PATH_REPLAYED
    assert result.predicted_end == NodeRef('A')


def test_structural_signature_of_pattern_is_identity_free():
    p1 = first_path([rel('r1', 'R', 'A', 'B')], 'A', 'B')
    p2 = first_path([rel('r2', 'R', 'X', 'Y')], 'X', 'Y')
    pp1 = generalize_path_pattern([p1, p2], 'PP::SIG')
    assert pp1 is not None
    form = path_pattern_structural_form(pp1)
    assert form[0] == 'PATH'
    assert structural_equal(form, path_pattern_structural_form(pp1))
