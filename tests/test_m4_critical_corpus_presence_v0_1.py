import json
from pathlib import Path


def test_critical_corpus_is_present_and_unique():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "m4_critical_corpus_v0_1.json").read_text(encoding="utf-8"))
    ids = [case["id"] for case in data["cases"]]
    assert data["protocol"] == "M4-third-party-v0.1"
    assert ids == [f"C{i:02d}" for i in range(1, 11)]
    assert len(ids) == len(set(ids))
