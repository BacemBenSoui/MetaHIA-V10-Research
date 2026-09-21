import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from e20d_p4_autonomous_transfer_v0_1 import make_paths, discover_source_invariants, transfer_invariants_blind


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))['discovery_facts']

F=ROOT/'corpus/family_tree_facts_v0_2.json'
O=ROOT/'corpus/organization_facts_v0_1.json'

def test_source_discovery_does_not_use_target():
    fp=make_paths(load(F),2); op=make_paths(load(O),2)
    inv=discover_source_invariants(fp,min_support=2)
    assert inv
    assert all('ORGANIZATION' not in i.invariant_id for i in inv)
    assert all(i.support_count>=2 for i in inv)
    assert len(inv) >= 3

def test_blind_transfer_has_common_structural_shapes():
    fp=make_paths(load(F),2); op=make_paths(load(O),2)
    inv=discover_source_invariants(fp,min_support=2)
    transfers=transfer_invariants_blind(inv,op)
    assert transfers
    assert all(t.predicted_end is not None for t in transfers)

def test_operator_identity_is_not_part_of_discovered_invariant():
    fp=make_paths(load(F),2)
    inv=discover_source_invariants(fp,min_support=2)
    assert all('MERE_DE' not in i.invariant_id and 'MEMBRE_DE' not in i.invariant_id for i in inv)
