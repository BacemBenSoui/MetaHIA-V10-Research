"""MetaHIA M3 — Recursive Structural Closure v0.1.

This module orchestrates the already validated K3 structural primitives without
adding new semantic primitives to ``kernel2.py``.

Pipeline:
    Graph -> Path discovery -> candidate frontier -> optional ROI selection
          -> Link reification -> graph reinjection -> repeat

Design constraints:
- structural/opaque operation only;
- reference identity != structural equality != external payload equality;
- DERIVED structures are never treated as epistemic evidence;
- provenance is retained on every generated link/path;
- closure is explicit, bounded, deterministic and fail-closed;
- the original graph is never mutated.

M3 is an orchestration layer. It does not decide semantic truth.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Callable, Iterable, Optional, Sequence, Tuple

from kernel2 import (
    NodeRef,
    RefObject,
    StructuralGraph,
    PathRecord,
    discover_paths,
    reify_path_link,
    reinject_reified_links,
    structural_equal,
)

try:
    from e20d_cognitive_control_v0_1 import (
        PathCandidate,
        CognitiveScore,
        build_candidate,
        score_candidate,
    )
except ImportError:  # pragma: no cover - optional integration safeguard
    PathCandidate = None  # type: ignore[assignment,misc]
    CognitiveScore = None  # type: ignore[assignment,misc]
    build_candidate = None  # type: ignore[assignment,misc]
    score_candidate = None  # type: ignore[assignment,misc]


STOP_SATURATED = "SATURATED"
STOP_MAX_PASSES = "MAX_PASSES"
STOP_MAX_LINKS = "MAX_LINKS"
STOP_EMPTY = "EMPTY"

SELECTION_EXHAUSTIVE = "EXHAUSTIVE"
SELECTION_ROI = "ROI"


@dataclass(frozen=True)
class ClosureConfig:
    """Bounded M3 exploration policy.

    The bounds are exploration controls, not semantic constraints.
    """

    max_passes: int = 8
    max_depth: int = 3
    max_paths: int = 1000
    max_new_links_per_pass: int = 100
    min_path_length: int = 2
    allow_reverse: bool = True
    selection: str = SELECTION_EXHAUSTIVE
    roi_explore_threshold: float = 0.5
    roi_defer_threshold: float = 0.2
    expected_gain: float = 1.0
    structural_novelty: float = 1.0

    def validate(self) -> None:
        if self.max_passes < 1:
            raise ValueError("max_passes must be >= 1")
        if self.max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        if self.max_paths < 1:
            raise ValueError("max_paths must be >= 1")
        if self.max_new_links_per_pass < 1:
            raise ValueError("max_new_links_per_pass must be >= 1")
        if self.min_path_length < 1:
            raise ValueError("min_path_length must be >= 1")
        if self.selection not in (SELECTION_EXHAUSTIVE, SELECTION_ROI):
            raise ValueError("selection must be EXHAUSTIVE or ROI")
        if self.roi_explore_threshold < self.roi_defer_threshold:
            raise ValueError("roi_explore_threshold must be >= roi_defer_threshold")


@dataclass(frozen=True)
class GeneratedLinkTrace:
    """Audit trace connecting a generated link to its source path."""

    link_ref_id: str
    path_id: str
    start_ref_id: str
    end_ref_id: str
    path_provenance: Tuple[str, ...]


@dataclass(frozen=True)
class ClosurePassRecord:
    """Observable accounting for one closure pass."""

    pass_index: int
    input_nodes: int
    input_edges: int
    discovered_paths: int
    eligible_paths: int
    frontier_paths: int
    selected_paths: int
    generated_links: int
    new_links: int
    output_nodes: int
    output_edges: int
    truncated_by_max_paths: bool
    stop_after_pass: Optional[str]
    estimated_cost: float
    provenance: Tuple[str, ...]
    generated_link_traces: Tuple[GeneratedLinkTrace, ...] = ()


@dataclass(frozen=True)
class ClosureResult:
    """Complete deterministic result of an M3 closure run."""

    initial_graph: StructuralGraph
    final_graph: StructuralGraph
    passes: Tuple[ClosurePassRecord, ...]
    generated_links: Tuple[RefObject, ...]
    generated_link_traces: Tuple[GeneratedLinkTrace, ...]
    saturated: bool
    stop_reason: str

    @property
    def pass_count(self) -> int:
        return len(self.passes)

    @property
    def total_new_links(self) -> int:
        return sum(record.new_links for record in self.passes)

    @property
    def total_discovered_paths(self) -> int:
        return sum(record.discovered_paths for record in self.passes)

    @property
    def total_cost(self) -> float:
        return sum(record.estimated_cost for record in self.passes)

    @property
    def provenance_complete(self) -> bool:
        return all(
            trace.path_provenance and trace.path_id
            for trace in self.generated_link_traces
        )


def _stable_token(value: object) -> str:
    """Serialize a structural token deterministically enough for local IDs."""
    return repr(value)


def _link_structural_signature(link: RefObject) -> tuple:
    """Return a stable structure key for duplicate suppression."""
    return (link.structure,)


def _known_link_signatures(graph: StructuralGraph) -> set[tuple]:
    known: set[tuple] = set()
    for edge in graph.edges:
        operator = edge.operator
        if not isinstance(operator, RefObject):
            continue
        structure = operator.structure
        if isinstance(structure, tuple) and len(structure) == 4 and structure[0] == "LINK":
            known.add(_link_structural_signature(operator))
    return known


def _path_candidate_key(path: PathRecord) -> tuple:
    """Structural candidate identity: endpoints + operator/direction skeleton."""
    return (
        path.start,
        path.end,
        tuple((step.operator, step.direction) for step in path.steps),
    )


def _stable_link_ref(path: PathRecord, pass_index: int, ordinal: int) -> str:
    payload = _stable_token((pass_index, ordinal, _path_candidate_key(path)))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"M3::LINK::{pass_index:03d}::{ordinal:04d}::{digest}"


def _deduplicate_paths(paths: Iterable[PathRecord]) -> Tuple[PathRecord, ...]:
    """Keep first path for each structural endpoint/skeleton candidate."""
    seen: set[tuple] = set()
    result = []
    for path in paths:
        key = _path_candidate_key(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return tuple(result)


def _roi_select(
    paths: Sequence[PathRecord],
    graph: StructuralGraph,
    known_paths: Sequence[PathRecord],
    *,
    explore_threshold: float,
    defer_threshold: float,
    expected_gain: float,
    structural_novelty: float,
) -> Tuple[Tuple[PathRecord, ...], Tuple[object, ...]]:
    """Select paths through the existing D19 structural ROI layer."""
    if build_candidate is None or score_candidate is None:
        raise RuntimeError("D19 cognitive-control module is unavailable")

    scored = []
    for path in paths:
        candidate = build_candidate(
            path,
            expected_gain=expected_gain,
            structural_novelty=structural_novelty,
            known_paths=known_paths,
        )
        scored.append(
            score_candidate(
                candidate,
                explore_threshold=explore_threshold,
                defer_threshold=defer_threshold,
            )
        )

    ordered = sorted(scored, key=lambda score: (-score.roi, score.path_id))
    selected = {score.path_id for score in ordered if score.decision == "EXPLORE"}
    return (
        tuple(path for path in paths if path.path_id in selected),
        tuple(ordered),
    )


def one_pass(
    graph: StructuralGraph,
    *,
    pass_index: int = 0,
    config: ClosureConfig = ClosureConfig(),
    known_paths: Sequence[PathRecord] = (),
    start: Optional[NodeRef] = None,
    end: Optional[NodeRef] = None,
) -> Tuple[StructuralGraph, ClosurePassRecord, Tuple[RefObject, ...]]:
    """Execute exactly one explicit closure pass."""
    config.validate()

    paths = discover_paths(
        graph,
        start=start,
        end=end,
        max_depth=config.max_depth,
        allow_reverse=config.allow_reverse,
        max_paths=config.max_paths,
    )
    eligible = tuple(path for path in paths if path.length >= config.min_path_length)
    frontier = _deduplicate_paths(eligible)
    if config.selection == SELECTION_ROI:
        selected, _scores = _roi_select(
            frontier,
            graph,
            known_paths,
            explore_threshold=config.roi_explore_threshold,
            defer_threshold=config.roi_defer_threshold,
            expected_gain=config.expected_gain,
            structural_novelty=config.structural_novelty,
        )
    else:
        selected = frontier

    known_link_sigs = _known_link_signatures(graph)
    links = []
    link_traces = []
    selected_sorted = sorted(selected, key=lambda path: path.path_id)
    for ordinal, path in enumerate(selected_sorted):
        link = reify_path_link(
            path,
            ref_id=_stable_link_ref(path, pass_index, ordinal),
        )
        if _link_structural_signature(link) in known_link_sigs:
            continue
        links.append(link)
        link_traces.append(
            GeneratedLinkTrace(
                link_ref_id=link.ref.ref_id,
                path_id=path.path_id,
                start_ref_id=path.start.ref_id,
                end_ref_id=path.end.ref_id,
                path_provenance=tuple(path.provenance),
            )
        )
        known_link_sigs.add(_link_structural_signature(link))
        if len(links) >= config.max_new_links_per_pass:
            break

    next_graph = reinject_reified_links(graph, links)
    provenance = []
    for trace in link_traces:
        provenance.extend(trace.path_provenance)
        provenance.append(trace.link_ref_id)

    estimated_cost = float(len(paths)) + 0.25 * sum(path.length for path in paths)
    truncated = len(paths) >= config.max_paths
    stop_reason = STOP_SATURATED if not links else None
    if links and len(links) >= config.max_new_links_per_pass and len(frontier) > len(links):
        stop_reason = STOP_MAX_LINKS

    record = ClosurePassRecord(
        pass_index=pass_index,
        input_nodes=len(graph.nodes),
        input_edges=len(graph.edges),
        discovered_paths=len(paths),
        eligible_paths=len(eligible),
        frontier_paths=len(frontier),
        selected_paths=len(selected),
        generated_links=len(links),
        new_links=max(0, len(next_graph.edges) - len(graph.edges)),
        output_nodes=len(next_graph.nodes),
        output_edges=len(next_graph.edges),
        truncated_by_max_paths=truncated,
        stop_after_pass=stop_reason,
        estimated_cost=estimated_cost,
        provenance=tuple(dict.fromkeys(provenance)),
        generated_link_traces=tuple(link_traces),
    )
    return next_graph, record, tuple(links)


def run_closure(
    graph: StructuralGraph,
    *,
    config: ClosureConfig = ClosureConfig(),
    start: Optional[NodeRef] = None,
    end: Optional[NodeRef] = None,
) -> ClosureResult:
    """Run bounded recursive structural closure until saturation or a bound."""
    config.validate()
    current = graph
    records = []
    all_links = []
    all_link_traces = []
    known_paths: list[PathRecord] = []
    saturated = False
    stop_reason = STOP_MAX_PASSES

    for pass_index in range(config.max_passes):
        next_graph, record, links = one_pass(
            current,
            pass_index=pass_index,
            config=config,
            known_paths=tuple(known_paths),
            start=start,
            end=end,
        )
        records.append(record)
        all_links.extend(links)
        all_link_traces.extend(record.generated_link_traces)

        current = next_graph
        if record.generated_links == 0:
            saturated = True
            stop_reason = STOP_EMPTY if record.discovered_paths == 0 else STOP_SATURATED
            break
        if record.new_links == 0:
            saturated = True
            stop_reason = STOP_SATURATED
            break
        if record.stop_after_pass == STOP_MAX_LINKS:
            # Continue with a fresh frontier in the next pass. The stop reason
            # is only recorded on the pass; global closure remains active.
            pass

        # Retain only a compact path history for D19 redundancy estimation.
        # Re-discovery is cheap and structural; provenance is not used as a
        # truth signal.
        known_paths = list(discover_paths(
            current,
            max_depth=config.max_depth,
            allow_reverse=config.allow_reverse,
            max_paths=config.max_paths,
        ))

    else:
        stop_reason = STOP_MAX_PASSES

    return ClosureResult(
        initial_graph=graph,
        final_graph=current,
        passes=tuple(records),
        generated_links=tuple(all_links),
        generated_link_traces=tuple(all_link_traces),
        saturated=saturated,
        stop_reason=stop_reason,
    )


__all__ = [
    "ClosureConfig",
    "GeneratedLinkTrace",
    "ClosurePassRecord",
    "ClosureResult",
    "STOP_SATURATED",
    "STOP_MAX_PASSES",
    "STOP_MAX_LINKS",
    "STOP_EMPTY",
    "SELECTION_EXHAUSTIVE",
    "SELECTION_ROI",
    "one_pass",
    "run_closure",
]
