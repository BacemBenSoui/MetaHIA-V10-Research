import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel2 import Node, NodeRef, OBSERVATION, ref_object, structural_equal, reference_equal
from e20d_protocol import discover_cross_slot_candidates, replay_candidate


def obs(i, *children):
    return Node(f"R{i}", OBSERVATION, tuple(children), provenance=(f"R{i}",))


def find(discovery, s, t):
    return [c for c in discovery.candidates if c.source_position == s and c.target_position == t]


def test_reference_equality_discovered():
    rows = [obs(1, NodeRef("a1"), NodeRef("a1"), NodeRef("z1")),
            obs(2, NodeRef("b1"), NodeRef("b1"), NodeRef("z2")),
            obs(3, NodeRef("c1"), NodeRef("c1"), NodeRef("z3"))]
    d = discover_cross_slot_candidates(rows)
    cs = find(d, 0, 1)
    assert len(cs) == 1
    assert cs[0].relation_kind == "REFERENCE_EQUALITY"
    assert all("pos0->pos1" in p for p in cs[0].source_target_provenance)


def test_same_payload_different_refs_not_merged():
    # External payload could be the same, but the kernel sees distinct refs.
    rows = [obs(1, NodeRef("a1"), NodeRef("b1")),
            obs(2, NodeRef("a2"), NodeRef("b2")),
            obs(3, NodeRef("a3"), NodeRef("b3"))]
    d = discover_cross_slot_candidates(rows)
    assert not find(d, 0, 1)


def test_generic_compare_permutation():
    rows = [obs(1, NodeRef("a"), NodeRef("b")),
            obs(2, NodeRef("b"), NodeRef("a")),
            obs(3, NodeRef("c"), NodeRef("c"))]
    d = discover_cross_slot_candidates(rows)
    # Target is a uniform row permutation of source: [b,a,c].
    cs = find(d, 0, 1)
    assert len(cs) == 1
    assert cs[0].relation_kind == "COMPARE_PERMUTATION"


def test_replay_uniform_permutation():
    # target column is the source column shifted by one row.
    rows = [obs(1, NodeRef("a"), NodeRef("b"), NodeRef("x")),
            obs(2, NodeRef("b"), NodeRef("c"), NodeRef("y")),
            obs(3, NodeRef("c"), NodeRef("a"), NodeRef("z"))]
    d = discover_cross_slot_candidates(rows)
    cs = find(d, 0, 1)
    assert len(cs) == 1
    assert cs[0].relation_kind == "COMPARE_PERMUTATION"
    replay = replay_candidate(cs[0], [obs(4, NodeRef("d"), NodeRef("e"), NodeRef("q")),
                                      obs(5, NodeRef("e"), NodeRef("f"), NodeRef("r")),
                                      obs(6, NodeRef("f"), NodeRef("d"), NodeRef("s"))])
    assert replay is not None
    assert replay.kind == OBSERVATION


def test_ambiguous_or_unidentified_is_not_forced():
    # Repeated references among genuinely varying positions yield several
    # valid Compare permutations. The protocol must expose ambiguity.
    rows = [obs(1, NodeRef("a"), NodeRef("b")),
            obs(2, NodeRef("a"), NodeRef("c")),
            obs(3, NodeRef("b"), NodeRef("a")),
            obs(4, NodeRef("c"), NodeRef("a"))]
    d = discover_cross_slot_candidates(rows)
    assert not find(d, 0, 1)
    assert any(pair[0] == 0 and pair[1] == 1 for pair in d.ambiguous_pairs)


def test_provenance_is_mechanical():
    rows = [obs(1, NodeRef("a"), NodeRef("a")),
            obs(2, NodeRef("b"), NodeRef("b")),
            obs(3, NodeRef("c"), NodeRef("c"))]
    d = discover_cross_slot_candidates(rows)
    c = find(d, 0, 1)[0]
    assert c.evidence_rows == ("R1", "R2", "R3")
    assert c.transformation.ref.ref_id == "T::REF_EQ::0->1"
    assert set(c.transformation.structure.provenance) == set(c.source_target_provenance)


def test_reference_vs_value_for_pattern_objects():
    p1 = ref_object("P1", Node("p1", OBSERVATION, (NodeRef("a"), NodeRef("b"))))
    p2 = ref_object("P2", Node("p2", OBSERVATION, (NodeRef("a"), NodeRef("b"))))
    assert not reference_equal(p1, p2)
    assert structural_equal(p1, p2)


if __name__ == "__main__":
    tests = [
        test_reference_equality_discovered,
        test_same_payload_different_refs_not_merged,
        test_generic_compare_permutation,
        test_replay_uniform_permutation,
        test_ambiguous_or_unidentified_is_not_forced,
        test_provenance_is_mechanical,
        test_reference_vs_value_for_pattern_objects,
    ]
    results = []
    for t in tests:
        try:
            t(); results.append({"test": t.__name__, "status": "PASS"})
        except Exception as e:
            results.append({"test": t.__name__, "status": "FAIL", "error": repr(e)})
    out = {
        "suite": "MetaHIA E20-D v0.2",
        "passed": sum(r["status"] == "PASS" for r in results),
        "failed": sum(r["status"] == "FAIL" for r in results),
        "tests": results,
    }
    out_path = Path(__file__).with_name("TEST_RESULTS_E20D_V0_2.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
