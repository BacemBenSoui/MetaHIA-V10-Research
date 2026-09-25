"""C9-1 analysis (PREREGISTRATION_C9_1.md)."""
import json
import math
import statistics as st
import sys
from collections import Counter

sys.path.insert(0, "../c81conf")
from analyze import summarize  # noqa: E402  (reads raw_<name>.json in cwd)
from scipy import stats  # noqa: E402


def cochran_armitage_increasing(counts, ns, scores):
    N = sum(ns); R = sum(counts); pbar = R / N
    T = sum(s * (r - n * pbar) for r, n, s in zip(counts, ns, scores))
    var = pbar * (1 - pbar) * (sum(n * s * s for n, s in zip(ns, scores)) - sum(n * s for n, s in zip(ns, scores)) ** 2 / N)
    z = T / math.sqrt(var) if var > 0 else 0.0
    return z, 1 - stats.norm.cdf(z)


def extra(name, paired_old=None):
    rows = json.load(open(f"raw_{name}.json"))["rows"]
    out = dict(
        obs_truncated=sum(r["obs_truncated"] for r in rows),
        null_truncated_replicates=sum(r["null_truncated"] for r in rows),
        mean_tries=st.mean(r["mean_tries"] for r in rows),
        dead_obs_mean=st.mean(r["dead_obs"] for r in rows),
        dead_null_mean=st.mean(r["dead_null_mean"] for r in rows),
        dead_null_span_mean=st.mean(r["dead_null_max"] - r["dead_null_min"] for r in rows),
        head_obs_mean=st.mean(r["head_obs"] for r in rows),
        head_null_mean=st.mean(r["head_null_mean"] for r in rows),
        argmax_top=Counter(a for r in rows for a in r["argmax"]).most_common(3),
    )
    if paired_old:
        old = {r["seed"]: r["pct"] >= 95 for r in json.load(open(paired_old))["rows"]}
        new = {r["seed"]: r["pct"] >= 95 for r in rows}
        both = sum(old[s] and new[s] for s in new); only_old = sum(old[s] and not new[s] for s in new)
        only_new = sum(new[s] and not old[s] for s in new); neither = sum(not old[s] and not new[s] for s in new)
        b, c = only_old, only_new
        out["paired_uniform_vs_degree"] = dict(both=both, only_uniform=b, only_degree=c, neither=neither,
                                               mcnemar_exact_p=stats.binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0)
    return out


if __name__ == "__main__":
    res = {}
    for name, old in [("C9A0", None), ("C9A1", None), ("C9A2", None), ("C9SBM", None),
                      ("C9Abis", "../c81conf/raw_Abis.json"),
                      ("C9B1", "../c81conf/raw_B1.json"), ("C9B2", "../c81conf/raw_B2.json"), ("C9B3", "../c81conf/raw_B3.json")]:
        try:
            s = summarize(name)
        except FileNotFoundError:
            continue
        s.update(extra(name, old))
        res[name] = s
        w = s["wilson95"]
        print(f"{name:7} rej={s['rejections']:3}/100 W=[{w[0]:.3f},{w[1]:.3f}] a_eff={s['alpha_eff']:.4f} "
              f"p2={s['binom_two_sided_p']:.3g} pG={s['binom_greater_p']:.3g} KS={s['pit_ks_p']:.3g} chi2={s['pit_chi2_p']:.3g} "
              f"pctMed={s['pct_median']:.1f} tie={s['mean_tie_mass']:.3f} Tobs={s['t_obs']['median']} Tnull={s['t_null']['median']}")
        print("        ", {k: v for k, v in s.items() if k in ("obs_truncated", "null_truncated_replicates", "mean_tries", "dead_obs_mean",
                                                                "dead_null_mean", "dead_null_span_mean", "head_obs_mean", "head_null_mean",
                                                                "paired_uniform_vs_degree", "argmax_top", "pit_decile_counts")})
    if all(k in res for k in ("C9A0", "C9A1", "C9A2")):
        z, p = cochran_armitage_increasing([res[k]["rejections"] for k in ("C9A0", "C9A1", "C9A2")], [100] * 3, [0, 0.5, 0.75])
        res["N3_cochran_armitage"] = dict(z=z, p_increasing=p)
        print("N3 Cochran-Armitage z=%.3f p(increasing)=%.3f" % (z, p))
    json.dump(res, open("summary_c9.json", "w"), indent=1, default=str)
