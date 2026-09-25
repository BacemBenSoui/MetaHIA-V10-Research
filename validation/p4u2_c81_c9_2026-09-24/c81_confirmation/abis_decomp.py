"""Diagnostic only (not a criterion): A-bis with the truncation-artifact bucket (depth1_count==0) excluded from the max."""
import sys, json, random
from multiprocessing import Pool
sys.argv=[sys.argv[0],"/home/user/MetaHIA-V10-Research"]
import c81_confirmation as h, p4u2_autonomous_relation_discovery_v0_1 as p
def T_ex(pairs):
    sigs=h.signatures([h.mk_obs(i,a,b) for i,(a,b) in enumerate(pairs)])
    g=p.group_by_signature(sigs)
    vals=[len(v) for s,v in g.items() if s.depth1_count>0]
    return max(vals), sum(len(v) for s,v in g.items() if s.depth1_count==0)
def run(seed):
    cfg=h.CONFIGS["Abis"]; pairs,_,U,ne=h.observed_and_null_spec(cfg,seed)
    t,z=T_ex(pairs)
    nt=[T_ex(h.uniform_pairs(random.Random(f"Abis|{seed}|null|{j}"),U,ne))[0] for j in range(cfg["n_null"])]
    return dict(seed=seed,t_obs=t,zero_edges=z,pct=p.percentile_rank(t,nt)*100,null_t=nt)
if __name__=="__main__":
    cfg=h.CONFIGS["Abis"]
    with Pool(4) as pl: rows=pl.map(run,[cfg["base"]+s for s in range(cfg["seeds"])])
    json.dump(dict(config="Abis_excl_trunc",spec=cfg,elapsed_s=0,rows=[dict(r,k_obs=0,null_k_mean=0,argmax_chain_share=None) for r in rows]),open("raw_Abis_excl_trunc.json","w"))
    print("mean zero-sig edges per observed graph", sum(r["zero_edges"] for r in rows)/len(rows))
