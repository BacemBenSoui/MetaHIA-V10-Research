"""MetaHIA E20-D.6 — structural rationalization / historical rapprochement v0.1.

Purpose:
  Keep the generative structural/operational core open, while allowing a
  separate statistical-like layer to propose similarities between generated
  structures and remembered structures.

Invariant:
  GENERATED structure is never rewritten into the historical candidate.
  The result is an evidential relation carrying similarity + provenance.

This prototype deliberately avoids semantic dictionaries. Similarity is based
only on structural sets of opaque evidence references and coarse structural
signatures. A high similarity does not assert identity; it yields a
SUPPORTED_HISTORICAL hypothesis that remains separate from the generated item.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from kernel2 import Node, NodeRef, RefObject, structural_signature, structural_equal, ref_object

GENERATED = "GENERATED"
UNKNOWN = "UNKNOWN"
SUPPORTED_HISTORICAL = "SUPPORTED_HISTORICAL"
RATIONALIZATION = "RATIONALIZATION"


@dataclass(frozen=True)
class RationalizationResult:
    generated: RefObject
    historical: RefObject
    similarity: float
    status: str
    evidence: Tuple[str, ...]


def _opaque_refs(obj: object) -> set[str]:
    """Collect NodeRef ids without dereferencing external values."""
    if isinstance(obj, NodeRef):
        return {obj.ref_id}
    if isinstance(obj, RefObject):
        return _opaque_refs(obj.structure)
    if isinstance(obj, Node):
        out: set[str] = set()
        for c in obj.children:
            out |= _opaque_refs(c)
        return out
    if isinstance(obj, tuple):
        out: set[str] = set()
        for c in obj:
            out |= _opaque_refs(c)
        return out
    if isinstance(obj, list):
        out: set[str] = set()
        for c in obj:
            out |= _opaque_refs(c)
        return out
    return set()


def ref_jaccard(a: object, b: object) -> float:
    """Generic Jaccard similarity on opaque structural references."""
    sa, sb = _opaque_refs(a), _opaque_refs(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    return len(sa & sb) / len(union)


def structural_similarity(a: object, b: object) -> float:
    """Bounded similarity with exact structural equality as a special case.

    Exact equality is deliberately stronger than the approximate score. For
    non-identical structures, Jaccard over opaque references is the only signal
    in this micro-layer.
    """
    if structural_equal(a, b):
        return 1.0
    return ref_jaccard(a, b)


def rationalize(
    generated: RefObject,
    historical_candidates: Sequence[RefObject],
    *,
    threshold: float = 0.97,
) -> Optional[RationalizationResult]:
    """Find the best historical structural analogue without rewriting source."""
    if not historical_candidates:
        return None
    scored = [(structural_similarity(generated.structure, h.structure), h) for h in historical_candidates]
    scored.sort(key=lambda x: (-x[0], x[1].ref.ref_id))
    score, historical = scored[0]
    status = SUPPORTED_HISTORICAL if score >= threshold else UNKNOWN
    evidence = (
        f"generated={generated.ref.ref_id}",
        f"historical={historical.ref.ref_id}",
        f"similarity={score:.6f}",
        f"threshold={threshold:.6f}",
    )
    return RationalizationResult(generated, historical, score, status, evidence)


def remember_rationalization(result: RationalizationResult) -> RefObject:
    """Reify the historical rapprochement as a separate structural object."""
    node = Node(
        f"rationalization::{result.generated.ref.ref_id}::{result.historical.ref.ref_id}",
        RATIONALIZATION,
        (
            result.generated.ref,
            result.historical.ref,
            NodeRef(f"SIM:{result.similarity:.6f}"),
            NodeRef(result.status),
        ),
    )
    return ref_object(f"RAT::{result.generated.ref.ref_id}::{result.historical.ref.ref_id}", node)
