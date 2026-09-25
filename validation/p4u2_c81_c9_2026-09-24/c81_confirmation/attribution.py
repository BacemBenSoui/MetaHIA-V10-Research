"""Which signature carries T=max|G_s| on observed signal corpora (B configs) and null configs."""
import sys, json, random
from collections import Counter
sys.argv=[sys.argv[0], "/home/user/MetaHIA-V10-Research"]
import c81_confirmation as h
import p4u2_autonomous_relation_discovery_v0_1 as p4u2
def label(sig):
    return f"({sig.depth1_count},{sig.depth2_count},{sig.depth3_count},{sorted(sig.directions)})"
res={}
for name in ["B2","B1","B3","A1","A2","A3","Abis"]:
    cfg=h.CONFIGS[name]; c=Counter(); chain_first=Counter(); comp=[]
    for s in range(cfg["seeds"]):
        pairs, chain_idx, universe, ne = h.observed_and_null_spec(cfg, cfg["base"]+s)
        sigs=h.signatures([h.mk_obs(i,a,b) for i,(a,b) in enumerate(pairs)])
        g=p4u2.group_by_signature(sigs); t=max(map(len,g.values()))
        for sg,idx in g.items():
            if len(idx)==t: c[label(sg)]+=1
        if chain_idx:
            firsts={i for i,(a,b) in enumerate(pairs) if a.startswith("cA")}
            seconds={i for i,(a,b) in enumerate(pairs) if a.startswith("cB")}
            best=max((idx for idx in g.values() if len(idx)==t), key=lambda idx: len(set(idx)&(firsts|seconds)))
            comp.append((t, len(set(best)&firsts), len(set(best)&seconds), t-len(set(best)&(firsts|seconds))))
    res[name]=dict(argmax_signatures=c.most_common(4))
    if comp:
        res[name]["mean_first_second_background_in_argmax"]=[round(sum(x[i] for x in comp)/len(comp),2) for i in range(4)]
    print(name, json.dumps(res[name]))
json.dump(res,open("attribution.json","w"),indent=1)
