"""C8.1-confirmation harness (disposable, not production).

Reconstructs the C8.1 support-statistic test from the UNMODIFIED production
module p4u2_autonomous_relation_discovery_v0_1 (V10-Research 2631252).
See PREREGISTRATION.md for protocol and frozen exit criteria.

Usage: python c81_confirmation.py <repo_path> <config_name> [...]
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from multiprocessing import Pool

REPO = sys.argv[1]
sys.path.insert(0, REPO)

import p4u2_autonomous_relation_discovery_v0_1 as p4u2  # noqa: E402
from kernel2 import Node, NodeRef, OBSERVATION, build_structural_graph, discover_paths  # noqa: E402


def mk_obs(idx, src, tgt):
    return Node(f"obs::{idx}", OBSERVATION, (NodeRef(f"OP#{idx:05d}"), NodeRef(src), NodeRef(tgt)),
                provenance=(f"obs::{idx}",))


def signatures(observations):
    """Bit-identical to p4u2.compute_signatures (verified): discover_paths
    depends only on (graph, start), so caching by source node is exact."""
    graph = build_structural_graph(observations)
    cache = {}
    out = []
    for edge in graph.edges:
        key = edge.source.ref_id
        if key not in cache:
            cache[key] = discover_paths(graph, start=edge.source, max_depth=p4u2.MAX_DEPTH, max_paths=p4u2.MAX_PATHS)
        f = [q for q in cache[key] if q.steps and q.steps[0].edge_id == edge.edge_id]
        out.append(p4u2.Signature(sum(q.length == 1 for q in f), sum(q.length == 2 for q in f),
                                  sum(q.length == 3 for q in f), frozenset(q.direction_sequence for q in f)))
    return tuple(out)


def support_stat(pairs):
    sigs = signatures([mk_obs(i, s, t) for i, (s, t) in enumerate(pairs)])
    groups = p4u2.group_by_signature(sigs)
    t = max(len(v) for v in groups.values())
    argmax = [idxs for idxs in groups.values() if len(idxs) == t]
    return t, len(groups), argmax


def uniform_pairs(rng, universe, n_edges, weights=None):
    pairs = []
    for _ in range(n_edges):
        if weights is None:
            pairs.append(tuple(rng.sample(universe, 2)))
        else:
            while True:
                s, t = rng.choices(universe, weights=weights, k=2)
                if s != t:
                    pairs.append((s, t))
                    break
    return pairs


# ---------------------------------------------------------------------------
# Configurations (PREREGISTRATION.md)
# ---------------------------------------------------------------------------

CONFIGS = {
    "R0_noise":  dict(kind="noise", nodes=60, edges=100, seeds=40, n_null=50, base=710000),
    "R0_signal": dict(kind="signal", chains=15, seeds=25, n_null=50, base=720000),
    "A1":        dict(kind="noise", nodes=60, edges=100, seeds=100, n_null=200, base=810000),
    "A2":        dict(kind="noise", nodes=150, edges=100, seeds=100, n_null=200, base=820000),
    "A3":        dict(kind="noise", nodes=250, edges=100, seeds=100, n_null=200, base=830000),
    "Abis":      dict(kind="zipf", nodes=60, edges=100, seeds=100, n_null=200, base=840000),
    "B1":        dict(kind="signal", chains=15, seeds=100, n_null=200, base=910000),
    "B2":        dict(kind="signal", chains=8, seeds=100, n_null=200, base=920000),
    "B3":        dict(kind="signal", chains=25, seeds=100, n_null=200, base=930000),
}
BG_NODES, BG_EDGES = 60, 80


def observed_and_null_spec(cfg, seed):
    rng = random.Random(seed)
    if cfg["kind"] in ("noise", "zipf"):
        universe = [f"n{i}" for i in range(cfg["nodes"])]
        weights = [1.0 / (r + 1) for r in range(len(universe))] if cfg["kind"] == "zipf" else None
        pairs = uniform_pairs(rng, universe, cfg["edges"], weights)
        return pairs, set(), universe, cfg["edges"]
    c = cfg["chains"]
    bg = [f"n{i}" for i in range(BG_NODES)]
    chain_pairs = []
    for k in range(c):
        chain_pairs += [(f"cA{k}", f"cB{k}"), (f"cB{k}", f"cC{k}")]
    pairs = chain_pairs + uniform_pairs(rng, bg, BG_EDGES)
    rng.shuffle(pairs)
    chain_set = set(chain_pairs)
    chain_idx = {i for i, pr in enumerate(pairs) if pr in chain_set}
    universe = bg + [f"c{x}{k}" for k in range(c) for x in "ABC"]
    return pairs, chain_idx, universe, BG_EDGES + 2 * c


def run_seed(args):
    name, seed = args
    cfg = CONFIGS[name]
    pairs, chain_idx, universe, n_edges = observed_and_null_spec(cfg, seed)
    t_obs, k_obs, argmax = support_stat(pairs)
    null_t, null_k = [], []
    for j in range(cfg["n_null"]):
        rng = random.Random(f"{name}|{seed}|null|{j}")
        t, k, _ = support_stat(uniform_pairs(rng, universe, n_edges))
        null_t.append(t)
        null_k.append(k)
    pct = p4u2.percentile_rank(t_obs, null_t) * 100.0
    chain_share = None
    if chain_idx:
        chain_share = max(sum(i in chain_idx for i in idxs) / len(idxs) for idxs in argmax)
    return dict(seed=seed, t_obs=t_obs, k_obs=k_obs, pct=pct, null_t=null_t, null_k_mean=sum(null_k) / len(null_k),
                argmax_chain_share=chain_share, n_argmax=len(argmax))


def main():
    for name in sys.argv[2:]:
        cfg = CONFIGS[name]
        t0 = time.time()
        with Pool(4) as pool:
            rows = pool.map(run_seed, [(name, cfg["base"] + s) for s in range(cfg["seeds"])])
        out = dict(config=name, spec=cfg, elapsed_s=time.time() - t0, rows=rows)
        with open(f"raw_{name}.json", "w") as fh:
            json.dump(out, fh)
        print(name, "done in %.0fs" % out["elapsed_s"], flush=True)


if __name__ == "__main__":
    main()
