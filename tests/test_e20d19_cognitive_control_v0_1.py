from kernel2 import Node, OBSERVATION, node_ref, build_structural_graph, discover_paths
from e20d_cognitive_control_v0_1 import (
    DECISION_DEFER,
    DECISION_EXPLORE,
    DECISION_STOP,
    build_candidate,
    path_redundancy,
    rank_candidates,
    score_candidate,
    select_reinjection_candidates,
)


def obs(i, op, a, b):
    return Node(i, OBSERVATION, (op, a, b), provenance=(i,))


def main():
    A, B, C, D, MOTO = map(node_ref, ("A", "B", "C", "D", "Moto"))
    R, S, T = map(node_ref, ("R", "S", "T"))

    graph = build_structural_graph(
        [
            obs("e1", R, A, B),
            obs("e2", S, B, C),
            obs("e3", T, C, D),
            obs("e4", node_ref("possede"), A, MOTO),
        ]
    )

    paths = discover_paths(graph, start=A, max_depth=3)
    assert paths, "expected at least one structural path"
    p = paths[0]

    c_hi = build_candidate(p, expected_gain=2.0, structural_novelty=1.0)
    s_hi = score_candidate(c_hi)
    assert s_hi.decision == DECISION_EXPLORE
    assert s_hi.roi > 0.5

    c_mid = build_candidate(p, expected_gain=1.2, structural_novelty=0.8, estimated_cost=3.0)
    s_mid = score_candidate(c_mid)
    assert s_mid.decision == DECISION_DEFER

    c_low = build_candidate(p, expected_gain=0.05, structural_novelty=0.2, estimated_cost=5.0)
    s_low = score_candidate(c_low)
    assert s_low.decision == DECISION_STOP

    assert path_redundancy(p, [p]) == 1.0

    q = tuple(x for x in paths if x.path_id != p.path_id)
    if q:
        assert path_redundancy(q[0], [p]) in (0.0, 1.0)

    c_absurd = build_candidate(p, expected_gain=2.0, structural_novelty=1.0)
    selected = select_reinjection_candidates([c_absurd])
    assert selected and selected[0].decision == DECISION_EXPLORE

    # Semantic-free principle: the controller does not reject a path because
    # its endpoint is an arbitrary opaque node such as "Moto".
    moto_paths = tuple(x for x in paths if x.end.ref_id == "Moto")
    if moto_paths:
        c_moto = build_candidate(moto_paths[0], expected_gain=2.0, structural_novelty=1.0)
        assert score_candidate(c_moto).decision == DECISION_EXPLORE

    # Ordering is deterministic and semantic-free.
    ranked = rank_candidates([c_mid, c_hi, c_low])
    assert ranked[0].roi >= ranked[1].roi >= ranked[2].roi
    assert ranked[0].path_id == c_hi.path.path_id

    print("E20-D.19: 12/12 PASS")


if __name__ == "__main__":
    main()
