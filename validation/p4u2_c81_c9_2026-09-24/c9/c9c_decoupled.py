"""C9-C harness (disposable): FFL motif planted by degree-invariant swaps into a simple digraph;
simple-graph degree-preserving MCMC null (switch + directed-triangle reversal). See PREREGISTRATION_C9_C.md.
Usage: python c9c_decoupled.py <repo_path> <config> [...] | mixcheck
"""
from __future__ import annotations

import json
import random
import statistics as st
import sys
import time
from collections import Counter
from multiprocessing import Pool

import c9_2_nontrivial as c92
import p4u2_autonomous_relation_discovery_v0_1 as p4u2

CONFIGS = {
    "C9C-M0":  dict(nodes=100, edges=150, m=0, base=3000000),
    "C9C-M5":  dict(nodes=100, edges=150, m=5, base=3005000),
    "C9C-M12": dict(nodes=100, edges=150, m=12, base=3012000),
    "C9C-S5":  dict(nodes=150, edges=150, m=5, base=3105000),
    "C9C-S12": dict(nodes=150, edges=150, m=12, base=3112000),
}
SEEDS, N_NULL = 100, 200
MOVES_PER_EDGE, TRIANGLE_FRACTION = 100, 0.10


def simple_background(rng, n, e):
    nodes = [f"n{i}" for i in range(n)]
    edges = set()
    while len(edges) < e:
        s, t = rng.sample(nodes, 2)
        edges.add((s, t))
    return nodes, sorted(edges)


def plant_ffl(rng, edges, m, max_tries=10000):
    E = set(edges)
    planted, used = set(), set()
    for _ in range(m):
        for _attempt in range(max_tries):
            out = {}
            for s, t in E:
                out.setdefault(s, []).append(t)
            paths = [(a, b, c) for a, bs in out.items() for b in bs for c in out.get(b, ())
                     if len({a, b, c}) == 3 and (a, c) not in E and not ({a, b, c} & used)]
            if not paths:
                return None
            a, b, c = rng.choice(paths)
            ax = [(a, x) for x in out[a] if x not in (b, c) and (a, x) not in planted]
            yc = [(y, c) for (y, t) in E if t == c and y not in (a, b) and (y, c) not in planted]
            rng.shuffle(ax); rng.shuffle(yc)
            done = False
            for (_, x) in ax:
                for (y, _) in yc:
                    if y != x and (y, x) not in E:
                        E.discard((a, x)); E.discard((y, c)); E.add((a, c)); E.add((y, x))
                        planted |= {(a, b), (b, c), (a, c)}; used |= {a, b, c}
                        done = True
                        break
                if done:
                    break
            if done:
                break
        else:
            return None
    return sorted(E), planted


def mcmc_null(rng, edges, n_moves):
    E = list(edges)
    S = set(E)
    for _ in range(n_moves):
        if rng.random() < TRIANGLE_FRACTION:
            a, b = E[rng.randrange(len(E))]
            # directed triangle a->b->c->a, reversed to a->c->b->a
            candidates = [c for (s, c) in E if s == b and (c, a) in S]
            if not candidates:
                continue
            c = rng.choice(candidates)
            rev = [(a, c), (c, b), (b, a)]
            if any(r in S for r in rev):
                continue
            for old, new in zip([(a, b), (b, c), (c, a)], [(b, a), (c, b), (a, c)]):
                S.discard(old); S.add(new)
                E[E.index(old)] = new
        else:
            i, j = rng.randrange(len(E)), rng.randrange(len(E))
            (a, b), (c, d) = E[i], E[j]
            if i == j or a == d or c == b or (a, d) in S or (c, b) in S:
                continue
            S.discard((a, b)); S.discard((c, d)); S.add((a, d)); S.add((c, b))
            E[i], E[j] = (a, d), (c, b)
    return E


def controls(obs, null, T_truncated):
    return (Counter(s for s, _ in obs) == Counter(s for s, _ in null)
            and Counter(t for _, t in obs) == Counter(t for _, t in null)
            and len(obs) == len(null) and len(set(null)) == len(null)
            and all(s != t for s, t in null) and not T_truncated)


def ffl_count(edges):
    S = set(edges)
    out = {}
    for s, t in S:
        out.setdefault(s, set()).add(t)
    return sum(1 for a, bs in out.items() for b in bs for c in out.get(b, ()) if c != a and c in bs)


def nontrivial_size(groups):
    return sum(len(v) for s, v in groups.items() if s.depth2_count > 0 or s.depth3_count > 0)


def build_observed(cfg, seed):
    rng = random.Random(seed)
    nodes, edges = simple_background(rng, cfg["nodes"], cfg["edges"])
    if cfg["m"] == 0:
        return edges, set()
    res = plant_ffl(rng, edges, cfg["m"])
    if res is None:
        return None, None
    return res


def run_seed(args):
    name, seed = args
    cfg = CONFIGS[name]
    obs, planted = build_observed(cfg, seed)
    if obs is None:
        return dict(seed=seed, invalid="planting_failed")
    o = c92.both_stats(obs)
    if o["truncated"] or len(set(obs)) != len(obs) or any(s == t for s, t in obs):
        return dict(seed=seed, invalid="observed_control_failed")
    idx_planted = {i for i, e in enumerate(obs) if e in planted}
    motif_sigs = {s for s, v in o["groups"].items() if set(v) & idx_planted}
    rows_t, rows_tp, rows_nt, rows_motif, rows_ffl = [], [], [], [], []
    for j in range(N_NULL):
        null = mcmc_null(random.Random(f"C9C|{name}|{seed}|null|{j}"), obs, MOVES_PER_EDGE * len(obs))
        r = c92.both_stats(null)
        if not controls(obs, null, r["truncated"]):
            return dict(seed=seed, invalid=f"null_control_failed_at_{j}")
        rows_t.append(r["t"]); rows_tp.append(r["tp"]); rows_nt.append(nontrivial_size(r["groups"]))
        rows_motif.append(sum(len(r["groups"].get(s, ())) for s in motif_sigs)); rows_ffl.append(ffl_count(null))
    return dict(seed=seed, invalid=None,
                t_obs=o["t"], null_t=rows_t, pct_t=p4u2.percentile_rank(o["t"], rows_t) * 100.0,
                tp_obs=o["tp"], null_tp=rows_tp, pct_tp=p4u2.percentile_rank(o["tp"], rows_tp) * 100.0,
                argmax_t=[repr(s) for s in o["argmax_t"]], argmax_t_family=sorted({c92.family(s) for s in o["argmax_t"]}),
                argmax_tp=[repr(s) for s in o["argmax_tp"]],
                argmax_tp_planted_share=max((len(set(o["groups"][s]) & idx_planted) / len(o["groups"][s]) for s in o["argmax_tp"]), default=None) if planted else None,
                nontrivial_obs=nontrivial_size(o["groups"]), nontrivial_null_mean=st.mean(rows_nt),
                motif_sig_count=len(motif_sigs), motif_obs=sum(len(o["groups"][s]) for s in motif_sigs), motif_null_mean=st.mean(rows_motif),
                ffl_obs=ffl_count(obs), ffl_null_mean=st.mean(rows_ffl))


def mixcheck():
    cfg = CONFIGS["C9C-M0"]
    out = []
    for s in range(5):
        obs, _ = build_observed(cfg, cfg["base"] + s)
        res = {}
        for mult in (30, 100):
            tp, ff = [], []
            for j in range(100):
                null = mcmc_null(random.Random(f"MIX|{s}|{mult}|{j}"), obs, mult * len(obs))
                tp.append(c92.both_stats(null)["tp"]); ff.append(ffl_count(null))
            res[mult] = (st.mean(tp), st.mean(ff))
        rel = [abs(res[30][k] - res[100][k]) / max(1e-9, res[100][k]) for k in (0, 1)]
        out.append(dict(seed=s, tp_30=res[30][0], tp_100=res[100][0], ffl_30=res[30][1], ffl_100=res[100][1], rel_diff=rel))
        print(out[-1], flush=True)
    json.dump(out, open("c9c_mixcheck.json", "w"), indent=1)


def main():
    if sys.argv[2] == "mixcheck":
        return mixcheck()
    for name in sys.argv[2:]:
        t0 = time.time()
        with Pool(4) as pool:
            rows = pool.map(run_seed, [(name, CONFIGS[name]["base"] + s) for s in range(SEEDS)])
        json.dump(dict(config=name, spec=CONFIGS[name], elapsed_s=time.time() - t0, rows=rows), open(f"raw_{name}.json", "w"))
        print(name, "done in %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
