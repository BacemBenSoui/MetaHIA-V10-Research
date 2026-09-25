"""C9-2 analysis (PREREGISTRATION_C9_2.md): T' criteria, paired T vs T', attribution."""
import json
import random
import statistics as st
import sys
from collections import Counter

sys.path.insert(0, "../c81conf")
from analyze import wilson, alpha_eff  # noqa: E402
from analyze_c9 import cochran_armitage_increasing  # noqa: E402
from scipy import stats  # noqa: E402


def block(rows, obs_key, null_key, pct_key):
    rr = [dict(t_obs=r[obs_key], null_t=r[null_key], pct=r[pct_key]) for r in rows]
    n = len(rr); k = sum(r["pct"] >= 95.0 for r in rr)
    a = alpha_eff(rr)
    rng = random.Random(12345); us = []
    for r in rr:
        b = sum(v < r["t_obs"] for v in r["null_t"]); t = sum(v == r["t_obs"] for v in r["null_t"])
        us.append((b + rng.random() * (t + 1)) / (len(r["null_t"]) + 1))
    dec = [0] * 10
    for u in us:
        dec[min(9, int(u * 10))] += 1
    return dict(rej=k, n=n, rate=k / n, wilson=wilson(k, n), alpha_eff=a,
                p_two=stats.binomtest(k, n, a).pvalue, p_greater=stats.binomtest(k, n, a, alternative="greater").pvalue,
                ks=stats.kstest(us, "uniform").pvalue, chi2=stats.chisquare(dec).pvalue, deciles=dec,
                obs_median=st.median(r["t_obs"] for r in rr), null_median=st.median(v for r in rr for v in r["null_t"]),
                tie=st.mean(sum(v == r["t_obs"] for v in r["null_t"]) / len(r["null_t"]) for r in rr),
                pct_median=st.median(r["pct"] for r in rr))


def summarize(name):
    rows = json.load(open(f"raw_{name}.json"))["rows"]
    T = block(rows, "t_obs", "null_t", "pct_t"); TP = block(rows, "tp_obs", "null_tp", "pct_tp")
    a = [r["pct_t"] >= 95 for r in rows]; b = [r["pct_tp"] >= 95 for r in rows]
    only_t = sum(x and not y for x, y in zip(a, b)); only_tp = sum(y and not x for x, y in zip(a, b))
    out = dict(config=name, T=T, Tp=TP,
               paired=dict(both=sum(x and y for x, y in zip(a, b)), only_T=only_t, only_Tp=only_tp,
                           neither=sum(not x and not y for x, y in zip(a, b)),
                           mcnemar_p=stats.binomtest(min(only_t, only_tp), only_t + only_tp, 0.5).pvalue if only_t + only_tp else 1.0),
               truncated_obs=sum(r["obs_truncated"] for r in rows), truncated_null=sum(r["null_truncated"] for r in rows),
               argmax_T_family=Counter(f for r in rows for f in r["argmax_t_family"]).most_common(),
               argmax_Tp_top=Counter(s for r in rows for s in r["argmax_tp"]).most_common(3),
               argmax_Tp_bucket_obs_mean=st.mean(r["argmax_tp_bucket_obs"] for r in rows),
               argmax_Tp_bucket_null_mean=st.mean(r["argmax_tp_bucket_null_mean"] for r in rows))
    shares = [r.get("argmax_tp_chain_share") for r in rows if r.get("argmax_tp_chain_share") is not None]
    if shares:
        out["argmax_Tp_chain_share_mean"] = st.mean(shares)
    return out


if __name__ == "__main__":
    names = [n for n in ["C92A0", "C92A1", "C92A2", "C92SBM", "C92Abis", "C92B2", "C92B1", "C92B3"]]
    res = {}
    for n in names:
        try:
            res[n] = summarize(n)
        except FileNotFoundError:
            continue
        s = res[n]
        for lab in ("T", "Tp"):
            b = s[lab]
            print(f"{n:8} {lab:2} rej={b['rej']:3}/100 W=[{b['wilson'][0]:.3f},{b['wilson'][1]:.3f}] a_eff={b['alpha_eff']:.4f} "
                  f"p2={b['p_two']:.3g} pG={b['p_greater']:.3g} KS={b['ks']:.3g} chi2={b['chi2']:.3g} obsMed={b['obs_median']} nullMed={b['null_median']} tie={b['tie']:.2f}")
        print("          paired", s["paired"], "trunc", s["truncated_obs"], s["truncated_null"], "famT", s["argmax_T_family"],
              "TpBucket obs/null %.2f/%.2f" % (s["argmax_Tp_bucket_obs_mean"], s["argmax_Tp_bucket_null_mean"]),
              "chainShare", s.get("argmax_Tp_chain_share_mean"))
        print("          TpTop", s["argmax_Tp_top"][:2])
    bs = [n for n in ("C92B2", "C92B1", "C92B3") if n in res]
    if len(bs) == 3:
        z, p = cochran_armitage_increasing([res[n]["Tp"]["rej"] for n in bs], [100] * 3, [8, 15, 25])
        res["trend_Tp"] = dict(z=z, p=p); print("trend Tp over chains z=%.2f p=%.3g" % (z, p))
    json.dump(res, open("summary_c92.json", "w"), indent=1, default=str)
