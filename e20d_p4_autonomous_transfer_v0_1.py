"""E20-D/P4.3 -- autonomous structural invariant discovery and blind transfer.

Experimental gate: discover an operator-agnostic path shape from a SOURCE graph,
then transfer only that shape to a TARGET graph. Discovery never reads target
facts, target labels, semantic dictionaries, or expected endpoints.

The abstraction contains only:
  length, direction sequence, and reference-binding equality pattern.
Operator identities are intentionally removed. This is a research witness,
not a new M1 primitive and not a claim of semantic equivalence.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable, Sequence, Tuple

from kernel2 import Node, NodeRef, OBSERVATION, PathRecord, build_structural_graph, discover_paths, reference_equal

@dataclass(frozen=True)
class AbstractPathInvariant:
    invariant_id: str
    length: int
    direction_sequence: Tuple[str, ...]
    node_binding: Tuple[int, ...]
    support_count: int
    source_path_ids: Tuple[str, ...]

    def signature(self) -> tuple:
        return (self.length, self.direction_sequence, self.node_binding)

@dataclass(frozen=True)
class TransferCandidate:
    invariant_id: str
    target_path_id: str
    start: NodeRef
    predicted_end: NodeRef
    target_operator_sequence: Tuple[NodeRef, ...]


def _binding(path: PathRecord) -> Tuple[int, ...]:
    roots: list[NodeRef] = []
    out: list[int] = []
    for node in path.node_sequence:
        found = next((i for i, ref in enumerate(roots) if reference_equal(node, ref)), None)
        if found is None:
            roots.append(node); found = len(roots) - 1
        out.append(found)
    return tuple(out)


def _shape(path: PathRecord) -> tuple:
    return (path.length, path.direction_sequence, _binding(path))


def discover_source_invariants(paths: Sequence[PathRecord], *, min_support: int = 2) -> Tuple[AbstractPathInvariant, ...]:
    """Discover repeated operator-agnostic shapes from SOURCE paths only."""
    groups: dict[tuple, list[PathRecord]] = defaultdict(list)
    for p in paths:
        groups[_shape(p)].append(p)
    result = []
    for sig, items in sorted(groups.items(), key=lambda kv: repr(kv[0])):
        if len(items) < min_support:
            continue
        length, directions, binding = sig
        result.append(AbstractPathInvariant(
            invariant_id=f"INV::{length}::{','.join(directions)}::{','.join(map(str,binding))}",
            length=length,
            direction_sequence=tuple(directions),
            node_binding=tuple(binding),
            support_count=len(items),
            source_path_ids=tuple(p.path_id for p in items),
        ))
    return tuple(result)


def transfer_invariants_blind(invariants: Sequence[AbstractPathInvariant], target_paths: Sequence[PathRecord]) -> Tuple[TransferCandidate, ...]:
    """Apply source-discovered shapes to target paths; no target outcome is read."""
    by_shape = {_shape(p): p for p in target_paths}
    out=[]
    for inv in invariants:
        for shape, p in by_shape.items():
            if shape != inv.signature():
                continue
            out.append(TransferCandidate(inv.invariant_id, p.path_id, p.node_sequence[0], p.node_sequence[-1], tuple(step.operator for step in p.steps)))
    return tuple(out)


def make_paths(facts: Iterable[tuple], max_depth: int = 2) -> Tuple[PathRecord, ...]:
    edges=[Node(i,OBSERVATION,(NodeRef(op),NodeRef(a),NodeRef(b)),provenance=(i,)) for i,op,a,b in facts]
    graph=build_structural_graph(edges)
    nodes=sorted({x for e in edges for x in e.children[1:] if isinstance(x,NodeRef)}, key=lambda x:x.ref_id)
    paths=[]
    for start in nodes:
        for end in nodes:
            if start == end: continue
            paths.extend(discover_paths(graph,start,end,max_depth,allow_reverse=True))
    return tuple(paths)
