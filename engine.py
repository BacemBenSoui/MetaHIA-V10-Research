from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Optional

from kernel2 import Node, StructuralGraph, build_structural_graph, discover_paths
from m3_recursive_structural_closure_v0_1 import ClosureConfig, ClosureResult, run_closure


class MetaHIAEngine:
    """Thin runtime facade for the currently implemented MetaHIA core.

    Input is already structured as ``Node`` observations. Text parsing and live
    LLM communication are intentionally out of scope and documented separately.
    """

    def __init__(self, observations: Iterable[Node] = ()) -> None:
        self.observations = tuple(observations)

    def graph(self) -> StructuralGraph:
        return build_structural_graph(self.observations)

    def paths(self, *, max_depth: int = 3, allow_reverse: bool = True, max_paths: int = 1000):
        return discover_paths(
            self.graph(),
            max_depth=max_depth,
            allow_reverse=allow_reverse,
            max_paths=max_paths,
        )

    def closure(self, config: Optional[ClosureConfig] = None) -> ClosureResult:
        return run_closure(self.graph(), config=config or ClosureConfig())

    def summary(self) -> dict[str, Any]:
        g = self.graph()
        ps = self.paths()
        return {
            'observations': len(self.observations),
            'graph_nodes': len(g.nodes),
            'graph_edges': len(g.edges),
            'paths': len(ps),
        }


def closure_summary(result: ClosureResult) -> dict[str, Any]:
    return asdict(result)
