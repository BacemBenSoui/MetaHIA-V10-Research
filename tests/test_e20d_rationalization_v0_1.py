import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel2 import Node, NodeRef, OBSERVATION, ref_object, structural_equal, reference_equal
from e20d_rationalization_v0_1 import (
    GENERATED, UNKNOWN, SUPPORTED_HISTORICAL,
    ref_jaccard, structural_similarity, rationalize, remember_rationalization,
)


def op_struct(ref_id, op, props):
    return ref_object(ref_id, Node(
        f"p::{ref_id}", OBSERVATION,
        (NodeRef(op), Node("props", "PROPS", tuple(NodeRef(p) for p in props)))
    ))


def test_exact_structure_scores_one():
    a = op_struct("A", "opaque1", ["p1", "p2"])
    b = op_struct("B", "opaque1", ["p1", "p2"])
    assert structural_similarity(a.structure, b.structure) == 1.0


def test_approximate_similarity_is_not_identity():
    a = op_struct("A", "opaque1", ["p1", "p2", "p3"])
    b = op_struct("B", "opaque1", ["p1", "p2", "p4"])
    s = structural_similarity(a.structure, b.structure)
    assert 0.0 < s < 1.0
    assert not structural_equal(a, b)
    assert not reference_equal(a, b)


def test_high_similarity_can_be_historical_support():
    props = [f"p{i}" for i in range(97)]
    generated = op_struct("GEN", "new", props)
    historical = op_struct("HIST", "known", props)
    r = rationalize(generated, [historical], threshold=0.97)
    assert r is not None
    assert r.status == SUPPORTED_HISTORICAL
    assert r.generated.ref.ref_id == "GEN"
    assert r.historical.ref.ref_id == "HIST"


def test_low_similarity_stays_unknown():
    generated = op_struct("GEN", "new", ["a", "b", "c"])
    historical = op_struct("HIST", "known", ["x", "y", "z"])
    r = rationalize(generated, [historical], threshold=0.97)
    assert r is not None
    assert r.status == UNKNOWN


def test_source_structure_is_never_rewritten():
    props = [f"p{i}" for i in range(97)]
    generated = op_struct("GEN", "new", props)
    before = generated.structure
    historical = op_struct("HIST", "known", props)
    r = rationalize(generated, [historical], threshold=0.97)
    assert generated.structure == before
    assert r.generated.structure == before


def test_historical_memory_is_separate_reified_object():
    props = [f"p{i}" for i in range(97)]
    generated = op_struct("GEN", "new", props)
    historical = op_struct("HIST", "known", props)
    r = rationalize(generated, [historical], threshold=0.97)
    mem = remember_rationalization(r)
    assert mem.ref.ref_id.startswith("RAT::")
    assert mem.structure.children[0] == NodeRef("GEN")
    assert mem.structure.children[1] == NodeRef("HIST")


def test_empty_reference_sets_are_exactly_similar():
    a = Node("a", "EMPTY", ())
    b = Node("b", "EMPTY", ())
    assert ref_jaccard(a, b) == 1.0
