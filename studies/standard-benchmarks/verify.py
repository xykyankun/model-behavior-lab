"""Verify the committed protocol; optionally compare to pinned upstream bytes."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from behavior_lab.benchmarks import BASE_INSTRUCTIONS, FORMATS, POLICIES, load_cases, source_manifest
from behavior_lab.protocol import load_plan


def verify(cache=None):
    plan = load_plan(ROOT / "protocol.json")
    spec = plan["spec"]
    assert len(spec["cases"]) == 4 and len(plan["jobs"]) == 24
    assert spec["models"] == ["gpt-5.6-sol", "gpt-6-astra"]
    assert spec["repeats"] == 1
    assert {c["id"] for c in spec["conditions"]} == set(POLICIES)
    for condition in spec["conditions"]:
        assert condition["base_instructions"] == BASE_INSTRUCTIONS
        assert condition["user_suffix"] == "\n\nMethod instruction: " + POLICIES[condition["id"]]
    sources = source_manifest()
    assert sum(s.get("count", 0) for s in sources) == 2069
    for source in sources:
        assert re.fullmatch(r"[a-f0-9]{40}", source["commit"])
        assert re.fullmatch(r"[a-f0-9]{64}", source["sha256"])
        if source.get("kind") == "license":
            path = ROOT.parents[1] / "third_party" / source["file"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    if cache:
        expected = load_cases(cache, 1, spec["seed"])
        for case in expected:
            case["prompt"] += "\n\nReturn the final answer on the last line as FINAL: <answer>. " + FORMATS[case["answer_kind"]]
        assert expected == spec["cases"], "Selected examples differ from pinned upstream sources"
    # Public study files must contain no machine-local paths or personal history.
    for path in ROOT.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"/(?:Users|home)/[A-Za-z0-9]", text), path.name
        assert not re.search(r"[\u4e00-\u9fff]", text), path.name
    return {"scheduled_attempts": len(plan["jobs"]), "unique_questions": len(spec["cases"]),
            "source_examples": 2069, "protocol_sha256": plan["sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache")
    args = parser.parse_args()
    print(json.dumps(verify(args.cache), indent=2))
