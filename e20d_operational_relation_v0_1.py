"""E20-D.14 — Generic operational relation discovery over paths/properties.

This module is deliberately additive to the K3 core. It does not introduce
semantic relation dictionaries. It consumes structural objects already
produced by kernel2.py and creates a replayable relation record describing
how two such objects compare at the property/operation level.

The relation is itself reifiable as an ordinary reference-bearing structure.
Identity, structure and external payload remain distinct.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from kernel2 import (
    PathPattern,
    PathPropertyObject,
    PathRecord,
    PathProperties,
    RefObject,
    NodeRef,
    reference_equal,
    structural_equal,
    structural_signature,
    path_properties,
    path_property_structural_form,
    path_pattern_structural_form,
)

RELATION_MARKER = "OPERATIONAL_RELATION"
REL_EQUAL = "EQUAL"
REL_DIFFERENT = "DIFFERENT"
REL_SAME_KEY = "SAME_KEY"


@dataclass(frozen=True)
class OperationalFieldRelation:
    """Comparison of one named structural property field.

    The field name comes from the structural property extractor, not from a
    domain ontology. The relation token is a generic structural outcome.
    """
    key: object
    relation: str
    left_value: object
    right_value: object

    def structural_form(self) -> Tuple[object, ...]:
        return (
            "FIELD_RELATION",
            structural_signature(self.key),
            self.relation,
            structural_signature(self.left_value),
            structural_signature(self.right_value),
        )


@dataclass(frozen=True)
class OperationalRelationRecord:
    """Replayable relation discovered between two structural objects."""
    relation_id: str
    left_ref: Optional[NodeRef]
    right_ref: Optional[NodeRef]
    basis: str
    fields: Tuple[OperationalFieldRelation, ...]
    relation_kind: str
    provenance: Tuple[str, ...]

    def structural_form(self) -> Tuple[object, ...]:
        return (
            RELATION_MARKER,
            self.basis,
            self.relation_kind,
            tuple(field.structural_form() for field in self.fields),
        )


def _object_ref(obj: object) -> Optional[NodeRef]:
    if isinstance(obj, RefObject):
        return obj.ref
    if isinstance(obj, PathRecord):
        return NodeRef(obj.path_id)
    if isinstance(obj, PathPropertyObject):
        return NodeRef(obj.property_id)
    if isinstance(obj, PathPattern):
        return NodeRef(obj.pattern_id)
    if isinstance(obj, NodeRef):
        return obj
    return None


def _provenance(obj: object) -> Tuple[str, ...]:
    if isinstance(obj, (PathRecord, PathPropertyObject, PathProperties, PathPattern)):
        return tuple(obj.provenance) if hasattr(obj, "provenance") else tuple()
    if isinstance(obj, RefObject):
        structure = obj.structure
        if isinstance(structure, tuple) and len(structure) > 0:
            return tuple()
    return tuple()


def _property_map(obj: object) -> Dict[object, object]:
    """Extract semantic-free structural properties from a supported object."""
    if isinstance(obj, PathPropertyObject):
        return {obj.key: obj.value}
    if isinstance(obj, PathProperties):
        return {p.key: p.value for p in obj.as_objects()}
    if isinstance(obj, PathRecord):
        props = path_properties(obj)
        return {p.key: p.value for p in props.as_objects()}
    if isinstance(obj, PathPattern):
        return {
            "length": obj.length,
            "operator_sequence": obj.operator_sequence,
            "direction_sequence": obj.direction_sequence,
            "node_binding": obj.node_binding,
            "position_groups": obj.position_groups,
        }
    if isinstance(obj, RefObject):
        structure = obj.structure
        if isinstance(structure, tuple) and len(structure) >= 1:
            # Generic reified structural object. We intentionally compare the
            # entire denoted structure as one opaque property.
            return {"structure": structure}
    raise TypeError(f"unsupported operational-relation object: {type(obj).__name__}")


def discover_operational_relation(
    left: object,
    right: object,
    relation_id: Optional[str] = None,
) -> Optional[OperationalRelationRecord]:
    """Discover a generic structural relation between two objects.

    No semantic names are inferred. The function aligns common structural
    property keys and records EQUAL/DIFFERENT outcomes. If there is no common
    structural basis at all, it fails closed with None.
    """
    left_map = _property_map(left)
    right_map = _property_map(right)
    common_keys = sorted(set(left_map).intersection(right_map), key=repr)
    if not common_keys:
        return None

    fields = []
    for key in common_keys:
        lv = left_map[key]
        rv = right_map[key]
        fields.append(
            OperationalFieldRelation(
                key=key,
                relation=REL_EQUAL if structural_equal(lv, rv) else REL_DIFFERENT,
                left_value=lv,
                right_value=rv,
            )
        )

    different_count = sum(f.relation == REL_DIFFERENT for f in fields)
    relation_kind = "STRUCTURAL_EQUIVALENCE" if different_count == 0 else "STRUCTURAL_RELATION"
    prov = []
    for source in _provenance(left) + _provenance(right):
        if source not in prov:
            prov.append(source)

    return OperationalRelationRecord(
        relation_id=relation_id or f"oprel::{_object_ref(left)}::{_object_ref(right)}",
        left_ref=_object_ref(left),
        right_ref=_object_ref(right),
        basis="COMMON_STRUCTURAL_PROPERTIES",
        fields=tuple(fields),
        relation_kind=relation_kind,
        provenance=tuple(prov),
    )


def reify_operational_relation(
    relation: OperationalRelationRecord,
    ref_id: Optional[str] = None,
) -> RefObject:
    """Reify an operational relation without collapsing identity and structure."""
    return RefObject(
        NodeRef(ref_id or relation.relation_id),
        relation.structural_form(),
    )


def operational_relation_structural_equal(
    left: OperationalRelationRecord,
    right: OperationalRelationRecord,
) -> bool:
    """Compare relation structures while ignoring identity/provenance metadata."""
    return left.structural_form() == right.structural_form()
