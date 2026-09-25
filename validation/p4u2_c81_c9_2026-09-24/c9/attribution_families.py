"""DESCRIPTIVE ONLY (no percentile, no decision): bucket-family attribution under the C9 degree null.
Families: DEADEND (1,0,0,{F}); NONTRIVIAL (d2>0 or d3>0); OTHER. Reports observed vs null-mean of each family's max bucket."""
import sys, random, json, statistics as st
sys.argv=[sys.argv[0],"/home/user/MetaHIA-V10-Research"]
import c9_degree_null as c
def fam(pairs):
    g=c.stat(pairs)["groups"]
    dead=len(g.get(c.DEADEND,()))
    nt=max([len(v) for s,v in g.items() if s.depth2_count>0 or s.depth3_count>0] or [0])
    ntsig=max(((len(v),repr(s)) for s,v in g.items() if s.depth2_count>0 or s.depth3_count>0), default=(0,""))[1]
    return dead, nt, ntsig
out={}
for name in ["C9A0","C9SBM","C9B1"]:
    cfg=c.CONFIGS[name]; D=[];N=[];DN=[];NN=[];sigs={}
    for s in range(100):
        seed=cfg["base"]+s; pairs,_=c.observed(cfg,seed); d,nt,sg=fam(pairs); D.append(d); N.append(nt); sigs[sg]=sigs.get(sg,0)+1
        nulls=[fam(c.degree_null(random.Random(f"C9|{name}|{seed}|null|{j}"),pairs)[0]) for j in range(50)]
        DN.append(st.mean(x[0] for x in nulls)); NN.append(st.mean(x[1] for x in nulls))
    out[name]=dict(dead_obs=st.mean(D),dead_null=round(st.mean(DN),2),max_nontrivial_obs=st.mean(N),max_nontrivial_null=round(st.mean(NN),2),
                   top_nontrivial_sig=sorted(sigs.items(),key=lambda x:-x[1])[:2])
    print(name,json.dumps(out[name]))
json.dump(out,open("attribution_families.json","w"),indent=1)
