"""C9-2 harness (disposable): T' = max over non-trivial signatures (d2>0 or d3>0), C9-1 null unchanged.

See PREREGISTRATION_C9_2.md. T is recomputed on the same graphs and the same null replicates (paired).
Usage: python c9_2_nontrivial.py <repo_path> <config> [...]
"""
from __future__ import annotations

import json
import random
import sys
import time
from multiprocessing import Pool

import c81_confirmation as h
import c9_degree_null as c9
import p4u2_autonomous_relation_discovery_v0_1 as p4u2

CONFIGS = {
    "C92A0":   dict(kind="zipf", nodes=100, edges=100, s=0.0, base=2010000),
    "C92A1":   dict(kind="zipf", nodes=100, edges=100, s=0.5, base=2020000),
    "C92A2":   dict(kind="zipf", nodes=100, edges=100, s=0.75, base=2030000),
    "C92SBM":  dict(kind="sbm", nodes=100, edges=100, ratio=9.0, base=2050000),
    "C92Abis": dict(kind="zipf60", base=2040000),
    "C92B2":   dict(kind="signal", chains=8, base=2120000),
    "C92B1":   dict(kind="signal", chains=15, base=2110000),
    "C92B3":   dict(kind="signal", chains=25, base=2130000),
}
SEEDS, N_NULL = 100, 200


def family(sig):
    if sig.depth1_count == 0:
        return "TRUNCATED_EMPTY"
    if sig.depth2_count > 0 or sig.depth3_count > 0:
        return "NONTRIVIAL"
    return "DEADEND"


def both_stats(pairs):
    r = c9.stat(pairs)
    g = r["groups"]
    nontriv = {s: v for s, v in g.items() if s.depth2_count > 0 or s.depth3_count > 0}
    tp = max((len(v) for v in nontriv.values()), default=0)
    argmax_tp = [s for s, v in nontriv.items() if len(v) == tp] if tp else []
    argmax_t = [s for s, v in g.items() if len(v) == r["t"]]
    return dict(t=r["t"], tp=tp, argmax_t=argmax_t, argmax_tp=argmax_tp, groups=g, truncated=r["truncated"])


def observed(cfg, seed):
    if cfg["kind"] == "signal":
        pairs, chain_idx, _, _ = h.observed_and_null_spec(dict(kind="signal", chains=cfg["chains"]), seed)
        return pairs, chain_idx
    if cfg["kind"] == "zipf60":
        pairs, _, _, _ = h.observed_and_null_spec(dict(kind="zipf", nodes=60, edges=100), seed)
        return pairs, set()
    return c9.observed(cfg, seed)


def run_seed(args):
    name, seed = args
    cfg = CONFIGS[name]
    pairs, chain_idx = observed(cfg, seed)
    o = both_stats(pairs)
    null_t, null_tp, null_trunc = [], [], 0
    null_bucket_of_obs_argmax_tp = []
    for j in range(N_NULL):
        npairs, _ = c9.degree_null(random.Random(f"C92|{name}|{seed}|null|{j}"), pairs)
        r = both_stats(npairs)
        null_t.append(r["t"]); null_tp.append(r["tp"]); null_trunc += r["truncated"]
        null_bucket_of_obs_argmax_tp.append(max((len(r["groups"].get(s, ())) for s in o["argmax_tp"]), default=0))
    out = dict(seed=seed, obs_truncated=o["truncated"], null_truncated=null_trunc,
               t_obs=o["t"], null_t=null_t, pct_t=p4u2.percentile_rank(o["t"], null_t) * 100.0,
               tp_obs=o["tp"], null_tp=null_tp, pct_tp=p4u2.percentile_rank(o["tp"], null_tp) * 100.0,
               argmax_t=[repr(s) for s in o["argmax_t"]], argmax_t_family=sorted({family(s) for s in o["argmax_t"]}),
               argmax_tp=[repr(s) for s in o["argmax_tp"]],
               argmax_tp_bucket_obs=o["tp"], argmax_tp_bucket_null_mean=sum(null_bucket_of_obs_argmax_tp) / N_NULL)
    if chain_idx:
        out["argmax_tp_chain_share"] = max((sum(i in chain_idx for i in o["groups"][s]) / len(o["groups"][s]) for s in o["argmax_tp"]), default=None)
    return out


def main():
    for name in sys.argv[2:]:
        t0 = time.time()
        with Pool(4) as pool:
            rows = pool.map(run_seed, [(name, CONFIGS[name]["base"] + s) for s in range(SEEDS)])
        json.dump(dict(config=name, spec=CONFIGS[name], elapsed_s=time.time() - t0, rows=rows), open(f"raw_{name}.json", "w"))
        print(name, "done in %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
