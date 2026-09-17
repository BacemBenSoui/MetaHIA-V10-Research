from e20d_property_discovery_v0_1 import (
    behavior_case, discover_arity, discover_fixed_point,
    discover_output_invariance_under_swap, build_discovered_property,
)
from kernel2 import NodeRef, structural_equal, reference_equal


def test_arity_is_discovered_from_observations_only():
    cases = [
        behavior_case("c1", "O", [NodeRef("a"), NodeRef("b")], NodeRef("r1")),
        behavior_case("c2", "O", [NodeRef("c"), NodeRef("d")], NodeRef("r2")),
    ]
    assert discover_arity(cases) == 2


def test_mixed_arity_fails_closed():
    cases = [
        behavior_case("c1", "O", [NodeRef("a")], NodeRef("r1")),
        behavior_case("c2", "O", [NodeRef("b"), NodeRef("c")], NodeRef("r2")),
    ]
    assert discover_arity(cases) is None


def test_fixed_point_uses_reference_identity_not_value():
    same = NodeRef("x")
    assert discover_fixed_point([behavior_case("c", "O", [same], same)]) is True
    assert discover_fixed_point([behavior_case("c", "O", [NodeRef("x")], NodeRef("x2"))]) is False


def test_swap_invariance_is_discovered_structurally():
    r = NodeRef("r")
    cases = [
        behavior_case("ab", "O", [NodeRef("a"), NodeRef("b")], r),
        behavior_case("ba", "O", [NodeRef("b"), NodeRef("a")], r),
    ]
    p = discover_output_invariance_under_swap(cases)
    assert p is not None
    assert p.kind == "INVARIANT"


def test_swap_invariance_requires_same_output_reference_or_structure():
    cases = [
        behavior_case("ab", "O", [NodeRef("a"), NodeRef("b")], NodeRef("r1")),
        behavior_case("ba", "O", [NodeRef("b"), NodeRef("a")], NodeRef("r2")),
    ]
    assert discover_output_invariance_under_swap(cases) is None


def test_property_object_is_reified_and_reference_bearing():
    cases = [
        behavior_case("ab", "O", [NodeRef("a"), NodeRef("b")], NodeRef("r")),
        behavior_case("ba", "O", [NodeRef("b"), NodeRef("a")], NodeRef("r")),
    ]
    obj = build_discovered_property(cases, property_ref_id="PROP::P1")
    assert obj is not None
    assert obj.ref == NodeRef("PROP::P1")
    assert obj.structure.kind == "PROPERTY_DISCOVERY"


def test_different_property_refs_can_have_same_derived_structure():
    cases = [
        behavior_case("ab", "O", [NodeRef("a"), NodeRef("b")], NodeRef("r")),
        behavior_case("ba", "O", [NodeRef("b"), NodeRef("a")], NodeRef("r")),
    ]
    a = build_discovered_property(cases, property_ref_id="P1")
    b = build_discovered_property(cases, property_ref_id="P2")
    assert a is not None and b is not None
    assert reference_equal(a, b) is False
    assert structural_equal(a, b) is True
