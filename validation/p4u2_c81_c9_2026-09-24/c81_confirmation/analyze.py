"""Analysis of raw_*.json produced by c81_confirmation.py (see PREREGISTRATION.md)."""
import json
import math
import random
import statistics as st
import sys

from scipy import stats


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def midrank(x, vals):
    below = sum(v < x for v in vals)
    tied = sum(v == x for v in vals)
    return (below + 0.5 * tied) / len(vals)


def alpha_eff(rows, thr=0.95):
    """Exact size of the discrete mid-rank test under exchangeability,
    estimated leave-one-out over the null replicates of every seed."""
    hits = tot = 0
    for r in rows:
        nt = r["null_t"]
        for j in range(len(nt)):
            others = nt[:j] + nt[j + 1:]
            hits += midrank(nt[j], others) >= thr
            tot += 1
    return hits / tot


def pit(rows, seed=12345):
    rng = random.Random(seed)
    us = []
    for r in rows:
        nt, x = r["null_t"], r["t_obs"]
        below = sum(v < x for v in nt)
        tied = sum(v == x for v in nt)
        us.append((below + rng.random() * (tied + 1)) / (len(nt) + 1))
    return us


def q(vals):
    s = sorted(vals)
    return {"min": s[0], "q25": s[len(s) // 4], "median": st.median(s), "q75": s[(3 * len(s)) // 4], "max": s[-1]}


def summarize(name):
    d = json.load(open(f"raw_{name}.json"))
    rows = d["rows"]
    n = len(rows)
    pcts = [r["pct"] for r in rows]
    k = sum(p >= 95.0 for p in pcts)
    a_eff = alpha_eff(rows)
    lo, hi = wilson(k, n)
    us = pit(rows)
    ks = stats.kstest(us, "uniform")
    counts = [0] * 10
    for u in us:
        counts[min(9, int(u * 10))] += 1
    chi = stats.chisquare(counts)
    null_all = [t for r in rows for t in r["null_t"]]
    tie_mass = st.mean(sum(v == r["t_obs"] for v in r["null_t"]) / len(r["null_t"]) for r in rows)
    out = dict(
        config=name, spec=d["spec"], n=n, rejections=k, rate=k / n, wilson95=(lo, hi), alpha_eff=a_eff,
        binom_two_sided_p=stats.binomtest(k, n, a_eff).pvalue,
        binom_greater_p=stats.binomtest(k, n, a_eff, alternative="greater").pvalue,
        pct_mean=st.mean(pcts), pct_median=st.median(pcts), pct_sorted=sorted(pcts),
        pit_ks_p=ks.pvalue, pit_chi2_p=chi.pvalue, pit_decile_counts=counts,
        t_obs=q([r["t_obs"] for r in rows]), t_null=q(null_all),
        k_obs_mean=st.mean(r["k_obs"] for r in rows), k_null_mean=st.mean(r["null_k_mean"] for r in rows),
        mean_tie_mass=tie_mass, elapsed_s=d["elapsed_s"],
    )
    shares = [r["argmax_chain_share"] for r in rows if r["argmax_chain_share"] is not None]
    if shares:
        det = [r for r in rows if r["pct"] >= 95.0]
        out["argmax_chain_share_mean"] = st.mean(shares)
        out["detections_with_chain_majority_argmax"] = sum(r["argmax_chain_share"] >= 0.5 for r in det)
        out["n_detections"] = len(det)
        out["all_seeds_chain_majority_argmax"] = sum(s >= 0.5 for s in shares)
    return out


if __name__ == "__main__":
    res = [summarize(nm) for nm in sys.argv[1:]]
    for r in res:
        print(json.dumps({k: v for k, v in r.items() if k != "pct_sorted"}, default=str))
    json.dump(res, open("summary_" + "_".join(sys.argv[1:]) + ".json", "w"), indent=1, default=str)
