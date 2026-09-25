"""C9-1 harness (disposable): degree-preserving null, T = max_s |G_s| unchanged.

See PREREGISTRATION_C9_1.md. Production module untouched.
Usage: python c9_degree_null.py <repo_path> <config> [...]
"""
from __future__ import annotations

import json
import random
import sys
import time
from multiprocessing import Pool

import c81_confirmation as h  # reads sys.argv[1] as repo path
import p4u2_autonomous_relation_discovery_v0_1 as p4u2
from kernel2 import build_structural_graph, discover_paths

DEADEND = p4u2.Signature(1, 0, 0, frozenset({("FORWARD",)}))
CHAIN_HEAD = p4u2.Signature(1, 1, 0, frozenset({("FORWARD",), ("FORWARD", "FORWARD")}))


def stat(pairs):
    """T, K, dead-end bucket size, chain-head bucket size, argmax signatures, truncated flag."""
    graph = build_structural_graph([h.mk_obs(i, s, t) for i, (s, t) in enumerate(pairs)])
    cache, sigs = {}, []
    truncated = False
    for edge in graph.edges:
        key = edge.source.ref_id
        if key not in cache:
            cache[key] = discover_paths(graph, start=edge.source, max_depth=p4u2.MAX_DEPTH, max_paths=p4u2.MAX_PATHS)
            truncated |= len(cache[key]) >= p4u2.MAX_PATHS
        f = [q for q in cache[key] if q.steps and q.steps[0].edge_id == edge.edge_id]
        sigs.append(p4u2.Signature(sum(q.length == 1 for q in f), sum(q.length == 2 for q in f),
                                   sum(q.length == 3 for q in f), frozenset(q.direction_sequence for q in f)))
    groups = p4u2.group_by_signature(sigs)
    t = max(len(v) for v in groups.values())
    return dict(t=t, k=len(groups), dead=len(groups.get(DEADEND, ())), head=len(groups.get(CHAIN_HEAD, ())),
                argmax=[repr(s) for s, v in groups.items() if len(v) == t], truncated=truncated, groups=groups)


def degree_null(rng, pairs, max_tries=10**6):
    sources = [s for s, _ in pairs]
    targets = [t for _, t in pairs]
    for attempt in range(1, max_tries + 1):
        rng.shuffle(targets)
        if all(s != t for s, t in zip(sources, targets)):
            return list(zip(sources, targets)), attempt
    raise RuntimeError("degree_null: no loop-free permutation within max_tries")


def zipf_pairs(rng, n_nodes, n_edges, s):
    universe = [f"n{i}" for i in range(n_nodes)]
    weights = None if s == 0 else [1.0 / (r + 1) ** s for r in range(n_nodes)]
    return h.uniform_pairs(rng, universe, n_edges, weights)


def sbm_pairs(rng, n_nodes, n_edges, ratio):
    universe = [f"n{i}" for i in range(n_nodes)]
    half = n_nodes // 2
    pairs = []
    for _ in range(n_edges):
        s = rng.randrange(n_nodes)
        w = [0.0 if j == s else (ratio if (j < half) == (s < half) else 1.0) for j in range(n_nodes)]
        t = rng.choices(range(n_nodes), weights=w, k=1)[0]
        pairs.append((universe[s], universe[t]))
    return pairs


CONFIGS = {
    "C9A0":   dict(kind="zipf", nodes=100, edges=100, s=0.0, base=1010000),
    "C9A1":   dict(kind="zipf", nodes=100, edges=100, s=0.5, base=1020000),
    "C9A2":   dict(kind="zipf", nodes=100, edges=100, s=0.75, base=1030000),
    "C9Abis": dict(kind="zipf", nodes=60, edges=100, s=1.0, base=840000),   # same observed graphs as A-bis
    "C9A2rep": dict(kind="zipf", nodes=100, edges=100, s=0.75, base=1130000, seeds=300),
    "C9SBM":  dict(kind="sbm", nodes=100, edges=100, ratio=9.0, base=1050000),
    "C9B1":   dict(kind="signal", chains=15, base=910000),                   # same observed graphs as B1
    "C9B2":   dict(kind="signal", chains=8, base=920000),
    "C9B3":   dict(kind="signal", chains=25, base=930000),
}
SEEDS, N_NULL = 100, 200


def observed(cfg, seed):
    if cfg["kind"] == "signal":
        pairs, chain_idx, _, _ = h.observed_and_null_spec(dict(kind="signal", chains=cfg["chains"]), seed)
        return pairs, chain_idx
    if cfg["kind"] == "zipf" and cfg["nodes"] == 60 and cfg["s"] == 1.0:
        pairs, _, _, _ = h.observed_and_null_spec(dict(kind="zipf", nodes=60, edges=100), seed)  # identical to A-bis
        return pairs, set()
    rng = random.Random(seed)
    if cfg["kind"] == "zipf":
        return zipf_pairs(rng, cfg["nodes"], cfg["edges"], cfg["s"]), set()
    return sbm_pairs(rng, cfg["nodes"], cfg["edges"], cfg["ratio"]), set()


def run_seed(args):
    name, seed = args
    cfg = CONFIGS[name]
    pairs, chain_idx = observed(cfg, seed)
    o = stat(pairs)
    null_t, null_dead, null_head, tries, null_trunc = [], [], [], [], 0
    for j in range(N_NULL):
        rng = random.Random(f"C9|{name}|{seed}|null|{j}")
        npairs, att = degree_null(rng, pairs)
        r = stat(npairs)
        null_t.append(r["t"]); null_dead.append(r["dead"]); null_head.append(r["head"])
        tries.append(att); null_trunc += r["truncated"]
    pct = p4u2.percentile_rank(o["t"], null_t) * 100.0
    chain_share = None
    if chain_idx:
        chain_share = max(sum(i in chain_idx for i in idxs) / len(idxs)
                          for s, idxs in o["groups"].items() if len(idxs) == o["t"])
    return dict(seed=seed, t_obs=o["t"], k_obs=o["k"], pct=pct, null_t=null_t, null_k_mean=0,
                dead_obs=o["dead"], dead_null_mean=sum(null_dead) / N_NULL, dead_null_min=min(null_dead), dead_null_max=max(null_dead),
                head_obs=o["head"], head_null_mean=sum(null_head) / N_NULL,
                argmax=o["argmax"], obs_truncated=o["truncated"], null_truncated=null_trunc,
                mean_tries=sum(tries) / N_NULL, argmax_chain_share=chain_share)


def main():
    for name in sys.argv[2:]:
        t0 = time.time()
        with Pool(4) as pool:
            rows = pool.map(run_seed, [(name, CONFIGS[name]["base"] + s) for s in range(CONFIGS[name].get("seeds", SEEDS))])
        json.dump(dict(config=name, spec=CONFIGS[name], elapsed_s=time.time() - t0, rows=rows), open(f"raw_{name}.json", "w"))
        print(name, "done in %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
