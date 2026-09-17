from kernel2 import Node, NodeRef, OBSERVATION
from e20d_protocol import discover_cross_slot_candidates, replay_candidate


def make_rows():
    rows=[]
    for i in range(1,4):
        src=Node(f"src{i}", OBSERVATION, ("O", NodeRef(f"{i}x"), NodeRef(f"{i}y"), NodeRef("z")))
        tgt=Node(f"tgt{i}", OBSERVATION, ("O", NodeRef(f"{i}y"), NodeRef(f"{i}x"), NodeRef("z")))
        rows.append(Node(f"row{i}", OBSERVATION, (NodeRef(f"op{i}"), src, tgt, NodeRef("out"))))
    return rows


def test_recursive_transformation_discovered():
    rows=make_rows()
    r=discover_cross_slot_candidates(rows)
    c=[x for x in r.candidates if (x.source_position,x.target_position)==(1,2)][0]
    assert c.relation_kind == "COMPARE_RECURSIVE"
    assert any(s.nested_pattern is not None for s in c.transformation.pattern.children)


def test_recursive_transformation_replays_on_unseen_rows():
    rows=make_rows()
    r=discover_cross_slot_candidates(rows)
    c=[x for x in r.candidates if (x.source_position,x.target_position)==(1,2)][0]
    fresh=[]
    for i in range(1,4):
        fresh_src=Node(f"fresh_src{i}", OBSERVATION, ("O", NodeRef(f"f{i}x"), NodeRef(f"f{i}y"), NodeRef("z")))
        # Only the source slot is needed for replay; the other children are
        # opaque controls and are not consulted by the discovered transformation.
        fresh.append(Node(f"fresh_row{i}", OBSERVATION, (NodeRef(f"op{i}"), fresh_src, NodeRef(f"target{i}"), NodeRef("out"))))
    out=replay_candidate(c, fresh)
    assert out is not None
    assert out.kind == OBSERVATION
    assert len(out.children) == 3
    for i, predicted in enumerate(out.children, start=1):
        assert predicted.kind == OBSERVATION
        assert predicted.children[1] == NodeRef(f"f{i}y")
        assert predicted.children[2] == NodeRef(f"f{i}x")
