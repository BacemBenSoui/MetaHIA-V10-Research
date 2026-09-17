import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel2 import Node, PatternSlot, ShapeRewrite, ShapeTerm, PATTERN, SHAPE_PATTERN, pattern_ref
from e20d_protocol import CrossSlotCandidate, compare_discovered_transformations


def make_pattern(mapping=(1,0,2)):
    return Node("p", PATTERN, tuple(PatternSlot(source_position=i) for i in mapping))

def make_shape(mapping=(1,0,2)):
    n=len(mapping); op=ShapeTerm("VAR",0)
    src=ShapeTerm("APPLY",op,tuple(ShapeTerm("VAR",i+1) for i in range(n)))
    dst=ShapeTerm("APPLY",op,tuple(ShapeTerm("VAR",i+1) for i in mapping))
    return Node("s", SHAPE_PATTERN, (ShapeRewrite(src,dst,n),))

def cand(ref, pattern):
    return CrossSlotCandidate(0,1,pattern_ref(ref,pattern),"COMPARE_PERMUTATION",("R1","R2","R3"),("R1:pos0->pos1","R2:pos0->pos1","R3:pos0->pos1"))

def run():
    a=cand("P1",make_pattern())
    b=cand("S1",make_shape())
    c=cand("P2",make_pattern((0,2,1)))
    results={
      "pattern_vs_shape_same": compare_discovered_transformations(a,b) is True,
      "same_structure_distinct_ref": compare_discovered_transformations(a,cand("P2same",make_pattern())) is True,
      "different_map": compare_discovered_transformations(a,c) is False,
    }
    assert all(results.values()), results
    return results
if __name__=='__main__':
    r=run(); out={'suite':'E20-D cross representation integration v0.3','passed':sum(r.values()),'failed':len(r)-sum(r.values()),'results':r}
    Path(__file__).with_name('TEST_RESULTS_E20D_CROSS_REPR_V0_3.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
