"""Loader for the E13-A.2 micro-corpus.

Keeps the corpus/engine separation the source discussion insists on (section
30-32): the JSON is data (a set of observations), never executable, never
inspected by the engine for what its labels "mean" — kernel.py only ever
compares labels for equality.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from kernel2 import Node, OBSERVATION

DEFAULT_CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "micro_corpus_v001.json"


@dataclass(frozen=True)
class MicroCorpus:
    corpus_id: str
    corpus_version: str
    families: Dict[str, List[Node]]
    non_commutative_pair: Tuple[Node, Node]
    contradiction_probe: Node
    holdout_observation: Node
    holdout_ground_truth: Node


def _obs(entry: dict) -> Node:
    return Node(node_id=entry["id"], kind=OBSERVATION, children=tuple(entry["children"]))


def load_micro_corpus(path: Path = DEFAULT_CORPUS_PATH) -> MicroCorpus:
    data = json.loads(path.read_text(encoding="utf-8"))

    families = {
        name: [_obs(entry) for entry in entries]
        for name, entries in data["families"].items()
    }

    nc = data["non_commutative_counter_example"]
    non_commutative_pair = (_obs(nc["observation_a"]), _obs(nc["observation_b"]))

    contradiction_probe = _obs(data["contradiction_probe"])

    holdout = data["holdout"]
    holdout_observation = _obs(holdout["observation"])
    holdout_ground_truth = _obs(holdout["ground_truth"])

    return MicroCorpus(
        corpus_id=data["corpus_id"],
        corpus_version=data["corpus_version"],
        families=families,
        non_commutative_pair=non_commutative_pair,
        contradiction_probe=contradiction_probe,
        holdout_observation=holdout_observation,
        holdout_ground_truth=holdout_ground_truth,
    )


VALIDATION_CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "validation_corpus_v001.json"


@dataclass(frozen=True)
class ValidationCorpus:
    """The larger, combined-dimension corpus (E14+E15+E16 at scale), requested
    2026-09-16 before attempting E17. Unlike MicroCorpus, families here are
    plain variable-length lists (some carry an extra malformed-arity impostor
    entry) and children can themselves be nested Node objects (E15, including
    depth 3), via a generic recursive builder -- unlike MicroCorpus's flat-only
    `_obs()`, kept untouched so every already-passing E13-A.2/E14/E15/E16 test
    stays exactly as it was."""
    corpus_id: str
    corpus_version: str
    families: Dict[str, List[Node]]
    holdout: Dict[str, Tuple[Node, Node]]  # name -> (observation, ground_truth)


def _build_node(entry: dict) -> Node:
    """Recursively builds a Node from a JSON entry. A child that is itself a
    dict with a "children" key becomes a nested OBSERVATION Node (E15); every
    other child (a plain JSON string) stays an opaque leaf label."""
    children = tuple(
        _build_node(child) if isinstance(child, dict) else child
        for child in entry["children"]
    )
    return Node(node_id=entry["id"], kind=OBSERVATION, children=children)


def load_validation_corpus(path: Path = VALIDATION_CORPUS_PATH) -> ValidationCorpus:
    data = json.loads(path.read_text(encoding="utf-8"))

    families = {
        name: [_build_node(entry) for entry in entries]
        for name, entries in data["families"].items()
    }
    holdout = {
        name: (_build_node(pair["observation"]), _build_node(pair["ground_truth"]))
        for name, pair in data["holdout"].items()
    }

    return ValidationCorpus(
        corpus_id=data["corpus_id"],
        corpus_version=data["corpus_version"],
        families=families,
        holdout=holdout,
    )
