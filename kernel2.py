"""K3 spike (E13-A.2) — minimal recursive Compare, implemented in code.

Isolated research spike (2026-09-16), testing empirically the K3 hypothesis
(Node / Apply / Compare) described in a ChatGPT discussion export (see
documentation/... discussion analysis and research/k3_spike_e13a2/README.md).
Nothing here is imported by, or a dependency of, structural/, metahia_m1, or
any other production package — the reverse is also true, this module imports
nothing from production code.

Constraints honored, verbatim from the source discussion's own E13-A.2 spec:
  - no hardcoded operator-property detector exists anywhere in this module;
    the structural mechanism works only with opaque labels and generic mappings.
  - no `abstract()` kernel primitive — abstraction (going from a pattern tied
    to one concrete operator to one that holds across several) is produced by
    calling the SAME `compare()` entry point again on its own prior output
    (PATTERN nodes), not by a separate bespoke mechanism.
  - no domain/semantic dictionary of any kind — labels are opaque strings;
    the engine never inspects what a label "means", only whether two labels
    are structurally equal.
  - M1 v0.4 and structural/ are untouched; this spike does not import from,
    or write into, either.
  - Reference/value separation is an architectural invariant: structural
    identity is carried by NodeRef; calculated objects may be wrapped in
    RefObject (`*P = f(*A,*B,...)`) so identity and denoted structure remain
    independently comparable. The same rule applies recursively to patterns,
    transformations and meta-structures.

2026-09-16 addendum (Apply unification): `apply_pattern()` (PATTERN nodes)
and `apply_tree_shape()` (SHAPE_PATTERN nodes, added for E18) were two
separate application entry points, with no function able to accept either
kind of discovered pattern. `apply()` below is the single public Apply
entry point (K3's Apply: Node^n -> Node), added to mirror compare() as the
single Compare entry point. It dispatches purely on `pattern.kind` and
changes neither `apply_pattern()` nor `apply_tree_shape()` -- see its
docstring for exactly what this does and does not unify.

E20-D.8 addendum (2026-09-17): derived properties and meta-structures are
represented without introducing a rigid PROPERTY/METASTRUCTURE ontology. Any
calculated object may remain a RefObject whose denoted structure can be used
as an operand of the same generic Apply/Compare mechanisms. `apply_operator()`
provides the constructor form of Apply, and `apply()` overloads this form while
preserving existing PATTERN/SHAPE_PATTERN application. Internal R-V-1
comparisons use `_kernel_values_equal()`; same-reference/different-structure
inconsistency fails loudly. Recurrent shape analysis may see through a
RefObject envelope only when its denoted body is the same-operator recurrent
application under analysis.


E20-D.18 addendum (2026-09-17): structural closure is now represented by
materializing a reified LINK as an ordinary binary K3 application and by an
additive `reinject_reified_links()` graph operation. The generated link remains
an opaque reference-bearing operator; no semantic relation name is inferred.
This creates an explicit one-step closure bridge from generated structures back
into Graph/Path exploration while keeping further recursion subject to the
cognitive/ROI layer.

E20-D.14 addendum (2026-09-17): preflight maintenance corrected two generic
Compare invariants: identical structures now return None rather than an
identity SHAPE_PATTERN, and `_compare_observations()` uses `_kernel_values_equal()`
for reference-aware difference detection. This is maintenance of the existing
K3 invariants, not a new primitive. The E20-D.14 operational relation layer is
implemented additively outside the K3 ontology: it consumes path/path-property
structures and produces a replayable relation record without assigning semantic
meaning to the relation.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Dict, Iterable, List, Optional, Tuple

# Pointer/identity mode: NodeRef carries only an opaque reference id.
# Kernel operations must not dereference or compare external payload values.

OBSERVATION = "OBSERVATION"
PATTERN = "PATTERN"


@dataclass(frozen=True)
class NodeRef:
    """Opaque reference to a Node/value identity.

    The kernel compares NodeRef instances only by ref_id. The referenced
    payload/value is intentionally outside the kernel and is never inspected
    by Node/Apply/Compare operations. Reusing the same NodeRef means the same
    structural object; different NodeRefs remain distinct even if their
    external payloads happen to be equal.
    """
    ref_id: str

    def __repr__(self) -> str:
        return f"*{self.ref_id}"


def node_ref(ref_id: str) -> NodeRef:
    """Construct an opaque structural reference."""
    return NodeRef(ref_id)


@dataclass(frozen=True)
class RefObject:
    """A referencable calculated structural object.

    `ref` is the object's identity; `structure` is the object it denotes.
    The identity is independent from the structure, and the structure is
    independent from any external payload/value. This is the generic form of
    the proposed notation:

        *P = f(*A, *B, ...)

    Two RefObjects can therefore satisfy any of the following independently:

        reference_equal(a, b)  -> same object identity
        structural_equal(a, b) -> equivalent denoted structure

    The kernel never dereferences NodeRef through an external payload store.
    `structure` must itself be a kernel structural object (normally Node,
    NodeRef, RefObject, tuple, PatternSlot, ShapeTerm, or a scalar kernel
    marker).
    """
    ref: NodeRef
    structure: object


@dataclass(frozen=True, init=False)
class PatternRef(RefObject):
    """Reference-bearing wrapper for any kernel pattern representation.

    This is the POO-style constructor extension used for E20-D: the caller
    constructs one logical ``PatternRef`` regardless of whether the body is
    represented internally as PATTERN or SHAPE_PATTERN. The internal body is
    preserved unchanged; only the public reference-bearing envelope is
    unified.

        *P = f(*A, *B, ...)

    ``pattern`` must be a kernel Node whose kind is PATTERN or SHAPE_PATTERN.
    """

    def __init__(self, ref_id: str | NodeRef, pattern: Node):
        ref = ref_id if isinstance(ref_id, NodeRef) else NodeRef(ref_id)
        if not isinstance(pattern, Node):
            raise TypeError("PatternRef requires a Node pattern body")
        if pattern.kind not in (PATTERN, SHAPE_PATTERN):
            raise ValueError(
                "PatternRef requires a PATTERN or SHAPE_PATTERN body, "
                f"got {pattern.kind!r}"
            )
        object.__setattr__(self, "ref", ref)
        object.__setattr__(self, "structure", pattern)

    @property
    def kind(self) -> str:
        return self.structure.kind

    @property
    def pattern(self) -> Node:
        return self.structure


def ref_object(ref_id: str, structure: object) -> RefObject:
    """Create a referencable structural object.

    Constructor overload by structural kind: pattern bodies are automatically
    wrapped in PatternRef, while all other kernel structures retain the
    historical RefObject behavior. This preserves backward compatibility and
    extends the constructor path without adding semantic knowledge.
    """
    if isinstance(structure, Node) and structure.kind in (PATTERN, SHAPE_PATTERN):
        return PatternRef(ref_id, structure)
    return RefObject(NodeRef(ref_id), structure)


def pattern_ref(ref_id: str | NodeRef, pattern: Node) -> PatternRef:
    """Explicit constructor for a unified reference-bearing pattern."""
    return PatternRef(ref_id, pattern)


def reference_equal(a: object, b: object) -> bool:
    """Strong identity equality: same reference id, nothing about payload.

    Only references are compared. Distinct references remain distinct even
    when they denote structurally identical objects or carry equal external
    payloads.
    """
    if isinstance(a, NodeRef) and isinstance(b, NodeRef):
        return a.ref_id == b.ref_id
    if isinstance(a, RefObject) and isinstance(b, RefObject):
        return a.ref.ref_id == b.ref.ref_id
    return False


def _reference_consistency(a: object, b: object) -> str:
    """Three-way reference-vs-structure verdict underlying `_kernel_values_equal`.

    Returns "EQUAL" (same reference, and same structure for RefObject), or
    "DIFFERENT" (distinct references, or a reference compared against a
    non-reference value -- never equal regardless of payload). Raises
    ValueError when the same reference id is reused for two different denoted
    structures (an object-identity inconsistency, not a mere inequality).
    """
    if isinstance(a, NodeRef) and isinstance(b, NodeRef):
        return "EQUAL" if reference_equal(a, b) else "DIFFERENT"
    if isinstance(a, RefObject) and isinstance(b, RefObject):
        same_ref = reference_equal(a, b)
        same_structure = structural_equal(a, b)
        if same_ref and same_structure:
            return "EQUAL"
        if not same_ref:
            return "DIFFERENT"
        raise ValueError(
            f"R-V-1 reference inconsistency: {a.ref.ref_id!r} "
            "claims structurally different objects"
        )
    return "DIFFERENT"


def _kernel_values_equal(a: object, b: object) -> bool:
    """Three-way-aware equality used inside kernel decision primitives.

    R-V-1 requires internal comparisons to distinguish reference identity from
    structural equivalence. For two RefObjects carrying the same reference id,
    a structural mismatch means the two objects claim one identity for two
    different structures: this is an internal inconsistency and must fail
    loudly with ValueError. Distinct references are DIFFERENT regardless of
    structure: a same value carried by two distinct references does not create
    coreference (fixed 2026-09-17 -- the previous revision fell through to a
    structural comparison for distinct references, silently treating two
    different-reference RefObjects with coincidentally-equal structure as
    EQUAL, in violation of this same invariant). Bare NodeRef values compare
    only by ref_id. All other values delegate to the recursive structural
    comparator.

    This helper is intentionally private: K3 exposes Node/Apply/Compare, while
    the invariant is enforced consistently inside their decision paths.
    """
    if isinstance(a, (NodeRef, RefObject)) or isinstance(b, (NodeRef, RefObject)):
        return _reference_consistency(a, b) == "EQUAL"
    return structural_equal(a, b)


def structural_equal(a: object, b: object) -> bool:
    """Reference-aware structural equality, deliberately not identity.

    For RefObject, the reference id is ignored and the denoted kernel
    structures are compared recursively. NodeRef remains identity-bearing, so
    two distinct NodeRefs are structurally different even if an external
    payload system happened to assign them equal values.
    """
    if isinstance(a, RefObject) and isinstance(b, RefObject):
        return structural_equal(a.structure, b.structure)
    if isinstance(a, NodeRef) or isinstance(b, NodeRef):
        return reference_equal(a, b)
    if isinstance(a, Node) and isinstance(b, Node):
        return (
            a.kind == b.kind
            and len(a.children) == len(b.children)
            and all(structural_equal(x, y) for x, y in zip(a.children, b.children))
        )
    if isinstance(a, PatternSlot) and isinstance(b, PatternSlot):
        return (
            a.source_position == b.source_position
            and structural_equal(a.literal_constraint, b.literal_constraint)
            and structural_equal(a.nested_pattern, b.nested_pattern)
            and a.requires_source_equal == b.requires_source_equal
        )
    if isinstance(a, ShapeTerm) and isinstance(b, ShapeTerm):
        return (
            a.kind == b.kind
            and structural_equal(a.value, b.value)
            and len(a.children) == len(b.children)
            and all(structural_equal(x, y) for x, y in zip(a.children, b.children))
        )
    if isinstance(a, ShapeRewrite) and isinstance(b, ShapeRewrite):
        return (
            structural_equal(a.source, b.source)
            and structural_equal(a.target, b.target)
            and a.arity == b.arity
            and a.output_passthrough == b.output_passthrough
        )
    if isinstance(a, PathPropertyObject) and isinstance(b, PathPropertyObject):
        # Property identity/provenance are metadata; structural equality is
        # determined only by the property key/value pair. This permits the
        # same structural property to be compared across independently
        # discovered paths without collapsing their reference identities.
        return (
            structural_equal(a.key, b.key)
            and structural_equal(a.value, b.value)
        )
    if isinstance(a, PathProperties) and isinstance(b, PathProperties):
        return path_properties_structural_form(a) == path_properties_structural_form(b)
    if isinstance(a, tuple) and isinstance(b, tuple):
        return len(a) == len(b) and all(structural_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(structural_equal(x, y) for x, y in zip(a, b))
    return a == b


def _canonical_pattern_term(term: ShapeTerm):
    """Canonicalize a ShapeTerm without using payload/value identity."""
    if term.kind == "VAR":
        if term.value == 0:
            return ("OPERATOR", 0)
        return ("VAR", term.value)
    if term.kind == "APPLY":
        return (
            "APPLY",
            _canonical_pattern_term(term.value),
            tuple(_canonical_pattern_term(x) for x in term.children),
        )
    return (term.kind, term.value, tuple(_canonical_pattern_term(x) for x in term.children))


def _pattern_slots_tree_signature(pattern: Node):
    """Lift a pure position-mapping PATTERN into the common rewrite space."""
    arity = len(pattern.children)
    if arity < 1:
        return None
    source_vars = tuple(("VAR", i + 1) for i in range(arity))
    target_vars = []
    for slot in pattern.children:
        if not isinstance(slot, PatternSlot):
            return None
        if slot.literal_constraint is not None or slot.nested_pattern is not None:
            return None
        if slot.requires_source_equal:
            return None
        if not isinstance(slot.source_position, int) or not 0 <= slot.source_position < arity:
            return None
        target_vars.append(("VAR", slot.source_position + 1))
    # Operator is deliberately represented as an opaque common placeholder.
    op = ("OPERATOR", 0)
    return (
        "REWRITE_TREE",
        arity,
        ("APPLY", op, source_vars),
        ("APPLY", op, tuple(target_vars)),
        True,
    )


def _canonical_shape_rewrite_signature(rw: ShapeRewrite):
    """Canonicalize a shape rewrite when it is an ordinary arity-preserving map."""
    source = _canonical_pattern_term(rw.source)
    target = _canonical_pattern_term(rw.target)
    return ("REWRITE_TREE", rw.arity, source, target, bool(rw.output_passthrough))


def _pattern_unified_signature(pattern: Node):
    """Return a common structural signature for PATTERN and SHAPE_PATTERN.

    A pure PATTERN position mapping is lifted into the same rewrite language
    as a ShapeRewrite. More general PATTERN literals/nested structures retain
    their own structural signature and are not forced into this equivalence.
    No semantic labels are interpreted.
    """
    pattern = resolve_structure(pattern)
    if not isinstance(pattern, Node):
        return None
    if pattern.kind == PATTERN:
        lifted = _pattern_slots_tree_signature(pattern)
        if lifted is not None:
            return lifted
        slots = []
        for pos, slot in enumerate(pattern.children):
            if not isinstance(slot, PatternSlot):
                return None
            nested = _pattern_unified_signature(slot.nested_pattern) if slot.nested_pattern is not None else None
            if nested is not None:
                target = ("NESTED", nested)
            elif slot.literal_constraint is not None:
                target = ("LITERAL", structural_signature(slot.literal_constraint))
            else:
                target = ("VAR_REF", slot.source_position)
            slots.append((pos, target, bool(slot.requires_source_equal)))
        return ("REWRITE_SLOTS", tuple(slots))
    if pattern.kind == SHAPE_PATTERN:
        if len(pattern.children) != 1 or not isinstance(pattern.children[0], ShapeRewrite):
            return None
        return _canonical_shape_rewrite_signature(pattern.children[0])
    return None


def structural_signature(obj: object):
    """Canonical structural signature used only for structure comparison.

    A RefObject is deliberately handled *before* generic resolution so its
    reference-bearing envelope remains visible in the ordinary structural
    signature. This preserves the distinction between a bare denoted body and
    a calculated object that has acquired its own identity. PatternRef uses
    the same envelope rule.
    """
    if isinstance(obj, NodeRef):
        return ("REF", obj.ref_id)
    if isinstance(obj, RefObject):
        body_sig = _pattern_unified_signature(obj.structure) or structural_signature(obj.structure)
        return ("REF_OBJECT", obj.ref.ref_id, body_sig)
    obj = resolve_structure(obj)
    if isinstance(obj, Node):
        if obj.kind in (PATTERN, SHAPE_PATTERN):
            return _pattern_unified_signature(obj)
        return (obj.kind, tuple(structural_signature(x) for x in obj.children))
    if isinstance(obj, PatternSlot):
        return (
            "SLOT", obj.source_position, structural_signature(obj.literal_constraint),
            structural_signature(obj.nested_pattern), bool(obj.requires_source_equal)
        )
    if isinstance(obj, ShapeTerm):
        return _canonical_pattern_term(obj)
    if isinstance(obj, ShapeRewrite):
        return (
            "REWRITE", obj.arity, _canonical_pattern_term(obj.source),
            _canonical_pattern_term(obj.target), bool(obj.output_passthrough)
        )
    if isinstance(obj, PathPropertyObject):
        return ("PATH_PROPERTY", structural_signature(obj.key), structural_signature(obj.value))
    if isinstance(obj, PathProperties):
        return path_properties_structural_form(obj)
    if isinstance(obj, tuple):
        return tuple(structural_signature(x) for x in obj)
    if isinstance(obj, list):
        return tuple(structural_signature(x) for x in obj)
    return obj


def pattern_structural_equal(a: object, b: object) -> bool:
    """Cross-representation structural equality for referenced patterns."""
    a = resolve_structure(a)
    b = resolve_structure(b)
    if not isinstance(a, Node) or not isinstance(b, Node):
        return False
    if a.kind not in (PATTERN, SHAPE_PATTERN) or b.kind not in (PATTERN, SHAPE_PATTERN):
        return False
    sa = _pattern_unified_signature(a)
    sb = _pattern_unified_signature(b)
    return sa is not None and sb is not None and sa == sb


def compare_pattern_references(a: object, b: object) -> Optional[bool]:
    """Compare two referenced pattern objects across internal representations.

    ``True`` means structurally equivalent, ``False`` means structurally
    comparable but different, and ``None`` means the two bodies cannot be
    lifted into a common representation without losing information.
    """
    a = resolve_structure(a)
    b = resolve_structure(b)
    if not isinstance(a, Node) or not isinstance(b, Node):
        return None
    if a.kind not in (PATTERN, SHAPE_PATTERN) or b.kind not in (PATTERN, SHAPE_PATTERN):
        return None
    sa = _pattern_unified_signature(a)
    sb = _pattern_unified_signature(b)
    if sa is None or sb is None:
        return None
    return sa == sb


@dataclass(frozen=True)
class Node:
    """A generic, opaquely-labeled structural object.

    kind="OBSERVATION": children may contain opaque NodeRef objects. In
        pointer mode, structural identity is carried by NodeRef.ref_id;
        external payload values are never inspected by the kernel.
        Raw strings remain supported for backwards compatibility.
    kind="PATTERN": children is a tuple of PatternSlot, one per position,
        produced by compare() — never authored by hand in this spike. A
        complete Pattern can itself be wrapped in RefObject for identity-
        separate recursive composition.
    """
    node_id: str
    kind: str
    children: Tuple[object, ...]
    provenance: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternSlot:
    """One position of a Pattern node.

    source_position: which position of an OBSERVATION to read when applying
        this pattern (equal to this slot's own position for a position that
        is simply copied through unchanged; a different position for one
        that gets permuted).
    literal_constraint: if set, an observation must carry exactly this label
        at this position for the pattern to apply (None = fully free/general).
        Usually a str, but can hold a Node when a frozen position happens to
        be an identical nested OBSERVATION on both sides (E15).
    nested_pattern: set (E15) when this position's difference between the two
        observations Compare was discovered from is itself explained by a
        recursive Compare on a composite (Node-valued) child, rather than by
        permuting it against another top-level position. Mutually exclusive
        with permuting this slot against a different source_position:
        source_position is this slot's own position (self) when set.
    requires_source_equal: FIX (2026-09-16, confirmed silent-misapplication
        gap -- see probe6_e19_aggregate.py). `compare()`'s permutation slots
        and `aggregate_observations()`'s dependency slots both express
        "source_position != own position, literal_constraint=None" but mean
        different things: for a compare()-discovered permutation, that just
        means "copy this value from over there" -- any value is fine, no
        precondition needed. For an aggregate_observations()-discovered
        column dependency, it means "position `source_position` must equal
        THIS position's own value in any observation this pattern legitimately
        describes" -- a real invariant, not a free relabeling. Reusing
        PatternSlot for both without distinguishing them made
        pattern_is_applicable() silently report True (and apply_pattern()
        silently produce a nonsensical prediction) for an observation that
        violates a discovered dependency, e.g. Z(FOO, K9, BAR) against a
        Z(x, K9) = x pattern discovered from Z(A,K9)=A / Z(B,K9)=B / Z(C,K9)=C.
        Set to True ONLY by aggregate_observations(); compare() never sets it,
        so every already-validated E13-A.2..E17 pattern is completely
        unaffected (see probe4_replay_our_suite.py, rerun after this fix).
    """
    source_position: int
    literal_constraint: Optional[object] = None
    nested_pattern: Optional[Node] = None
    requires_source_equal: bool = False


@dataclass(frozen=True)
class ShapeTerm:
    """Generic structural template used for recursive tree rewrites.

    kind: VAR, APPLY, or OUTPUT. For APPLY, operator and children are carried
    structurally. Variables are numeric references into the flattened argument
    sequence produced from an observation.
    """
    kind: str
    value: object = None
    children: Tuple[object, ...] = ()


SHAPE_PATTERN = "SHAPE_PATTERN"


@dataclass(frozen=True)
class ShapeRewrite:
    source: ShapeTerm
    target: ShapeTerm
    arity: int
    output_passthrough: bool = True


def resolve_structure(obj: object) -> object:
    """Resolve only a kernel-owned RefObject to its denoted structure.

    This is deliberately different from dereferencing a bare NodeRef: a
    NodeRef has no payload in the kernel and therefore cannot be resolved here.
    RefObject carries both an opaque identity and a kernel structural body, so
    recursive Compare/Apply can operate on the body without coupling identity
    to value.
    """
    return obj.structure if isinstance(obj, RefObject) else obj


def _flatten_recurrent_args(node: Node):
    """Purely structural canonicalization of nested applications.

    A child Node is expanded only when it is an OBSERVATION whose first child
    is the same opaque operator reference as the enclosing operator. A
    RefObject/PatternRef around such a child is an identity-bearing envelope,
    not a semantic barrier: when its denoted structure is a same-operator
    recurrent application, the structural view is allowed to see through the
    envelope. The reference identity remains available on the original object
    and is not confused with the denoted structure.

    This deliberately closes the E18 reserve discovered on 2026-09-16:
    RefObject(O(A,B)) must not become an opaque leaf for recurrent shape
    analysis when the envelope is only a reference-bearing wrapper around the
    recurrent structure itself.
    """
    node = resolve_structure(node)
    if not isinstance(node, Node) or node.kind != OBSERVATION or len(node.children) < 2:
        return [], None
    op = node.children[0]
    args = node.children[1:-1]
    out = node.children[-1]
    flat=[]
    for arg in args:
        resolved = resolve_structure(arg)
        if (
            isinstance(resolved, Node)
            and resolved.kind == OBSERVATION
            and len(resolved.children) >= 2
            and structural_equal(resolved.children[0], op)
        ):
            inner, _ = _flatten_recurrent_args(resolved)
            flat.extend(inner)
        else:
            flat.append(arg)
    return flat, out


def _flatten_recurrent_args_distinct(node: Node):
    """Deduplicated counterpart to `_flatten_recurrent_args`, mirroring the
    variable numbering `_shape_template` assigns: a repeated NodeRef/RefObject
    identity collapses to a single slot (first-appearance order), while raw
    non-reference leaves are never deduplicated -- exactly `bind_reference`
    vs `bind_leaf`'s split there.

    `apply_tree_shape` must index a SHAPE_PATTERN's VAR numbers against this
    list, not the raw `_flatten_recurrent_args` output: the template's VAR
    numbers already refer to distinct slots, so indexing the raw (longer,
    non-deduplicated) list off-by-shifts every VAR after a repeated reference,
    silently dropping trailing arguments and duplicating the repeated one
    instead of preserving coreference (fixed 2026-09-17, caught by
    `test_noderef_coreference_discovered_and_applied_correctly_end_to_end`).
    """
    node = resolve_structure(node)
    if not isinstance(node, Node) or node.kind != OBSERVATION or len(node.children) < 2:
        return [], None
    op = node.children[0]
    args = node.children[1:-1]
    out = node.children[-1]
    distinct: list = []
    seen_ref_ids: set = set()

    def _walk(value):
        resolved = resolve_structure(value)
        if (
            isinstance(resolved, Node)
            and resolved.kind == OBSERVATION
            and len(resolved.children) >= 2
            and structural_equal(resolved.children[0], op)
        ):
            for inner in resolved.children[1:-1]:
                _walk(inner)
            return
        ref = value.ref if isinstance(value, RefObject) else value if isinstance(value, NodeRef) else None
        if ref is not None:
            if ref.ref_id not in seen_ref_ids:
                seen_ref_ids.add(ref.ref_id)
                distinct.append(value)
            return
        distinct.append(value)

    for arg in args:
        _walk(arg)
    return distinct, out


def _shape_template(node: Node):
    """Build a generic tree template using structural bindings.

    In pointer mode, repeated NodeRef identities are bound to the SAME
    structural variable, while different NodeRefs remain different even if
    their external payloads are equal.

    This is deliberately based on reference identity, never payload/value
    equality. A single observation may therefore carry an explicit
    coreference such as:

        O(O(*P,*P),*X)

    which becomes:

        O(O(V1,V1),V2)

    whereas:

        O(O(*P1,*P2),*X)

    becomes:

        O(O(V1,V2),V3)

    even when the external payloads of *P1 and *P2 are identical.

    Raw strings remain supported for backwards compatibility. In that legacy
    mode, each leaf occurrence receives a fresh variable exactly as before;
    callers that need explicit identity should use NodeRef.
    """
    if node.kind != OBSERVATION or len(node.children) < 2:
        raise ValueError("shape template requires an observation application")

    op = node.children[0]
    next_leaf_var = [0]
    ref_variable_map = {}

    def bind_leaf(value):
        next_leaf_var[0] += 1
        return ShapeTerm("VAR", next_leaf_var[0])

    def bind_reference(ref):
        if ref.ref_id not in ref_variable_map:
            next_leaf_var[0] += 1
            ref_variable_map[ref.ref_id] = next_leaf_var[0]
        return ShapeTerm("VAR", ref_variable_map[ref.ref_id])

    def rec(value):
        resolved = resolve_structure(value)
        if (
            isinstance(resolved, Node)
            and resolved.kind == OBSERVATION
            and len(resolved.children) >= 2
            and structural_equal(resolved.children[0], op)
        ):
            return ShapeTerm(
                "APPLY",
                ShapeTerm("VAR", 0),
                tuple(rec(x) for x in resolved.children[1:-1])
            )
        if isinstance(value, RefObject):
            # A RefObject is a calculated object whose identity is carried by
            # its NodeRef. When its denoted body is a recurrent same-operator
            # application, the structural view may expand that body; otherwise
            # the reference itself remains the structural leaf.
            return bind_reference(value.ref)
        if isinstance(value, NodeRef):
            return bind_reference(value)
        return bind_leaf(value)

    return ShapeTerm(
        "APPLY",
        ShapeTerm("VAR", 0),
        tuple(rec(x) for x in node.children[1:-1])
    )


def _same_shape_signature(a: Node, b: Node):
    if a.kind != OBSERVATION or b.kind != OBSERVATION:
        return None
    if len(a.children) != len(b.children) or len(a.children) < 2:
        return None
    # Each side must be internally recurrent with one opaque operator symbol;
    # the two symbols are allowed to differ so the discovered pattern can be
    # tested on a fresh operator.
    af,_=_flatten_recurrent_args(a)
    bf,_=_flatten_recurrent_args(b)
    if len(af) != len(bf) or not af:
        return None
    if len(af) != len(bf) or not all(_kernel_values_equal(x, y) for x, y in zip(af, bf)):
        return None
    src=_shape_template(a)
    dst=_shape_template(b)
    # The top-level outputs are required to coincide in discovery; the actual
    # output value is copied through when applying the discovered structure.
    if not _kernel_values_equal(a.children[-1], b.children[-1]):
        return None
    distinct_af, _ = _flatten_recurrent_args_distinct(a)
    return src,dst,len(distinct_af)


def _apply_shape_term(term: ShapeTerm, values, operator):
    if term.kind == "VAR":
        return operator if term.value == 0 else values[term.value - 1]
    if term.kind == "APPLY":
        op_term=term.value
        op_value=_apply_shape_term(op_term, values, operator)
        return Node(
            node_id="shape-child",
            kind=OBSERVATION,
            children=(op_value,)+tuple(_apply_shape_term(x, values, operator) for x in term.children)+("_intermediate",),
        )
    raise ValueError(f"unknown shape term: {term.kind!r}")


def compare_tree_shapes(a: Node, b: Node) -> Optional[Node]:
    """Generic extension of Compare for same-symbol recurrent tree shapes."""
    sig=_same_shape_signature(a,b)
    if sig is None:
        return None
    src,dst,arity=sig
    if src == dst:
        # No-op guard (fixed 2026-09-17): two observations whose recurrent
        # shape rewrite is the identity carry no information -- there is
        # nothing to reify, matching compare()'s "identical: nothing to
        # discover" contract for the flat case.
        return None
    return Node(
        node_id=f"shape_pattern::{a.node_id}::{b.node_id}",
        kind=SHAPE_PATTERN,
        children=(ShapeRewrite(src,dst,arity),),
        provenance=(a.node_id,b.node_id),
    )


def apply_tree_shape(pattern: Node, observation: Node) -> Optional[Node]:
    if pattern.kind != SHAPE_PATTERN or observation.kind != OBSERVATION:
        return None
    if len(pattern.children)!=1 or not isinstance(pattern.children[0], ShapeRewrite):
        return None
    rw=pattern.children[0]
    values,_=_flatten_recurrent_args_distinct(observation)
    if len(values)!=rw.arity:
        return None
    target=_apply_shape_term(rw.target, values, observation.children[0])
    if not isinstance(target, Node):
        return None
    # Preserve the observed top-level output and create a fresh immutable node.
    target_children=list(target.children[:-1])+[observation.children[-1]]
    return Node(
        node_id=f"predicted::{pattern.node_id}::{observation.node_id}",
        kind=OBSERVATION,
        children=tuple(target_children),
        provenance=(pattern.node_id,observation.node_id),
    )


def shape_pattern_is_applicable(pattern: Node, observation: Node) -> bool:
    """Applicability check for SHAPE_PATTERN, symmetric to
    pattern_is_applicable() for PATTERN.

    FIX (2026-09-16, closes the gap found during E20/E21 verification --
    see probe7_applicable_gap.py): apply() unified Apply across both pattern
    kinds, but nothing symmetric existed for Applicable, so a caller using
    the "check applicability, then apply" idiom that works for a PATTERN got
    an unhandled ValueError for a SHAPE_PATTERN. Confirmed by execution that
    apply_tree_shape() itself already fails safe (returns None, never a
    wrong result) on every shape mismatch tested -- this function exposes
    that same precondition (arity match on the flattened, same-operator-
    recurrent argument count) so a caller can ask ahead of time instead of
    only finding out via a None result afterwards. Does not change
    apply_tree_shape() in any way; it remains directly callable."""
    if pattern.kind != SHAPE_PATTERN or observation.kind != OBSERVATION:
        return False
    if len(pattern.children) != 1 or not isinstance(pattern.children[0], ShapeRewrite):
        return False
    rw = pattern.children[0]
    values, _ = _flatten_recurrent_args(observation)
    return len(values) == rw.arity


def compare(a: Node, b: Node) -> Optional[Node]:
    """The single recursive Compare entry point.

    Called on two OBSERVATION nodes, it looks for a position permutation that
    reconciles their differences and reifies it as a local PATTERN node.
    Called on two PATTERN nodes (i.e. on its own prior output), it looks for
    a shared underlying permutation across both — the abstraction step,
    exactly `P = Compare(D1, D2)` from the source discussion (E13-A.1).

    Returns None when the two nodes are structurally incomparable (different
    shape), identical, or when no permutation reconciles them (no forced
    fit) -- AND ALSO when more than one permutation reconciles them equally
    well. compare() never guesses among competing candidates: when the
    varying positions contain repeated values, several distinct permutations
    can be equally valid, and picking one silently would make the discovered
    pattern depend on enumeration order rather than on the data (see
    research/k3_spike_e13a2/README.md, "Sonde adversariale ajoutée le
    2026-09-16" — this fail-closed behavior is the fix for that finding).
    Callers that want every viable candidate instead of only the unambiguous
    case should call compare_candidates().
    """
    a = resolve_structure(a)
    b = resolve_structure(b)
    if not isinstance(a, Node) or not isinstance(b, Node):
        raise ValueError("compare() requires Node or RefObject(Node) inputs")
    if a.kind != b.kind:
        raise ValueError(f"compare() requires two nodes of the same kind, got {a.kind!r} and {b.kind!r}")
    if len(a.children) != len(b.children):
        return None
    # Identical structures carry no transformation. In particular, do not
    # fall through to shape comparison and manufacture an identity
    # SHAPE_PATTERN: Compare is about differences, not self-equivalence.
    if structural_equal(a, b):
        return None
    if a.kind == OBSERVATION:
        direct = _compare_observations(a, b)
        if direct is not None:
            return direct
        return compare_tree_shapes(a, b)
    if a.kind == PATTERN:
        return _compare_patterns(a, b)
    raise ValueError(f"unknown node kind: {a.kind!r}")


def compare_candidates(a: Node, b: Node) -> Tuple[Node, ...]:
    """Like compare(), but never fails closed on ambiguity: returns every
    PATTERN node consistent with the evidence -- zero (incomparable or
    identical), one (the same result compare() would return), or more than
    one when several permutations reconcile a and b equally well.

    Intended for callers that want to carry multiple competing local-pattern
    hypotheses forward rather than have one picked arbitrarily -- consistent
    with the project's existing "never silently discard a viable alternative"
    stance (see Hypothesis / the E4 contradiction-handling precedent: a
    contradicted pattern keeps its prior support on record instead of being
    erased). Disambiguation is then a matter of gathering more evidence (a
    third observation, or a second independent family) that only some of the
    candidates survive -- not a matter of Compare guessing up front.
    """
    a = resolve_structure(a)
    b = resolve_structure(b)
    if not isinstance(a, Node) or not isinstance(b, Node):
        raise ValueError("compare_candidates() requires Node or RefObject(Node) inputs")
    if a.kind != b.kind:
        raise ValueError(f"compare_candidates() requires two nodes of the same kind, got {a.kind!r} and {b.kind!r}")
    if len(a.children) != len(b.children):
        return ()
    if a.kind == OBSERVATION:
        n = len(a.children)
        varying = [p for p in range(n) if not _kernel_values_equal(a.children[p], b.children[p])]
        if not varying:
            return ()
        nested_resolved, remaining = _resolve_nested_positions(a, b, varying)
        sigmas = _all_reconciling_permutations(a.children, b.children, remaining)
        if not sigmas:
            # Parity with compare(): when the direct positional search finds
            # no reconciling permutation, fall back to the same recurrent
            # tree-shape discovery compare() itself falls back to, instead of
            # silently reporting "no candidates" for a case compare() can in
            # fact resolve (fixed 2026-09-17, caught by
            # test_active_refusal_compare_and_compare_candidates_are_always_consistent).
            shape = compare_tree_shapes(a, b)
            return (shape,) if shape is not None else ()
        ambiguous = len(sigmas) > 1
        return tuple(
            _reify_observation_pattern(a, b, remaining, sigma, nested_resolved, suffix=f"#{i}" if ambiguous else "")
            for i, sigma in enumerate(sigmas)
        )
    if a.kind == PATTERN:
        merged = _compare_patterns(a, b)
        return (merged,) if merged is not None else ()
    raise ValueError(f"unknown node kind: {a.kind!r}")


def _resolve_nested_positions(a: Node, b: Node, varying):
    """E15 (nested structures): among the varying positions, recursively
    resolve any whose values on both sides are themselves OBSERVATION nodes
    with a discoverable Compare result -- `compare()` applied to its own
    composite children, exactly the "recursive Compare" principle already
    used for abstraction (Compare on PATTERN nodes), now applied one level
    deeper into the data itself. Terminates structurally: each recursive
    call operates on a strictly smaller child Node, never the node itself
    (an immutable Node cannot contain itself at construction time).

    E17: the two nested values may be OBSERVATION nodes (E15's original
    case: data containing data) OR PATTERN nodes (a discovered regularity
    embedded as an operand inside a further composition -- an operator
    entering composition without ever being specially declared as such,
    per the source discussion's E12/E17). Either way the SAME compare()
    entry point is reused; only the "both sides must agree on which kind
    of Node this position holds" requirement is kind-agnostic now.

    Returns (nested_resolved: dict[position, Node], remaining: list[position])
    -- `remaining` is what's left for the flat top-level permutation search.
    """
    nested_resolved = {}
    remaining = []
    for p in varying:
        av, bv = a.children[p], b.children[p]
        if isinstance(av, Node) and isinstance(bv, Node) and av.kind == bv.kind:
            inner = compare(av, bv)
            if inner is not None:
                nested_resolved[p] = inner
                continue
        remaining.append(p)
    return nested_resolved, remaining


def _all_reconciling_permutations(a_children, b_children, positions):
    """Every bijection sigma over `positions` with a[p] == b[sigma[p]] for
    every p in positions -- not just the first one found. Positions are, by
    construction, exactly those where a and b differ, so the unchanged
    positional mapping can never satisfy this check and needs no special-casing.
    An empty `positions` list yields exactly one (empty) mapping -- the
    unambiguous case where every varying position was resolved by nesting.
    Small position counts only (a spike, not a scalability claim)."""
    results = []
    for perm in permutations(positions):
        sigma = dict(zip(positions, perm))
        if all(_kernel_values_equal(a_children[p], b_children[sigma[p]]) for p in positions):
            results.append(sigma)
    return results


def _reify_observation_pattern(a: Node, b: Node, remaining, sigma, nested_resolved=None, suffix: str = "") -> Node:
    nested_resolved = nested_resolved or {}
    n = len(a.children)
    slots = []
    for p in range(n):
        if p in nested_resolved:
            slots.append(PatternSlot(source_position=p, literal_constraint=None, nested_pattern=nested_resolved[p]))
        elif p in remaining:
            slots.append(PatternSlot(source_position=sigma[p], literal_constraint=None))
        else:
            slots.append(PatternSlot(source_position=p, literal_constraint=a.children[p]))
    return Node(
        node_id=f"pattern::{a.node_id}::{b.node_id}{suffix}",
        kind=PATTERN,
        children=tuple(slots),
        provenance=(a.node_id, b.node_id),
    )


def _compare_observations(a: Node, b: Node) -> Optional[Node]:
    n = len(a.children)
    # R-V-1: internal difference detection must use the kernel-aware
    # comparator, never Python's raw `!=` on potentially reference-bearing
    # structures.
    varying = [p for p in range(n) if not _kernel_values_equal(a.children[p], b.children[p])]
    if not varying:
        return None  # identical observations: nothing to reify

    nested_resolved, remaining = _resolve_nested_positions(a, b, varying)
    sigmas = _all_reconciling_permutations(a.children, b.children, remaining)
    if len(sigmas) != 1:
        return None  # zero (no permutation reconciles them) or ambiguous (>1): compare() never guesses

    return _reify_observation_pattern(a, b, remaining, sigmas[0], nested_resolved)


def _compare_patterns(a: Node, b: Node) -> Optional[Node]:
    """Only a mismatched source_position signals two genuinely different
    transformations (incompatible). A slot that is a literal constraint in
    one instance and free (or a different literal) in the other is not a
    conflict — it means the wider evidence no longer supports treating that
    slot as fixed, so it generalizes to free. Generalization is monotonic:
    once free, always free.

    E15: a slot explained by a nested_pattern in both instances is merged by
    recursing Compare into the nested patterns themselves -- abstraction goes
    exactly as deep as discovery did. A slot nested in only one instance is
    incompatible (the two instances disagree about whether this position is a
    composite sub-structure at all)."""
    slots = []
    for sa, sb in zip(a.children, b.children):
        if sa.source_position != sb.source_position:
            return None  # different underlying transformation: not the same pattern family

        if sa.nested_pattern is not None and sb.nested_pattern is not None:
            merged_nested = compare(sa.nested_pattern, sb.nested_pattern)
            if merged_nested is None:
                return None  # not the same underlying nested regularity
            slots.append(PatternSlot(source_position=sa.source_position, literal_constraint=None, nested_pattern=merged_nested))
        elif sa.nested_pattern is not None or sb.nested_pattern is not None:
            return None  # one instance explains this slot recursively, the other doesn't: incompatible
        elif (
            sa.literal_constraint is not None
            and sb.literal_constraint is not None
            and _kernel_values_equal(sa.literal_constraint, sb.literal_constraint)
        ):
            slots.append(sa)  # both instances agree on this literal: keep the constraint
        else:
            slots.append(PatternSlot(source_position=sa.source_position, literal_constraint=None))  # generalize

    return Node(
        node_id=f"pattern::{a.node_id}::{b.node_id}",
        kind=PATTERN,
        children=tuple(slots),
        provenance=(a.node_id, b.node_id),
    )


def pattern_is_applicable(pattern: Node, observation: Node) -> bool:
    """Applicability check, deliberately kept separate from Apply (source
    discussion, section 12: "Exploration != application automatique", the
    mechanism must separate Applicable from Apply). True iff every literal-
    constrained slot of `pattern` matches the value already present in
    `observation` at that position -- checked recursively (E15) for any slot
    explained by a nested_pattern.

    E17: `observation` may itself be a PATTERN node -- applying a discovered
    regularity to another discovered regularity (an operator acting as the
    operand of a further composition), not only to raw data.

    NOTE (2026-09-16, Apply unification): this applicability check is
    PATTERN-specific and is not extended here to SHAPE_PATTERN. See apply()'s
    docstring -- unifying applicability checking across both kinds is left
    open deliberately, not folded silently into this function.

    FIX (2026-09-16, confirmed silent-misapplication gap, E19 verification --
    see probe6_e19_aggregate.py): also False if a `requires_source_equal`
    slot's own value does not actually equal the value at its
    source_position in THIS observation -- i.e. a discovered column
    dependency (aggregate_observations()) is now genuinely checked, not
    silently assumed to hold just because no literal_constraint was set."""
    pattern = resolve_structure(pattern)
    if not isinstance(pattern, Node) or observation.kind not in (OBSERVATION, PATTERN):
        raise ValueError("pattern_is_applicable() requires a PATTERN and an OBSERVATION-or-PATTERN node")
    if len(pattern.children) != len(observation.children):
        return False
    for slot, value in zip(pattern.children, observation.children):
        if slot.nested_pattern is not None:
            if not isinstance(value, Node) or value.kind not in (OBSERVATION, PATTERN):
                return False
            if not pattern_is_applicable(slot.nested_pattern, value):
                return False
        elif slot.literal_constraint is not None and not _kernel_values_equal(slot.literal_constraint, value):
            return False
        elif slot.requires_source_equal and not _kernel_values_equal(observation.children[slot.source_position], value):
            return False
    return True


def apply_pattern(pattern: Node, observation: Node) -> Optional[Node]:
    """Apply (K3's Apply) a PATTERN to an OBSERVATION-or-PATTERN node,
    producing a predicted node of that same kind. Always computes a result
    when the shapes match, regardless of whether the pattern's literal
    constraints are met — that is deliberate: computing "what would this
    pattern predict" is exactly how a contradiction is detected (compare the
    prediction to what was actually observed), so apply_pattern must not
    itself refuse to run. Callers that need to know whether applying is
    *meaningful* first should call pattern_is_applicable().

    E15: a slot with a nested_pattern recurses Apply into the corresponding
    composite child instead of copying it through unchanged -- the prediction
    goes exactly as deep as discovery did.

    E17: `observation` (and any nested child reached along the way) may
    itself be a PATTERN node -- a previously-discovered regularity playing
    the role of operand in a further composition, never specially declared
    as "an operator" anywhere in this module. The predicted node's kind
    matches whatever kind was fed in, so applying to a PATTERN yields a
    PATTERN (a predicted variant of that operator), exactly as applying to
    an OBSERVATION yields an OBSERVATION.

    When `observation` is itself a PATTERN, its children are PatternSlot
    objects whose OWN source_position is meaningful only relative to their
    position within `observation` -- relocating such a slot without
    rewriting that internal reference would silently produce a different,
    wrong transformation (verified empirically while building E17: it
    degenerated a swap into an unchanged mapping). Relocated PatternSlots are
    therefore rebased through the same permutation Apply is itself
    performing, a generic operation (composing two permutations), not a
    domain-specific fix."""
    pattern = resolve_structure(pattern)
    if not isinstance(pattern, Node) or pattern.kind != PATTERN:
        raise ValueError("apply_pattern() requires a PATTERN node or RefObject(PATTERN)")
    if observation.kind not in (OBSERVATION, PATTERN):
        raise ValueError("apply_pattern() requires an OBSERVATION-or-PATTERN node to apply to")
    if len(pattern.children) != len(observation.children):
        return None

    old_to_new = None
    if observation.kind == PATTERN:
        old_to_new = {slot.source_position: new for new, slot in enumerate(pattern.children)}

    predicted = []
    for slot in pattern.children:
        value = observation.children[slot.source_position]
        if slot.nested_pattern is not None:
            if not isinstance(value, Node) or value.kind not in (OBSERVATION, PATTERN):
                return None
            nested_predicted = apply_pattern(slot.nested_pattern, value)
            if nested_predicted is None:
                return None
            predicted.append(nested_predicted)
        elif old_to_new is not None:
            predicted.append(PatternSlot(
                source_position=old_to_new.get(value.source_position, value.source_position),
                literal_constraint=value.literal_constraint,
                nested_pattern=value.nested_pattern,
            ))
        else:
            predicted.append(value)

    return Node(
        node_id=f"predicted::{pattern.node_id}::{observation.node_id}",
        kind=observation.kind,
        children=tuple(predicted),
        provenance=(pattern.node_id, observation.node_id),
    )


def _operator_reference(operator: object) -> NodeRef:
    """Extract an operator identity without inspecting its external value.

    Operators are not a rigid kernel type. In the open structural algebra an
    operator is simply a reference-bearing object used in the first position
    of an application. A RefObject contributes its own reference identity; a
    NodeRef is already an opaque operator identity; a raw string remains a
    backwards-compatible opaque token.
    """
    if isinstance(operator, RefObject):
        return operator.ref
    if isinstance(operator, NodeRef):
        return operator
    if isinstance(operator, str):
        return NodeRef(operator)
    raise ValueError(
        "operator application requires a NodeRef, RefObject, or opaque string operator"
    )


def apply_operator(
    operator: object,
    *operands: object,
    node_id: Optional[str] = None,
    provenance: Tuple[str, ...] = (),
) -> Node:
    """Construct an application structure from an operator reference.

    This is the constructor form of K3's Apply: it does not evaluate the
    operator, inspect its meaning, or introduce a new semantic primitive. It
    creates the ordinary recursive application structure:

        *P = f(*A, *B, ...)

    Operator identity is reference-based. Operands may themselves be NodeRef,
    RefObject, PatternRef, Node, or other kernel structural objects. The
    resulting Node is therefore immediately eligible to participate in Compare
    and further Apply operations.
    """
    op_ref = _operator_reference(operator)
    return Node(
        node_id=node_id or "apply::" + op_ref.ref_id,
        kind=OBSERVATION,
        children=(op_ref,) + tuple(operands),
        provenance=tuple(provenance),
    )


def apply(
    pattern_or_operator: object,
    observation_or_operand: object,
    *operands: object,
    node_id: Optional[str] = None,
    provenance: Tuple[str, ...] = (),
) -> Optional[Node]:
    """The single public Apply entry point, with structural constructor overload.

    Existing behavior is preserved for PATTERN/SHAPE_PATTERN: the second
    argument is the observation/subject to transform and optional extra
    operands are rejected. In the constructor form, a NodeRef, RefObject that
    is not a pattern, or opaque string is treated as the operator identity and
    all following arguments are operands, yielding an OBSERVATION structure.

    The overload is intentionally structural, analogous to extending a POO
    constructor: it adds no fixed ``Operator`` class to the ontology. A
    property, relation, transformation, or meta-structure can therefore be
    represented simply by a reference-bearing structural object and reused as
    an operand at a higher level.
    """
    resolved = resolve_structure(pattern_or_operator)
    if isinstance(resolved, Node) and resolved.kind in (PATTERN, SHAPE_PATTERN):
        if operands or node_id is not None or provenance:
            raise ValueError(
                "pattern Apply does not accept constructor-only operands/node_id/provenance"
            )
        if resolved.kind == PATTERN:
            return apply_pattern(resolved, observation_or_operand)
        return apply_tree_shape(resolved, observation_or_operand)

    # Generic constructor form: operator identity is not dereferenced.
    return apply_operator(
        pattern_or_operator,
        observation_or_operand,
        *operands,
        node_id=node_id,
        provenance=provenance,
    )


def is_applicable(pattern: Node, observation: Node) -> bool:
    """The single public Applicable entry point, symmetric to apply().

    Added 2026-09-16 to close the gap apply() itself flagged but did not
    fix: Apply was unified across PATTERN and SHAPE_PATTERN, but Applicable
    stayed PATTERN-only, so a caller relying on the "check applicability,
    then apply" idiom that works for a PATTERN got an unhandled ValueError
    for a SHAPE_PATTERN (confirmed by execution, not merely suspected --
    see probe7_applicable_gap.py). Dispatches on pattern.kind alone, exactly
    like apply() and compare(): PATTERN -> pattern_is_applicable(),
    SHAPE_PATTERN -> shape_pattern_is_applicable(). Raises ValueError for
    any other pattern.kind, on the same fail-loud precedent.

    Neither pattern_is_applicable() nor shape_pattern_is_applicable() is
    changed by this function's existence; both remain directly callable."""
    pattern = resolve_structure(pattern)
    if not isinstance(pattern, Node):
        raise ValueError("is_applicable() requires a PATTERN/SHAPE_PATTERN node or RefObject containing one")
    if pattern.kind == PATTERN:
        return pattern_is_applicable(pattern, observation)
    if pattern.kind == SHAPE_PATTERN:
        return shape_pattern_is_applicable(pattern, observation)
    raise ValueError(f"is_applicable() requires a PATTERN or SHAPE_PATTERN node as `pattern`, got {pattern.kind!r}")


@dataclass(frozen=True)
class Hypothesis:
    """Epistemic wrapper around a discovered PATTERN. Vocabulary matches the
    project's existing three-state contract (Supported/Unknown/Contradicted —
    see structural/epistemic.py and metahia_m2) as plain, LOCAL strings: this
    spike defines its own copy rather than importing the production one, to
    keep zero coupling with production code."""
    hypothesis_id: str
    pattern: Node
    supporting_ids: Tuple[str, ...] = ()
    contradicting_ids: Tuple[str, ...] = ()

    @property
    def status(self) -> str:
        if self.contradicting_ids:
            return "CONTRADICTED"
        if self.supporting_ids:
            return "SUPPORTED"
        return "UNKNOWN"

    def with_support(self, observation_id: str) -> "Hypothesis":
        return Hypothesis(self.hypothesis_id, self.pattern, self.supporting_ids + (observation_id,), self.contradicting_ids)

    def with_contradiction(self, observation_id: str) -> "Hypothesis":
        return Hypothesis(self.hypothesis_id, self.pattern, self.supporting_ids, self.contradicting_ids + (observation_id,))


def group_into_hypotheses(pairs) -> Tuple[Hypothesis, ...]:
    """E16: given several (a, b) OBSERVATION pairs -- possibly all nominally
    "the same family" -- discover a local pattern per pair and group them
    into competing Hypothesis objects by structural compatibility, using
    compare() itself as the compatibility test: two patterns are "the same
    regularity" exactly when compare() can merge them (the same abstraction
    mechanism already used across independent operator families in E13-A.2),
    and genuinely incompatible when it cannot (returns None) -- reusing the
    existing PATTERN-vs-PATTERN comparison rather than inventing a second,
    bespoke notion of "same pattern".

    A pair whose pattern merges into an existing hypothesis adds support to
    it (generalizing it in the process, exactly like cross-family
    abstraction). A pair whose pattern does not merge into ANY existing
    hypothesis becomes a new, independent one. No hypothesis is ever dropped
    or silently overwritten by another -- the same "never erase a viable
    alternative" stance already used for contradiction (with_contradiction).
    A pair yielding no local pattern at all (compare() returns None on the
    raw observations) contributes nothing and is skipped.
    """
    hypotheses: List[Hypothesis] = []
    for a, b in pairs:
        pattern = compare(a, b)
        if pattern is None:
            continue
        for i, h in enumerate(hypotheses):
            merged = compare(h.pattern, pattern)
            if merged is not None:
                hypotheses[i] = Hypothesis(
                    h.hypothesis_id,
                    merged,
                    h.supporting_ids + (a.node_id, b.node_id),
                    h.contradicting_ids,
                )
                break
        else:
            hypotheses.append(Hypothesis(
                hypothesis_id=f"H{len(hypotheses)}",
                pattern=pattern,
                supporting_ids=(a.node_id, b.node_id),
            ))
    return tuple(hypotheses)


def aggregate_observations(observations):
    """Generic multi-observation regularity discovery.

    For each position, infer either a constant value or a unique positional
    dependency that holds across every supplied observation. Ambiguous or
    unsupported dependencies return None. No domain meaning is inspected.
    """
    if len(observations) < 3:
        return None
    if any(n.kind != OBSERVATION for n in observations):
        return None
    width=len(observations[0].children)
    if any(len(n.children) != width for n in observations):
        return None
    slots=[]
    for target in range(width):
        col=[n.children[target] for n in observations]
        # Constant column: retain the observed literal structurally.
        if all(_kernel_values_equal(v, col[0]) for v in col[1:]):
            slots.append(PatternSlot(source_position=target, literal_constraint=col[0]))
            continue
        candidates=[]
        for source in range(width):
            if source == target:
                continue
            if all(_kernel_values_equal(n.children[target], n.children[source]) for n in observations):
                candidates.append(source)
        if len(candidates) != 1:
            return None
        # requires_source_equal=True (2026-09-16 fix): this slot encodes a
        # genuine invariant ("this position must equal that one"), not a
        # free relabeling -- pattern_is_applicable() must actually check it.
        slots.append(PatternSlot(source_position=candidates[0], literal_constraint=None, requires_source_equal=True))
    return Node(
        node_id="aggregate_pattern::" + "::".join(n.node_id for n in observations),
        kind=PATTERN,
        children=tuple(slots),
        provenance=tuple(n.node_id for n in observations),
    )


def discover_hypothesis(observations):
    """Wrap a multi-observation structural pattern with its evidence lineage."""
    pattern=aggregate_observations(observations)
    if pattern is None:
        return None
    return Hypothesis(
        hypothesis_id=f"H::{observations[0].node_id}",
        pattern=pattern,
        supporting_ids=tuple(n.node_id for n in observations),
    )


# ---------------------------------------------------------------------------
# Generic Graph / Path discovery layer (E20-D.10 / E20-D.11)
# ---------------------------------------------------------------------------
# These dataclasses are execution records/views over K3 structures, not new
# ontological primitives. The K3 core remains Node / Apply / Compare. They make
# explicit a structural graph induced by observed binary applications and the
# anonymous paths found by traversing that graph.

PATH_FORWARD = "FORWARD"
PATH_REVERSE = "REVERSE"
PATH_MARKER = "PATH"
LINK_MARKER = "LINK"


@dataclass(frozen=True)
class GraphEdge:
    """One observed binary relation edge.

    The operator is kept opaque. Direction is a traversal property, not an
    invented inverse operator. `observation_id` is provenance back to the
    source structure.
    """
    edge_id: str
    source: NodeRef
    operator: object
    target: NodeRef
    observation_id: str
    source_position: int = 1
    target_position: int = 2


@dataclass(frozen=True)
class StructuralGraph:
    """Immutable graph view induced from observed binary structures."""
    nodes: Tuple[NodeRef, ...]
    edges: Tuple[GraphEdge, ...]

    def outgoing(self, node: NodeRef, allow_reverse: bool = True) -> Tuple[Tuple[GraphEdge, str, NodeRef], ...]:
        """Return traversable edge steps from `node`.

        For a reversed traversal the original operator is retained and the
        step direction records the traversal orientation. No inverse operator
        is fabricated here.
        """
        result = []
        for edge in self.edges:
            if reference_equal(edge.source, node):
                result.append((edge, PATH_FORWARD, edge.target))
            if allow_reverse and reference_equal(edge.target, node):
                result.append((edge, PATH_REVERSE, edge.source))
        return tuple(result)


@dataclass(frozen=True)
class PathStep:
    """One traversal step inside an anonymous structural path."""
    edge_id: str
    observation_id: str
    operator: object
    direction: str
    source: NodeRef
    target: NodeRef


@dataclass(frozen=True)
class PathRecord:
    """A discovered path with explicit endpoint and provenance information."""
    path_id: str
    start: NodeRef
    end: NodeRef
    steps: Tuple[PathStep, ...]
    provenance: Tuple[str, ...]

    @property
    def length(self) -> int:
        return len(self.steps)

    @property
    def operator_sequence(self) -> Tuple[object, ...]:
        return tuple(step.operator for step in self.steps)

    @property
    def direction_sequence(self) -> Tuple[str, ...]:
        return tuple(step.direction for step in self.steps)

    @property
    def node_sequence(self) -> Tuple[NodeRef, ...]:
        if not self.steps:
            return (self.start,)
        return (self.start,) + tuple(step.target for step in self.steps)


@dataclass(frozen=True)
class PathPropertyObject:
    """One structural property extracted from a PathRecord.

    This is an execution-level object, not a new K3 primitive.  The property
    has a structural key and a structural value, plus provenance back to the
    path that produced it.  No semantic interpretation is attached.
    """
    property_id: str
    key: object
    value: object
    path_id: str
    provenance: Tuple[str, ...]

    def structural_form(self) -> Tuple[object, ...]:
        return ("PATH_PROPERTY", self.key, self.value)


@dataclass(frozen=True)
class PathProperties:
    """Structural feature bundle of a discovered path.

    The scalar/object values are kept as execution data while each property
    can also be projected to a standalone PathPropertyObject and reified as a
    RefObject.  The bundle itself remains descriptive, never semantic.
    """
    length: int
    operator_sequence: Tuple[object, ...]
    direction_sequence: Tuple[str, ...]
    node_sequence: Tuple[NodeRef, ...]
    distinct_node_count: int
    distinct_operator_count: int
    repeated_operator: bool
    reversed_traversal: bool
    branching_at_start: int
    branching_at_end: int
    path_id: str = ""
    provenance: Tuple[str, ...] = ()

    def as_objects(self) -> Tuple[PathPropertyObject, ...]:
        values = (
            ("length", self.length),
            ("operator_sequence", self.operator_sequence),
            ("direction_sequence", self.direction_sequence),
            ("node_sequence", self.node_sequence),
            ("distinct_node_count", self.distinct_node_count),
            ("distinct_operator_count", self.distinct_operator_count),
            ("repeated_operator", self.repeated_operator),
            ("reversed_traversal", self.reversed_traversal),
            ("branching_at_start", self.branching_at_start),
            ("branching_at_end", self.branching_at_end),
        )
        return tuple(
            PathPropertyObject(
                property_id=f"{self.path_id}::prop::{index}",
                key=key,
                value=value,
                path_id=self.path_id,
                provenance=self.provenance,
            )
            for index, (key, value) in enumerate(values)
        )


def _binary_relation_edge(observation: Node, edge_index: int) -> GraphEdge:
    """Convert one OBSERVATION with exactly two operands to an edge."""
    if not isinstance(observation, Node) or observation.kind != OBSERVATION:
        raise ValueError("graph construction requires OBSERVATION nodes")
    if len(observation.children) != 3:
        raise ValueError(
            "graph construction requires binary OBSERVATION form "
            "(operator, source, target)"
        )
    operator, source, target = observation.children
    if not isinstance(source, NodeRef) or not isinstance(target, NodeRef):
        raise ValueError(
            "graph endpoints must be NodeRef objects; external payload values "
            "must not be used as graph identity"
        )
    return GraphEdge(
        edge_id=f"edge::{edge_index}::{observation.node_id}",
        source=source,
        operator=operator,
        target=target,
        observation_id=observation.node_id,
    )


def build_structural_graph(observations: Iterable[Node]) -> StructuralGraph:
    """Build an immutable graph from observed binary K3 structures.

    Input is only the already represented structure. No relation name is
    interpreted. Each OBSERVATION must have the form

        (operator, source_ref, target_ref)

    The function deliberately fails closed on non-binary or payload-based
    inputs rather than manufacturing graph identities.
    """
    nodes: List[NodeRef] = []
    edges: List[GraphEdge] = []
    for index, observation in enumerate(observations):
        edge = _binary_relation_edge(observation, index)
        edges.append(edge)
        if not any(reference_equal(edge.source, n) for n in nodes):
            nodes.append(edge.source)
        if not any(reference_equal(edge.target, n) for n in nodes):
            nodes.append(edge.target)
    return StructuralGraph(nodes=tuple(nodes), edges=tuple(edges))


def materialize_reified_link(
    link: RefObject,
    *,
    node_id: Optional[str] = None,
    provenance: Tuple[str, ...] = (),
) -> Node:
    """Materialize a reified LINK object as an ordinary binary observation.

    The link object remains the opaque operator identity of the new edge.
    No semantic name is inferred. This is the minimal bridge required for
    recursive structural closure: a generated link becomes an ordinary K3
    application and can therefore re-enter graph/path exploration.

    Expected link structure is produced by :func:`reify_path_link`:

        (LINK_MARKER, start_ref, end_ref, path_operator_direction)

    The fourth component is retained inside the reified link object but is
    not interpreted here. The materialized observation has the generic form

        link_ref(start_ref, end_ref)

    where ``link_ref`` is the generated object's own reference identity.
    """
    if not isinstance(link, RefObject):
        raise TypeError("materialize_reified_link requires a RefObject")
    structure = link.structure
    if (
        not isinstance(structure, tuple)
        or len(structure) != 4
        or structure[0] != LINK_MARKER
        or not isinstance(structure[1], NodeRef)
        or not isinstance(structure[2], NodeRef)
    ):
        raise ValueError("link does not carry a valid reified LINK structure")

    start_ref = structure[1]
    end_ref = structure[2]
    derived_provenance = tuple(provenance) or (link.ref.ref_id,)
    return Node(
        node_id=node_id or f"materialized::{link.ref.ref_id}",
        kind=OBSERVATION,
        children=(link, start_ref, end_ref),
        provenance=derived_provenance,
    )


def reinject_reified_links(
    graph: StructuralGraph,
    links: Iterable[RefObject],
    *,
    observation_prefix: str = "reinject",
) -> StructuralGraph:
    """Return a new graph containing reified links as additional edges.

    Existing graph nodes/edges are preserved. Each generated LINK becomes an
    ordinary K3 binary observation whose operator is the link's own
    reference-bearing object. Consequently, a generated link can participate
    in subsequent path discovery without any semantic interpretation.

    The operation is additive and one-step: recursive exploration is obtained
    by calling it again after generating another batch of links. This keeps
    structural closure explicit and compatible with cognitive/ROI control.
    """
    new_edges = list(graph.edges)
    nodes = list(graph.nodes)
    existing_edge_ids = {edge.edge_id for edge in new_edges}

    for index, link in enumerate(tuple(links)):
        observation = materialize_reified_link(
            link,
            node_id=f"{observation_prefix}::{index}::{link.ref.ref_id}",
            provenance=(link.ref.ref_id,),
        )
        edge = _binary_relation_edge(observation, len(new_edges))
        if edge.edge_id in existing_edge_ids:
            continue
        existing_edge_ids.add(edge.edge_id)
        new_edges.append(edge)
        if not any(reference_equal(edge.source, n) for n in nodes):
            nodes.append(edge.source)
        if not any(reference_equal(edge.target, n) for n in nodes):
            nodes.append(edge.target)

    return StructuralGraph(nodes=tuple(nodes), edges=tuple(new_edges))


def discover_paths(
    graph: StructuralGraph,
    start: Optional[NodeRef] = None,
    end: Optional[NodeRef] = None,
    max_depth: int = 3,
    allow_reverse: bool = True,
    max_paths: int = 1000,
) -> Tuple[PathRecord, ...]:
    """Enumerate simple structural paths without semantic filtering.

    A traversal may follow an observed edge forward or reverse. Reverse is
    represented only by `PATH_REVERSE`; no inverse operator is invented.
    Node identity is reference-based. A node is not revisited within a path,
    which prevents trivial cycles while keeping arbitrary path shapes open.

    `max_depth` and `max_paths` are exploration controls, not semantic rules.
    """
    if max_depth < 1:
        return tuple()
    if max_paths < 1:
        return tuple()

    starts = (start,) if start is not None else graph.nodes
    results: List[PathRecord] = []

    def walk(current: NodeRef, origin: NodeRef, steps: List[PathStep], visited: Tuple[NodeRef, ...]):
        if len(results) >= max_paths:
            return
        if steps and (end is None or reference_equal(current, end)):
            path_id = "path::" + "::".join(step.edge_id + ":" + step.direction for step in steps)
            results.append(PathRecord(
                path_id=path_id,
                start=origin,
                end=current,
                steps=tuple(steps),
                provenance=tuple(step.observation_id for step in steps),
            ))
            if end is not None and reference_equal(current, end):
                return
        if len(steps) >= max_depth:
            return
        for edge, direction, nxt in graph.outgoing(current, allow_reverse=allow_reverse):
            if any(reference_equal(nxt, seen) for seen in visited):
                continue
            step = PathStep(
                edge_id=edge.edge_id,
                observation_id=edge.observation_id,
                operator=edge.operator,
                direction=direction,
                source=current,
                target=nxt,
            )
            walk(nxt, origin, steps + [step], visited + (nxt,))
            if len(results) >= max_paths:
                return

    for root in starts:
        walk(root, root, [], (root,))
        if len(results) >= max_paths:
            break
    return tuple(results)


def path_properties(path: PathRecord, graph: Optional[StructuralGraph] = None) -> PathProperties:
    """Extract structural features from a path without semantic interpretation."""
    operators = path.operator_sequence
    node_sequence = path.node_sequence
    distinct_nodes = []
    for node in node_sequence:
        if not any(reference_equal(node, seen) for seen in distinct_nodes):
            distinct_nodes.append(node)
    distinct_ops = []
    for op in operators:
        if not any(structural_equal(op, seen) for seen in distinct_ops):
            distinct_ops.append(op)

    branching_start = 0
    branching_end = 0
    if graph is not None:
        branching_start = len(graph.outgoing(path.start, allow_reverse=True))
        branching_end = len(graph.outgoing(path.end, allow_reverse=True))

    return PathProperties(
        length=path.length,
        operator_sequence=operators,
        direction_sequence=path.direction_sequence,
        node_sequence=node_sequence,
        distinct_node_count=len(distinct_nodes),
        distinct_operator_count=len(distinct_ops),
        repeated_operator=len(distinct_ops) < len(operators),
        reversed_traversal=PATH_REVERSE in path.direction_sequence,
        branching_at_start=branching_start,
        branching_at_end=branching_end,
        path_id=path.path_id,
        provenance=path.provenance,
    )


def path_property_objects(path: PathRecord, graph: Optional[StructuralGraph] = None) -> Tuple[PathPropertyObject, ...]:
    """Extract each path property as a standalone structural object.

    This is the E20-D.13 bridge from descriptive path features to objects that
    can themselves be compared, related, reified and later composed.
    """
    return path_properties(path, graph).as_objects()


def path_property_structural_form(prop: PathPropertyObject) -> Tuple[object, ...]:
    """Return the semantic-free structural form of one path property object."""
    return prop.structural_form()


def reify_path_property(prop: PathPropertyObject, ref_id: Optional[str] = None) -> RefObject:
    """Reify a path property while preserving identity/value separation."""
    ref = ref_id or prop.property_id
    return RefObject(NodeRef(ref), path_property_structural_form(prop))


def path_properties_structural_form(props: PathProperties) -> Tuple[object, ...]:
    """Return a structural bundle without path identity/provenance."""
    return (
        "PATH_PROPERTIES",
        tuple(path_property_structural_form(p) for p in props.as_objects()),
    )


def reify_path_properties(props: PathProperties, ref_id: Optional[str] = None) -> RefObject:
    """Reify the complete property bundle as one reference-bearing object."""
    ref = ref_id or f"props::{props.path_id}"
    return RefObject(NodeRef(ref), path_properties_structural_form(props))


def path_structural_form(path: PathRecord) -> Tuple[object, ...]:
    """Canonical anonymous representation of a path for later Compare/Apply.

    Endpoints and operator labels remain opaque references/structural tokens.
    The traversal direction is explicit. Path provenance is intentionally not
    included in the structural form so independently discovered equivalent
    paths can compare structurally while retaining provenance on PathRecord.
    """
    return (
        PATH_MARKER,
        path.start,
        path.end,
        tuple((step.operator, step.direction) for step in path.steps),
    )


def reify_path(path: PathRecord, ref_id: Optional[str] = None) -> RefObject:
    """Reify a discovered path as an ordinary reference-bearing object."""
    ref = ref_id or path.path_id
    return RefObject(NodeRef(ref), path_structural_form(path))




@dataclass(frozen=True)
class PathPattern:
    """Generic structural abstraction shared by compatible PathRecord objects.

    This is an execution-level structural object, not a new K3 primitive.
    A PathPattern contains only structural bindings:
      - `operator_sequence` and `direction_sequence` are preserved exactly;
      - `node_binding` maps each path node position to an anonymous variable;
      - `position_groups` records positions proven co-referent in *every* input
        path (intersection of observed reference-equality constraints);
      - `source_count` records how many concrete paths supported the abstraction.

    No payload value, semantic label, or domain rule is used.
    """
    pattern_id: str
    operator_sequence: Tuple[object, ...]
    direction_sequence: Tuple[str, ...]
    node_binding: Tuple[int, ...]
    position_groups: Tuple[Tuple[int, ...], ...]
    source_path_ids: Tuple[str, ...]
    provenance: Tuple[str, ...]

    @property
    def length(self) -> int:
        return len(self.operator_sequence)


def _path_operator_direction_signature(path: PathRecord) -> Tuple[Tuple[object, str], ...]:
    """Return the non-semantic operator/direction skeleton of a path."""
    return tuple(
        (step.operator, step.direction)
        for step in path.steps
    )


def _path_reference_equal(left: NodeRef, right: NodeRef) -> bool:
    """Local reference-only equality for path abstraction."""
    return reference_equal(left, right)


def _path_equality_pairs(path: PathRecord) -> set[Tuple[int, int]]:
    """Return co-reference pairs among node positions of one concrete path."""
    nodes = path.node_sequence
    return {
        (i, j)
        for i in range(len(nodes))
        for j in range(i + 1, len(nodes))
        if _path_reference_equal(nodes[i], nodes[j])
    }


def _canonical_position_partition(
    node_count: int,
    common_equal_pairs: set[Tuple[int, int]],
) -> Tuple[int, ...]:
    """Assign anonymous variables from the equality constraints shared by all paths."""
    parent = list(range(node_count))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in sorted(common_equal_pairs):
        union(a, b)

    root_to_var: Dict[int, int] = {}
    bindings: List[int] = []
    for pos in range(node_count):
        root = find(pos)
        if root not in root_to_var:
            root_to_var[root] = len(root_to_var)
        bindings.append(root_to_var[root])
    return tuple(bindings)


def generalize_path_pattern(paths: Iterable[PathRecord], pattern_id: Optional[str] = None) -> Optional[PathPattern]:
    """Generalize compatible paths into one anonymous structural pattern.

    Compatibility is deliberately strict:
      1. at least two paths are required;
      2. all paths have the same length;
      3. their operator/direction skeletons are structurally equal;
      4. reference-equality constraints are generalized only when they hold in
         every input path (intersection, never union).

    This means that repeated values/references in only a subset of examples do
    not create false co-reference. The result is a path schema, not a semantic
    relation name and not a truth claim.
    """
    items = tuple(paths)
    if len(items) < 2:
        return None
    length = items[0].length
    if any(path.length != length for path in items):
        return None

    skeleton = _path_operator_direction_signature(items[0])
    for path in items[1:]:
        if any(
            not structural_equal(op_a, op_b) or dir_a != dir_b
            for (op_a, dir_a), (op_b, dir_b)
            in zip(skeleton, _path_operator_direction_signature(path))
        ):
            return None

    node_count = length + 1
    common_pairs = _path_equality_pairs(items[0])
    for path in items[1:]:
        common_pairs.intersection_update(_path_equality_pairs(path))

    binding = _canonical_position_partition(node_count, common_pairs)
    groups_map: Dict[int, List[int]] = {}
    for pos, var_id in enumerate(binding):
        groups_map.setdefault(var_id, []).append(pos)
    groups = tuple(tuple(v) for _, v in sorted(groups_map.items()))

    prov: List[str] = []
    for path in items:
        for source in path.provenance:
            if source not in prov:
                prov.append(source)

    pid = pattern_id or "path_pattern::" + "::".join(path.path_id for path in items)
    return PathPattern(
        pattern_id=pid,
        operator_sequence=tuple(step.operator for step in items[0].steps),
        direction_sequence=items[0].direction_sequence,
        node_binding=binding,
        position_groups=groups,
        source_path_ids=tuple(path.path_id for path in items),
        provenance=tuple(prov),
    )


def path_pattern_structural_form(pattern: PathPattern) -> Tuple[object, ...]:
    """Return the anonymous structural form of a PathPattern."""
    return (
        PATH_MARKER,
        ("PATH_PATTERN",),
        tuple((op, direction) for op, direction in zip(pattern.operator_sequence, pattern.direction_sequence)),
        pattern.node_binding,
    )


def reify_path_pattern(pattern: PathPattern, ref_id: Optional[str] = None) -> RefObject:
    """Reify a generalized path pattern without assigning semantic meaning."""
    ref = ref_id or pattern.pattern_id
    return RefObject(NodeRef(ref), path_pattern_structural_form(pattern))


@dataclass(frozen=True)
class PathReplayResult:
    """Result of replaying a structural path pattern on a new graph.

    The result is a prediction only over the structural graph: no semantic
    interpretation of the operator sequence is attempted.  ``status`` is one
    of ``REPLAYED`` or ``AMBIGUOUS``/``NOT_FOUND`` and the predicted endpoint
    is retained only when exactly one structural continuation exists at every
    step.
    """
    status: str
    start: NodeRef
    predicted_end: Optional[NodeRef]
    path: Optional[PathRecord]
    provenance: Tuple[str, ...]


PATH_REPLAYED = "REPLAYED"
PATH_REPLAY_NOT_FOUND = "NOT_FOUND"
PATH_REPLAY_AMBIGUOUS = "AMBIGUOUS"


def replay_path_pattern(
    pattern: PathPattern,
    graph: StructuralGraph,
    start: NodeRef,
    *,
    max_candidates_per_step: int = 1,
) -> PathReplayResult:
    """Replay a generalized path pattern against a holdout graph.

    The operator/direction skeleton is treated as an executable structural
    operation. At each step the graph is queried for continuations matching
    the expected opaque operator and traversal direction. The replay succeeds
    only when exactly one continuation is available (or when the caller
    explicitly allows more than one by raising ``max_candidates_per_step``).

    No semantic inverse is fabricated: reverse traversal remains the explicit
    ``PATH_REVERSE`` direction. The produced PathRecord is fully provenance-
    linked to the holdout graph observations.
    """
    if not isinstance(pattern, PathPattern):
        raise TypeError("replay requires a PathPattern")
    if not isinstance(graph, StructuralGraph):
        raise TypeError("replay requires a StructuralGraph")
    if max_candidates_per_step < 1:
        raise ValueError("max_candidates_per_step must be >= 1")

    current = start
    steps: List[PathStep] = []
    visited: Tuple[NodeRef, ...] = (start,)

    for expected_operator, expected_direction in zip(
        pattern.operator_sequence, pattern.direction_sequence
    ):
        matches = []
        for edge, direction, nxt in graph.outgoing(current, allow_reverse=True):
            if direction != expected_direction:
                continue
            if not structural_equal(edge.operator, expected_operator):
                continue
            if any(reference_equal(nxt, seen) for seen in visited):
                continue
            matches.append((edge, direction, nxt))

        if not matches:
            return PathReplayResult(
                status=PATH_REPLAY_NOT_FOUND,
                start=start,
                predicted_end=None,
                path=None,
                provenance=tuple(step.observation_id for step in steps),
            )

        if len(matches) > max_candidates_per_step:
            return PathReplayResult(
                status=PATH_REPLAY_AMBIGUOUS,
                start=start,
                predicted_end=None,
                path=None,
                provenance=tuple(step.observation_id for step in steps),
            )

        edge, direction, nxt = matches[0]
        step = PathStep(
            edge_id=edge.edge_id,
            observation_id=edge.observation_id,
            operator=edge.operator,
            direction=direction,
            source=current,
            target=nxt,
        )
        steps.append(step)
        current = nxt
        visited = visited + (nxt,)

    path_id = "replay::" + pattern.pattern_id + "::" + start.ref_id
    path = PathRecord(
        path_id=path_id,
        start=start,
        end=current,
        steps=tuple(steps),
        provenance=tuple(step.observation_id for step in steps),
    )
    return PathReplayResult(
        status=PATH_REPLAYED,
        start=start,
        predicted_end=current,
        path=path,
        provenance=path.provenance,
    )


def replay_path_pattern_holdout(
    pattern: PathPattern,
    holdout: Iterable[Node],
    start: NodeRef,
    *,
    allow_reverse: bool = True,
    max_candidates_per_step: int = 1,
) -> PathReplayResult:
    """Build a holdout graph from new observations and replay a PathPattern."""
    observations = tuple(holdout)
    if not allow_reverse:
        graph = build_structural_graph(observations)
        return replay_path_pattern(
            pattern,
            graph,
            start,
            max_candidates_per_step=max_candidates_per_step,
        )
    graph = build_structural_graph(observations)
    return replay_path_pattern(
        pattern,
        graph,
        start,
        max_candidates_per_step=max_candidates_per_step,
    )


def predicted_link_from_replay(result: PathReplayResult, ref_id: Optional[str] = None) -> Optional[RefObject]:
    """Reify a successful replay as an anonymous structural candidate link."""
    if result.status != PATH_REPLAYED or result.path is None:
        return None
    return reify_path_link(result.path, ref_id=ref_id)


def reify_path_link(path: PathRecord, ref_id: Optional[str] = None) -> RefObject:
    """Reify a candidate link derived from a path, still semantically unnamed."""
    ref = ref_id or f"link::{path.path_id}"
    structure = (
        LINK_MARKER,
        path.start,
        path.end,
        tuple((step.operator, step.direction) for step in path.steps),
    )
    return RefObject(NodeRef(ref), structure)
